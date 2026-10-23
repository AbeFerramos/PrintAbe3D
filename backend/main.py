from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import cv2
import numpy as np
import os
import shutil
from pathlib import Path
from typing import Optional
import uuid
from datetime import datetime
import aiofiles
import asyncio
import logging
from colmap_integration import COLMAPIntegration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Video to 3D API", version="1.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directorios de trabajo
UPLOAD_DIR = Path("uploads")
FRAMES_DIR = Path("frames")
OUTPUT_DIR = Path("output")
TEMP_DIR = Path("temp")

# Crear directorios si no existen
for directory in [UPLOAD_DIR, FRAMES_DIR, OUTPUT_DIR, TEMP_DIR]:
    directory.mkdir(exist_ok=True)

# Almacenamiento en memoria del estado de procesamiento
processing_status = {}


class VideoProcessor:
    def __init__(self, video_path: str, job_id: str):
        self.video_path = video_path
        self.job_id = job_id
        self.output_frames_dir = FRAMES_DIR / job_id
        
    def extract_key_frames(self, frame_interval: int = 30) -> list:
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
            raise HTTPException(status_code=400, detail="No se pudo abrir el video")
        
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
                cv2.imwrite(str(frame_path), frame)
                extracted_frames.append(str(frame_path))
                saved_count += 1
                
                # Actualizar progreso
                progress = int((frame_count / total_frames) * 100)
                processing_status[self.job_id]["progress"] = progress
                processing_status[self.job_id]["message"] = f"Extrayendo fotogramas: {progress}%"
            
            frame_count += 1
        
        cap.release()
        
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


@app.on_event("startup")
async def startup_event():
    """Inicializar el servidor"""
    print("🚀 Servidor Video to 3D API iniciado")
    print(f"📁 Directorio de uploads: {UPLOAD_DIR.absolute()}")
    print(f"📁 Directorio de frames: {FRAMES_DIR.absolute()}")
    print(f"📁 Directorio de output: {OUTPUT_DIR.absolute()}")


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
    frame_interval: Optional[int] = 30
):
    """
    Sube un video y comienza el procesamiento para extracción de fotogramas.
    """
    # Validar tipo de archivo
    if not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="El archivo debe ser un video")
    
    # Generar ID único para el job
    job_id = str(uuid.uuid4())
    
    # Guardar archivo subido
    file_extension = Path(file.filename).suffix
    video_path = UPLOAD_DIR / f"{job_id}{file_extension}"
    
    async with aiofiles.open(video_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Inicializar estado del job
    processing_status[job_id] = {
        "status": "queued",
        "stage": "uploaded",
        "progress": 0,
        "message": "Video subido exitosamente",
        "created_at": datetime.now().isoformat(),
        "video_path": str(video_path),
        "original_filename": file.filename
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
    background_tasks: BackgroundTasks,
    images: list[UploadFile] = File(...)
):
    """
    Sube múltiples imágenes y las prepara para reconstrucción 3D.
    """
    if not images:
        raise HTTPException(status_code=400, detail="Debe subir al menos una imagen")
    
    # Validar que sean imágenes
    for image in images:
        if not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail=f"El archivo {image.filename} no es una imagen")
    
    # Generar ID único para el job
    job_id = str(uuid.uuid4())
    
    # Crear directorio para las imágenes
    images_dir = FRAMES_DIR / job_id
    images_dir.mkdir(exist_ok=True)
    
    # Guardar imágenes subidas
    image_paths = []
    for idx, image in enumerate(images):
        file_extension = Path(image.filename).suffix
        image_path = images_dir / f"image_{idx:04d}{file_extension}"
        
        async with aiofiles.open(image_path, 'wb') as f:
            content = await image.read()
            await f.write(content)
        
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
    method: str = "colmap"  # "colmap", "api_external" o "local_photogrammetry"
):
    """
    Inicia la reconstrucción 3D usando el método especificado.
    """
    if job_id not in processing_status:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    
    if processing_status[job_id]["status"] != "completed":
        raise HTTPException(status_code=400, detail="Los fotogramas deben estar extraídos primero")
    
    processing_status[job_id]["status"] = "processing"
    processing_status[job_id]["stage"] = "reconstructing_3d"
    processing_status[job_id]["message"] = "Iniciando reconstrucción 3D..."
    processing_status[job_id]["reconstruction_method"] = method
    
    def perform_reconstruction():
        try:
            if method == "api_external":
                # Aquí se integraría con APIs como Meshy, Tripo3D, etc.
                # Por ahora, simulamos el proceso
                import time
                for i in range(0, 101, 10):
                    time.sleep(1)
                    processing_status[job_id]["progress"] = i
                    processing_status[job_id]["message"] = f"Reconstruyendo modelo 3D: {i}%"
                
                # Simular generación de archivo (en producción esto vendría de la API)
                output_path = OUTPUT_DIR / f"{job_id}.stl"
                # Crear archivo dummy
                with open(output_path, 'w') as f:
                    f.write("STL dummy file - en producción esto sería el modelo real")
                
            elif method == "colmap":
                # Usar COLMAP API para fotogrametría gratuita
                processing_status[job_id]["message"] = "Iniciando reconstrucción con COLMAP..."
                processing_status[job_id]["progress"] = 10
                
                # Obtener directorio de frames/imágenes
                frames_dir = FRAMES_DIR / job_id
                if not frames_dir.exists():
                    raise Exception("Directorio de imágenes no encontrado")
                
                # Obtener lista de imágenes (soportar múltiples formatos)
                image_extensions = ["*.jpg", "*.jpeg", "*.png", "*.webp", "*.JPG", "*.JPEG", "*.PNG", "*.WEBP"]
                frame_files = []
                for ext in image_extensions:
                    frame_files.extend(frames_dir.glob(ext))
                
                frame_files = sorted(frame_files)
                
                if not frame_files:
                    raise Exception("No se encontraron imágenes para procesar. Asegúrate de subir imágenes válidas.")
                
                processing_status[job_id]["message"] = f"Procesando {len(frame_files)} imágenes con COLMAP..."
                processing_status[job_id]["progress"] = 20
                
                # Inicializar COLMAP Integration
                colmap_api_url = os.getenv("COLMAP_API_URL", "http://localhost:8001")
                print(f"Conectando a COLMAP API en: {colmap_api_url}")
                colmap = COLMAPIntegration(colmap_api_url)
                
                # No verificar health check, asumimos que COLMAP API está disponible
                print("Saltando health check, asumiendo COLMAP API disponible...")
                
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
                        # Intentar convertir desde PLY si no hay STL
                        if result["mesh_files"].get("ply"):
                            ply_file = result["mesh_files"]["ply"]
                            stl_dest = OUTPUT_DIR / f"{job_id}.stl"
                            if colmap.convert_to_stl(ply_file, str(stl_dest)):
                                processing_status[job_id]["stl_file"] = str(stl_dest)
                            else:
                                # Si no hay malla pero hay point cloud, informar al usuario
                                if result["mesh_files"].get("point_cloud"):
                                    raise Exception("COLMAP generó solo una nube de puntos, no una malla 3D completa. Intenta con más imágenes o mejores ángulos.")
                                else:
                                    raise Exception("No se pudo convertir la malla a STL. COLMAP no generó una malla válida. Intenta con más imágenes (mínimo 12-20) desde diferentes ángulos.")
                        else:
                            # Si no hay malla pero hay point cloud, informar al usuario
                            if result["mesh_files"].get("point_cloud"):
                                raise Exception("COLMAP generó solo una nube de puntos, no una malla 3D completa. Intenta con más imágenes o mejores ángulos.")
                            else:
                                raise Exception("No se encontró malla válida en la reconstrucción. COLMAP pudo no generar suficientes puntos 3D. Intenta con más imágenes (mínimo 12-20) desde diferentes ángulos con mayor superposición.")
                    
                    processing_status[job_id]["colmap_result"] = result
                    processing_status[job_id]["message"] = "Reconstrucción 3D completada con COLMAP"
                    processing_status[job_id]["progress"] = 100
                else:
                    raise Exception("La reconstrucción COLMAP falló")
                
            elif method == "local_photogrammetry":
                # Aquí se implementaría fotogrametría local con COLMAP + OpenMVS
                processing_status[job_id]["message"] = "Fotogrametría local no implementada aún"
                raise NotImplementedError("Fotogrametría local requiere configuración adicional")
            
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
    
    # Eliminar archivos temporales
    try:
        video_path = Path(processing_status[job_id].get("video_path"))
        if video_path.exists():
            video_path.unlink()
        
        frames_dir = FRAMES_DIR / job_id
        if frames_dir.exists():
            shutil.rmtree(frames_dir)
        
        output_file = OUTPUT_DIR / f"{job_id}.stl"
        if output_file.exists():
            output_file.unlink()
        
        # Eliminar del estado
        del processing_status[job_id]
        
        return {"message": "Job limpiado exitosamente"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en limpieza: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
