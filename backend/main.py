from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import cv2
import os
import shutil
from pathlib import Path
import uuid
from datetime import datetime
from contextlib import asynccontextmanager
import aiofiles
import logging
from dotenv import load_dotenv
from PIL import Image
from colmap_integration import COLMAPIntegration

load_dotenv(Path(__file__).resolve().parent / ".env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_app):
    logger.info("Servidor Video to 3D API iniciado")
    logger.info("Directorio de uploads: %s", UPLOAD_DIR.absolute())
    logger.info("Directorio de frames: %s", FRAMES_DIR.absolute())
    logger.info("Directorio de output: %s", OUTPUT_DIR.absolute())
    yield


app = FastAPI(title="Video to 3D API", version="1.0.0", lifespan=lifespan)

# Configurar CORS
allowed_origins = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directorios de trabajo, relativos al backend por defecto.
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", BASE_DIR / "uploads"))
FRAMES_DIR = Path(os.getenv("FRAMES_DIR", BASE_DIR / "frames"))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", BASE_DIR / "output"))
TEMP_DIR = Path(os.getenv("TEMP_DIR", BASE_DIR / "temp"))
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", 500 * 1024 * 1024))
MAX_TOTAL_UPLOAD_BYTES = int(os.getenv("MAX_TOTAL_UPLOAD_BYTES", 1024 * 1024 * 1024))
MAX_IMAGE_COUNT = int(os.getenv("MAX_IMAGE_COUNT", 100))

# Crear directorios si no existen
for directory in [UPLOAD_DIR, FRAMES_DIR, OUTPUT_DIR, TEMP_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Almacenamiento en memoria del estado de procesamiento
processing_status = {}


class VideoProcessor:
    def __init__(self, video_path: str, job_id: str):
        self.video_path = video_path
        self.job_id = job_id
        self.output_frames_dir = FRAMES_DIR / job_id
        
    def extract_key_frames(self, frame_interval: int = 30) -> dict:
        """
        Extrae fotogramas clave del video a intervalos regulares.
        frame_interval: Extraer 1 frame cada N frames (30 = 1 frame por segundo aprox en video 30fps)
        """
        processing_status[self.job_id] = {
            "status": "processing",
            "stage": "extracting_frames",
            "progress": 0,
            "message": "Extrayendo fotogramas del video..."
        }
        
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise ValueError("No se pudo abrir el video. Comprueba que el archivo no esté dañado.")
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = total_frames / fps if fps > 0 else 0
        
        self.output_frames_dir.mkdir(exist_ok=True)
        extracted_frames = []
        
        frame_count = 0
        saved_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % frame_interval == 0:
                # Guardar frame
                frame_path = self.output_frames_dir / f"frame_{saved_count:04d}.jpg"
                if not cv2.imwrite(str(frame_path), frame):
                    cap.release()
                    raise ValueError("No se pudo guardar un fotograma del video")
                extracted_frames.append(str(frame_path))
                saved_count += 1
                
                # Actualizar progreso
                progress = int((frame_count / total_frames) * 100)
                processing_status[self.job_id]["progress"] = progress
                processing_status[self.job_id]["message"] = f"Extrayendo fotogramas: {progress}%"
            
            frame_count += 1
        
        cap.release()
        if saved_count == 0:
            raise ValueError("No se pudieron extraer fotogramas del video")
        
        processing_status[self.job_id]["stage"] = "frames_extracted"
        processing_status[self.job_id]["message"] = f"Se extrajeron {saved_count} fotogramas"
        
        return {
            "total_frames": total_frames,
            "extracted_frames": saved_count,
            "fps": fps,
            "duration": duration,
            "frame_paths": extracted_frames
        }
    
    def analyze_video_quality(self) -> dict:
        """
        Analiza la calidad del video para determinar parámetros de reconstrucción.
        """
        processing_status[self.job_id]["stage"] = "analyzing_quality"
        processing_status[self.job_id]["message"] = "Analizando calidad del video..."
        
        cap = cv2.VideoCapture(self.video_path)
        
        # Obtener propiedades del video
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        cap.release()
        
        # Análisis de calidad
        quality_score = min(100, (width * height) / 10000)  # Puntuación basada en resolución
        recommended_interval = max(10, min(60, int(30 / fps * 30))) if fps > 0 else 30
        
        return {
            "resolution": f"{width}x{height}",
            "fps": fps,
            "total_frames": total_frames,
            "duration": total_frames / fps if fps > 0 else 0,
            "quality_score": quality_score,
            "recommended_frame_interval": recommended_interval,
            "is_high_quality": quality_score > 50
        }


@app.get("/")
async def root():
    return {
        "message": "Video to 3D API",
        "version": "1.0.0",
        "endpoints": {
            "upload_video": "/api/v1/upload",
            "check_status": "/api/v1/status/{job_id}",
            "get_frames": "/api/v1/frames/{job_id}",
            "download_model": "/api/v1/download/{job_id}"
        }
    }


@app.post("/api/v1/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    frame_interval: int = Form(default=30, ge=1, le=300)
):
    """
    Sube un video y comienza el procesamiento para extracción de fotogramas.
    """
    # Validar tipo de archivo
    allowed_extensions = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".m4v"}
    file_extension = Path(file.filename or "").suffix.lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="El archivo debe ser un video")
    
    # Generar ID único para el job
    job_id = str(uuid.uuid4())
    
    # Guardar archivo subido
    video_path = UPLOAD_DIR / f"{job_id}{file_extension}"
    total_bytes = 0
    try:
        async with aiofiles.open(video_path, 'wb') as f:
            while chunk := await file.read(1024 * 1024):
                total_bytes += len(chunk)
                if total_bytes > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail="El video supera el límite de tamaño configurado")
                await f.write(chunk)
    except Exception:
        video_path.unlink(missing_ok=True)
        raise
    finally:
        await file.close()
    if total_bytes == 0:
        video_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="El archivo está vacío")
    
    # Inicializar estado del job
    processing_status[job_id] = {
        "status": "queued",
        "stage": "uploaded",
        "progress": 0,
        "message": "Video subido exitosamente",
        "created_at": datetime.now().isoformat(),
        "video_path": str(video_path),
        "original_filename": file.filename or video_path.name
    }
    
    # Procesar en background
    processor = VideoProcessor(str(video_path), job_id)
    
    def process_video():
        try:
            # Analizar calidad del video
            quality_analysis = processor.analyze_video_quality()
            processing_status[job_id]["quality_analysis"] = quality_analysis
            
            # Extraer fotogramas
            frame_extraction = processor.extract_key_frames(frame_interval)
            processing_status[job_id]["frame_extraction"] = frame_extraction
            
            # Marcar como completado
            processing_status[job_id]["status"] = "completed"
            processing_status[job_id]["stage"] = "ready_for_reconstruction"
            processing_status[job_id]["message"] = "Fotogramas extraídos exitosamente. Listo para reconstrucción 3D."
            processing_status[job_id]["progress"] = 100
            
        except Exception as e:
            processing_status[job_id]["status"] = "failed"
            processing_status[job_id]["stage"] = "error"
            processing_status[job_id]["message"] = f"Error en el procesamiento: {str(e)}"
            processing_status[job_id]["error"] = str(e)
    
    background_tasks.add_task(process_video)
    
    return {
        "job_id": job_id,
        "message": "Video subido exitosamente. Procesamiento iniciado.",
        "status_endpoint": f"/api/v1/status/{job_id}"
    }


@app.post("/api/v1/upload-images")
async def upload_images(
    images: list[UploadFile] = File(...)
):
    """
    Sube múltiples imágenes y las prepara para reconstrucción 3D.
    """
    if len(images) < 2:
        raise HTTPException(status_code=400, detail="Sube al menos 2 imágenes para reconstruir el objeto")
    if len(images) > MAX_IMAGE_COUNT:
        raise HTTPException(status_code=413, detail=f"El máximo permitido es {MAX_IMAGE_COUNT} imágenes por reconstrucción")
    
    # Validar que sean imágenes
    for image in images:
        if Path(image.filename or "").suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            raise HTTPException(status_code=400, detail=f"Formato de imagen no admitido: {image.filename}")
    
    # Generar ID único para el job
    job_id = str(uuid.uuid4())
    
    # Crear directorio para las imágenes
    images_dir = FRAMES_DIR / job_id
    images_dir.mkdir(exist_ok=True)
    
    # Guardar imágenes subidas
    image_paths = []
    total_upload_bytes = 0
    for idx, image in enumerate(images):
        file_extension = Path(image.filename or "image.jpg").suffix.lower()
        image_path = images_dir / f"image_{idx:04d}{file_extension}"
        
        total_bytes = 0
        try:
            async with aiofiles.open(image_path, 'wb') as f:
                while chunk := await image.read(1024 * 1024):
                    total_bytes += len(chunk)
                    total_upload_bytes += len(chunk)
                    if total_bytes > MAX_UPLOAD_BYTES or total_upload_bytes > MAX_TOTAL_UPLOAD_BYTES:
                        raise HTTPException(status_code=413, detail="La carga de imágenes supera el límite de tamaño configurado")
                    await f.write(chunk)
            if total_bytes == 0:
                raise HTTPException(status_code=400, detail=f"La imagen {image.filename} está vacía")
            with Image.open(image_path) as decoded_image:
                decoded_image.verify()
        except Exception:
            image_path.unlink(missing_ok=True)
            shutil.rmtree(images_dir, ignore_errors=True)
            raise
        finally:
            await image.close()
        
        image_paths.append(str(image_path))
    
    # Inicializar estado del job
    processing_status[job_id] = {
        "status": "queued",
        "stage": "images_uploaded",
        "progress": 0,
        "message": f"{len(images)} imágenes subidas exitosamente",
        "created_at": datetime.now().isoformat(),
        "images_dir": str(images_dir),
        "image_paths": image_paths,
        "total_images": len(images)
    }
    
    # Marcar como listo para reconstrucción inmediatamente
    processing_status[job_id]["status"] = "completed"
    processing_status[job_id]["stage"] = "ready_for_reconstruction"
    processing_status[job_id]["message"] = f"Imágenes listas para reconstrucción 3D ({len(images)} imágenes)"
    processing_status[job_id]["progress"] = 100
    
    return {
        "job_id": job_id,
        "message": f"{len(images)} imágenes subidas exitosamente. Listas para reconstrucción 3D.",
        "total_images": len(images),
        "status_endpoint": f"/api/v1/status/{job_id}"
    }


@app.get("/api/v1/status/{job_id}")
async def get_status(job_id: str):
    """
    Obtiene el estado del procesamiento de un job.
    """
    if job_id not in processing_status:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    
    return processing_status[job_id]


@app.get("/api/v1/frames/{job_id}")
async def get_frames_info(job_id: str):
    """
    Obtiene información sobre los fotogramas extraídos.
    """
    if job_id not in processing_status:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    
    frames_dir = FRAMES_DIR / job_id
    if not frames_dir.exists():
        raise HTTPException(status_code=404, detail="Fotogramas no encontrados")
    
    frame_files = list(frames_dir.glob("*.jpg"))
    
    return {
        "job_id": job_id,
        "total_frames": len(frame_files),
        "frames": [f.name for f in sorted(frame_files)]
    }


@app.post("/api/v1/reconstruct/{job_id}")
async def reconstruct_3d(
    job_id: str,
    background_tasks: BackgroundTasks,
    method: str = Query(default="colmap", pattern="^colmap$")
):
    """
    Inicia la reconstrucción 3D usando el método especificado.
    """
    if job_id not in processing_status:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    
    job_status = processing_status[job_id]
    can_retry_reconstruction = (
        job_status.get("status") == "failed"
        and job_status.get("stage") == "reconstruction_error"
    )
    if job_status.get("status") != "completed" and not can_retry_reconstruction:
        raise HTTPException(status_code=400, detail="Los fotogramas deben estar extraídos primero")
    
    processing_status[job_id]["status"] = "processing"
    processing_status[job_id]["stage"] = "reconstructing_3d"
    processing_status[job_id]["message"] = "Iniciando reconstrucción 3D..."
    processing_status[job_id]["reconstruction_method"] = method
    processing_status[job_id].pop("error", None)
    (OUTPUT_DIR / f"{job_id}.stl").unlink(missing_ok=True)
    
    def perform_reconstruction():
        try:
            if method == "colmap":
                # Usar COLMAP API para fotogrametría gratuita
                processing_status[job_id]["message"] = "Iniciando reconstrucción con COLMAP..."
                processing_status[job_id]["progress"] = 10
                
                # Obtener directorio de frames/imágenes
                frames_dir = FRAMES_DIR / job_id
                if not frames_dir.exists():
                    raise Exception("Directorio de imágenes no encontrado")
                
                # Obtener lista de imágenes (soportar múltiples formatos)
                image_extensions = ["*.jpg", "*.jpeg", "*.png", "*.webp"]
                frame_files = sorted({
                    path for extension in image_extensions for path in frames_dir.glob(extension)
                })
                
                if not frame_files:
                    raise Exception("No se encontraron imágenes para procesar. Asegúrate de subir imágenes válidas.")
                
                processing_status[job_id]["message"] = f"Procesando {len(frame_files)} imágenes con COLMAP..."
                processing_status[job_id]["progress"] = 20
                
                # Inicializar COLMAP Integration
                colmap_api_url = os.getenv("COLMAP_API_URL", "http://localhost:8001")
                print(f"Conectando a COLMAP API en: {colmap_api_url}")
                colmap = COLMAPIntegration(colmap_api_url)
                
                processing_status[job_id]["message"] = "Enviando frames a COLMAP API..."
                processing_status[job_id]["progress"] = 30
                
                # Crear directorio de salida para COLMAP
                colmap_output_dir = OUTPUT_DIR / job_id / "colmap"
                
                # Realizar reconstrucción
                result = colmap.reconstruct_from_images(
                    image_paths=[str(f) for f in frame_files],
                    output_dir=str(colmap_output_dir)
                )
                
                processing_status[job_id]["message"] = "Reconstrucción COLMAP completada. Procesando resultados..."
                processing_status[job_id]["progress"] = 70
                
                if result["success"]:
                    # Si hay archivo STL generado, copiarlo al directorio principal
                    if result.get("stl_file"):
                        stl_source = Path(result["stl_file"])
                        stl_dest = OUTPUT_DIR / f"{job_id}.stl"
                        shutil.copy(stl_source, stl_dest)
                        processing_status[job_id]["stl_file"] = str(stl_dest)
                    else:
                        # Probar todos los formatos de malla recibidos; un PLY de
                        # nube de puntos puede fallar aunque el ZIP incluya un OBJ válido.
                        mesh_files = result.get("mesh_files", {})
                        stl_dest = OUTPUT_DIR / f"{job_id}.stl"
                        mesh_candidates = [mesh_files.get("ply"), mesh_files.get("obj")]
                        converted = any(
                            colmap.convert_to_stl(mesh_path, str(stl_dest))
                            for mesh_path in mesh_candidates if mesh_path
                        )
                        if converted:
                            processing_status[job_id]["stl_file"] = str(stl_dest)
                        elif not mesh_candidates or not any(mesh_candidates):
                            # Si no hay malla pero hay point cloud, informar al usuario
                            if mesh_files.get("point_cloud") or mesh_files.get("ply"):
                                raise Exception("COLMAP generó solo una nube de puntos, no una malla 3D completa. Intenta con más imágenes o mejores ángulos.")
                            else:
                                raise Exception("No se encontró malla válida en la reconstrucción. COLMAP pudo no generar suficientes puntos 3D. Intenta con más imágenes (mínimo 12-20) desde diferentes ángulos con mayor superposición.")
                        else:
                            raise Exception("No se pudo convertir ninguna malla COLMAP a STL. Verifica que el ZIP incluya una malla válida.")
                    
                    processing_status[job_id]["colmap_result"] = result
                    processing_status[job_id]["message"] = "Reconstrucción 3D completada con COLMAP"
                    processing_status[job_id]["progress"] = 100
                else:
                    raise Exception("La reconstrucción COLMAP falló")
                
            if not (OUTPUT_DIR / f"{job_id}.stl").is_file() or (OUTPUT_DIR / f"{job_id}.stl").stat().st_size == 0:
                raise ValueError("COLMAP no produjo un archivo STL válido")
            
            processing_status[job_id]["status"] = "completed"
            processing_status[job_id]["stage"] = "reconstruction_completed"
            processing_status[job_id]["message"] = "Reconstrucción 3D completada"
            processing_status[job_id]["progress"] = 100
            processing_status[job_id]["output_file"] = f"{job_id}.stl"
            
        except Exception as e:
            processing_status[job_id]["status"] = "failed"
            processing_status[job_id]["stage"] = "reconstruction_error"
            processing_status[job_id]["message"] = f"Error en reconstrucción: {str(e)}"
            processing_status[job_id]["error"] = str(e)
    
    background_tasks.add_task(perform_reconstruction)
    
    return {
        "job_id": job_id,
        "message": "Reconstrucción 3D iniciada",
        "method": method,
        "status_endpoint": f"/api/v1/status/{job_id}"
    }


@app.get("/api/v1/download/{job_id}")
async def download_model(job_id: str, format: str = "stl"):
    """
    Descarga el modelo 3D generado.
    """
    if job_id not in processing_status:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    
    if processing_status[job_id].get("stage") != "reconstruction_completed":
        raise HTTPException(status_code=400, detail="El modelo 3D no está listo aún")
    
    file_extension = format.lower()
    if file_extension != "stl":
        raise HTTPException(status_code=400, detail="Por ahora solo está disponible la descarga en formato STL")
    output_path = OUTPUT_DIR / f"{job_id}.{file_extension}"
    
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    return FileResponse(
        path=output_path,
        filename=f"model_3d_{job_id}.{file_extension}",
        media_type="application/octet-stream"
    )


@app.delete("/api/v1/cleanup/{job_id}")
async def cleanup_job(job_id: str):
    """
    Limpia los archivos temporales de un job.
    """
    if job_id not in processing_status:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    if processing_status[job_id].get("status") in {"queued", "processing"}:
        raise HTTPException(status_code=409, detail="No se puede limpiar un trabajo que sigue procesándose")
    
    # Eliminar archivos temporales
    try:
        video_path_value = processing_status[job_id].get("video_path")
        if video_path_value and Path(video_path_value).exists():
            video_path = Path(video_path_value)
            video_path.unlink()
        
        frames_dir = FRAMES_DIR / job_id
        if frames_dir.exists():
            shutil.rmtree(frames_dir)
        
        job_output_dir = OUTPUT_DIR / job_id
        if job_output_dir.exists():
            shutil.rmtree(job_output_dir)
        for suffix in ("stl", "obj", "3mf"):
            output_file = OUTPUT_DIR / f"{job_id}.{suffix}"
            output_file.unlink(missing_ok=True)
        
        # Eliminar del estado
        del processing_status[job_id]
        
        return {"message": "Job limpiado exitosamente"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en limpieza: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=os.getenv("DEBUG", "false").lower() == "true",
    )
