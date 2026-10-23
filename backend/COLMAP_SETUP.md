# Guía de Instalación de COLMAP API

COLMAP API es una solución 100% gratuita y open source para fotogrametría de alta calidad. Esta guía te ayudará a configurarla para usarla con Print3D.

## 🎯 ¿Qué es COLMAP?

COLMAP es un pipeline de Structure-from-Motion y Multi-View Stereo general-purpose que ofrece:
- ✅ Reconstrucción 3D de alta calidad desde imágenes
- ✅ Totalmente gratis y open source (licencia BSD)
- ✅ Soporte para GPU para procesamiento más rápido
- ✅ API REST fácil de integrar
- ✅ Calidad profesional para impresión 3D

## 📋 Requisitos Previos

### Opción A: Docker (Recomendada - Más Fácil)
- Docker instalado en tu sistema
- Docker Compose (opcional)
- GPU NVIDIA con Docker NVIDIA runtime (opcional, para aceleración)

### Opción B: Instalación Manual
- Python 3.7+
- CUDA 11+ (opcional, para GPU)
- Dependencies de COLMAP

## 🚀 Instalación

### Opción A: Usando Docker (Recomendada)

#### 1. Descargar la imagen Docker de COLMAP API

```bash
# Descargar imagen pre-construida
docker pull jourdelune876/colmap-api:latest

# Renombrar para facilitar uso
docker tag jourdelune876/colmap-api:latest colmap-api:latest
```

#### 2. Ejecutar COLMAP API

**CPU only (más lento pero funciona en cualquier sistema):**
```bash
docker run --ipc=host -p 8001:8000 colmap-api:latest
```

**Con GPU (más rápido, requiere NVIDIA):**
```bash
docker run --gpus all --ipc=host -p 8001:8000 colmap-api:latest
```

#### 3. Verificar que funciona

```bash
# Verificar health check
curl http://localhost:8001/health

# Debería responder: {"status":"ok"}
```

#### 4. Acceder a la documentación

Abre tu navegador en: `http://localhost:8001/docs`

### Opción B: Instalación Manual desde Código Fuente

#### 1. Clonar el repositorio

```bash
git clone https://github.com/Jourdelune/colmap-api.git
cd colmap-api
```

#### 2. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows
```

#### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

#### 4. Instalar COLMAP

**En Ubuntu/Debian:**
```bash
# Instalar dependencias del sistema
sudo apt-get install \
    cmake \
    libeigen3-dev \
    libflann-dev \
    libfreeimage-dev \
    libmetis-dev \
    libgoogle-glog-dev \
    libgflags-dev \
    libsqlite3-dev \
    libglew-dev \
    libboost-dev \
    libboost-filesystem-dev \
    libboost-iostreams-dev \
    libboost-program-options-dev \
    libboost-system-dev \
    libboost-thread-dev \
    libboost-timer-dev \
    libboost-regex-dev \
    libboost-date-time-dev \
    libboost-atomic-dev \
    libboost-chrono-dev \
    libboost-python-dev \
    libboost-test-dev

# Clonar y compilar COLMAP
git clone https://github.com/colmap/colmap.git
cd colmap
mkdir build
cd build
cmake ..
make -j8
sudo make install
```

**En Windows:**
Descarga los binarios pre-compilados desde: https://github.com/colmap/colmap/releases

#### 5. Ejecutar COLMAP API

```bash
# Desde el directorio colmap-api
python main.py --port 8001
```

## 🔧 Configuración con Print3D

### 1. Actualizar archivo .env

En `backend/.env`, asegúrate de tener:

```env
COLMAP_API_URL=http://localhost:8001
```

### 2. Iniciar los servidores

**Terminal 1 - COLMAP API:**
```bash
# Si usas Docker
docker run --ipc=host -p 8001:8000 colmap-api:latest

# Si usas instalación manual
cd colmap-api
python main.py --port 8001
```

**Terminal 2 - Backend Print3D:**
```bash
cd backend
python main.py
```

**Terminal 3 - Frontend Print3D:**
```bash
cd frontend
npm run dev
```

## 📊 Uso de la API

### Endpoint Principal: POST /sfm

```bash
curl -X POST "http://localhost:8001/sfm" \
  -F "images=@image1.jpg" \
  -F "images=@image2.jpg" \
  -F "images=@image3.jpg" \
  -F "retrieval_conf_key=netvlad" \
  -F "feature_conf_key=superpoint_aachen" \
  -F "matcher_conf_key=superpoint+lightglue" \
  --output result.zip
```

### Parámetros Configurables

- **retrieval_conf_key**: Configuración de recuperación
  - `netvlad` (default) - Buen balance calidad/velocidad
  - `densevlad` - Más preciso pero más lento

- **feature_conf_key**: Extracción de características
  - `superpoint_aachen` (default) - Alta precisión
  - `disk` - Más rápido
  - `sift` - Clásico, robusto

- **matcher_conf_key**: Matching de características
  - `superpoint+lightglue` (default) - Estado del arte
  - `superglue` - Alta precisión
  - `nn` - Nearest neighbor (más rápido)

## 🎨 Integración con el Frontend

El frontend de Print3D ahora soporta COLMAP automáticamente. Cuando subas un video:

1. Los frames se extraen automáticamente
2. Puedes seleccionar "COLMAP" como método de reconstrucción
3. El sistema enviará los frames a COLMAP API
4. Recibirás un modelo STL listo para impresión

## ⚡ Optimización de Rendimiento

### Para Procesamiento más Rápido:

1. **Usar GPU:**
   ```bash
   docker run --gpus all --ipc=host -p 8001:8000 colmap-api:latest
   ```

2. **Ajustar intervalo de frames:**
   - Menos frames = más rápido pero menos detalle
   - Más frames = más lento pero mejor calidad
   - Recomendado: 20-40 frames para buena balance

3. **Usar configuraciones más rápidas:**
   ```python
   # En colmap_integration.py
   result = colmap.reconstruct_from_images(
       image_paths=image_paths,
       output_dir=output_dir,
       retrieval_conf="netvlad",  # Rápido
       feature_conf="disk",       # Más rápido que superpoint
       matcher_conf="nn"          # Más rápido que lightglue
   )
   ```

## 🐛 Solución de Problemas

### COLMAP API no responde

```bash
# Verificar si el contenedor está corriendo
docker ps

# Ver logs del contenedor
docker logs <container_id>

# Reiniciar el contenedor
docker restart <container_id>
```

### Error de conexión desde backend

```bash
# Verificar que COLMAP API está accesible
curl http://localhost:8001/health

# Verificar configuración en backend/.env
cat backend/.env | grep COLMAP
```

### Memoria insuficiente

```bash
# Aumentar memoria de Docker
# En Docker Desktop: Settings > Resources > Memory
# Recomendado: 8GB+ para procesamiento serio
```

### Procesamiento muy lento

1. Verifica que estás usando GPU (si disponible)
2. Reduce el número de frames
3. Usa configuraciones más rápidas (disk + nn)
4. Asegúrate de tener suficiente RAM

## 📚 Recursos Adicionales

- **COLMAP oficial:** https://colmap.github.io/
- **COLMAP API GitHub:** https://github.com/Jourdelune/colmap-api
- **Documentación COLMAP API:** http://localhost:8001/docs (cuando esté corriendo)
- **PyCOLMAP:** https://colmap.github.io/pycolmap/

## 🆚 Comparación con Otras Soluciones

| Característica | COLMAP API | Free.ai | Meshy |
|---|---|---|---|
| Coste | Gratis | Freemium | De pago |
| Calidad | Alta | Media-Alta | Alta |
| Velocidad | Media | Rápido | Rápido |
| Control | Total | Limitado | Limitado |
| Límites | Ninguno | 5k tokens/día | Por modelo |
| Self-hosted | Sí | No | No |

## 🎯 Conclusión

COLMAP API es la mejor opción para Print3D porque:
- ✅ 100% gratis y sin límites
- ✅ Calidad profesional para impresión 3D
- ✅ Control total del proceso
- ✅ Fácil integración con tu stack Python
- ✅ Comunidad activa y documentación extensa

¡Ahora tienes una solución completa de fotogrametría gratuita para tu proyecto!
