# Backend - Video to 3D API

Backend en Python para procesamiento de videos y reconstrucción 3D con COLMAP API (gratuito y open source).

## Características

- ✅ Carga de videos (MP4, AVI, MOV, MKV)
- ✅ Extracción automática de fotogramas clave
- ✅ Análisis de calidad de video
- ✅ **Reconstrucción 3D con COLMAP API (100% gratis)**
- ✅ Procesamiento y reparación de mallas 3D
- ✅ Validación para impresión 3D
- ✅ Exportación a STL/3MF/OBJ

## Instalación

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno (Windows)
venv\Scripts\activate

# Activar entorno (Linux/Mac)
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

## Configuración

```bash
# Copiar archivo de configuración
cp .env.example .env

# Editar configuración según necesites
notepad .env
```

## Ejecución

```bash
# Desarrollo
python main.py

# Producción
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### POST /api/v1/upload
Sube un video para procesamiento.

**Parámetros:**
- `file`: Archivo de video (multipart/form-data)
- `frame_interval`: Intervalo de extracción de frames (default: 30)

**Respuesta:**
```json
{
  "job_id": "uuid",
  "message": "Video subido exitosamente",
  "status_endpoint": "/api/v1/status/{job_id}"
}
```

### GET /api/v1/status/{job_id}
Obtiene el estado del procesamiento.

**Respuesta:**
```json
{
  "status": "processing",
  "stage": "extracting_frames",
  "progress": 45,
  "message": "Extrayendo fotogramas: 45%"
}
```

### GET /api/v1/frames/{job_id}
Obtiene información sobre los fotogramas extraídos.

### POST /api/v1/reconstruct/{job_id}
Inicia la reconstrucción 3D.

**Parámetros:**
- `method`: "api_external" o "local_photogrammetry"

### GET /api/v1/download/{job_id}
Descarga el modelo 3D generado.

**Parámetros:**
- `format`: "stl", "3mf", u "obj"

### DELETE /api/v1/cleanup/{job_id}
Limpia los archivos temporales.

## Uso del MeshProcessor

```python
from mesh_processor import MeshProcessor

# Procesar malla para impresión
processor = MeshProcessor("input.stl")
processor.load_mesh()

# Analizar malla
analysis = processor.analyze_mesh()
print(analysis)

# Reparar malla
processor.fix_non_manifold()
processor.make_watertight()

# Exportar
processor.export_mesh("output.stl", "stl")
```

## Arquitectura

```
backend/
├── main.py              # API FastAPI principal
├── mesh_processor.py    # Procesamiento de mallas 3D
├── requirements.txt     # Dependencias Python
├── .env.example        # Configuración de ejemplo
└── README.md           # Este archivo
```

## Integración con APIs de IA 3D

El backend está preparado para integrarse con servicios como:
- **Meshy.ai**: Generación de modelos 3D desde imágenes
- **Tripo3D**: Reconstrucción 3D rápida
- **Luma AI**: Renderizado y reconstrucción 3D

Para integrar, añade tus API keys en `.env` y modifica el método `reconstruct_3d` en `main.py`.

## Desarrollo

```bash
# Ejecutar con auto-reload
uvicorn main:app --reload

# Ver documentación interactiva
# Abrir http://localhost:8000/docs en navegador
```

## Próximos pasos

1. Integrar con API de IA 3D real
2. Implementar fotogrametría local (COLMAP + OpenMVS)
3. Añadir cola de procesamiento (Celery + Redis)
4. Implementar autenticación
5. Añadir sistema de caché para modelos procesados
