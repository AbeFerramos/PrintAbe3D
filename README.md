# Print3D - Video to 3D Converter

Aplicación full-stack para convertir videos rotativos de 360° en modelos 3D listos para impresión 3D.

## 🎯 Objetivo

Transformar videos o series de imágenes de objetos en modelos 3D digitales exportables a STL para impresión 3D.

## 📹 Video vs Imágenes para Reconstrucción 3D

### Usar Video (Recomendado para rotación 360°)
**Ventajas:**
- ✅ Captura automática de múltiples ángulos
- ✅ Movimiento continuo asegura cobertura completa
- ✅ Más fácil de capturar (solo un video)
- ✅ El sistema extrae frames automáticamente

**Ideal para:**
- Objetos pequeños que puedes rotar
- Captura con smartphone o cámara
- Cuando quieres automatizar el proceso

### Usar Imágenes Directamente
**Ventajas:**
- ✅ Control total sobre cada ángulo
- ✅ Mejor calidad por imagen (foco, iluminación)
- ✅ Puedes seleccionar solo los mejores ángulos
- ✅ Mayor flexibilidad en configuración

**Ideal para:**
- Objetos grandes o difíciles de rotar
- Cuando necesitas control preciso
- Fotografía profesional con trípode
- Objetos que requieren iluminación específica

### 🏆 Recomendación para tu Proyecto

**Para empezar:** Usa el video que ya tienes
- El sistema extraerá automáticamente los frames clave
- COLMAP API procesará estos frames para crear el modelo 3D
- Es más rápido y automatizado

**Para mejor calidad:** Considera capturar imágenes específicas
- Toma fotos cada 15-30° de rotación
- Usa iluminación uniforme
- Asegura fondo neutro
- Controla el enfoque en cada foto

## 🏗️ Arquitectura Técnica

### Frontend
- **React 18** + **TypeScript** para interfaz de usuario moderna
- **Three.js** + **@react-three/fiber** para visualización 3D interactiva
- **Vite** como bundler para desarrollo rápido
- **React Dropzone** para carga de videos/imagenes
- **Axios** para comunicación con backend

### Backend
- **Python 3.10+** con **FastAPI** para API REST eficiente
- **OpenCV** para extracción de fotogramas y procesamiento de video
- **Open3D** y **Trimesh** para procesamiento de mallas 3D
- **PyTorch** para modelos de IA (futuro)
- **Celery + Redis** para procesamiento asíncrono (futuro)

### Estrategia de Reconstrucción 3D
- **Fase inicial (MVP):** **COLMAP API (100% gratis y open source)** - Fotogrametría de alta calidad
- **Alternativa premium:** APIs de IA 3D (Meshy, Tripo3D, Luma AI) - Más rápidas pero de pago
- **Fase posterior:** Fotogrametría local avanzada (COLMAP + OpenMVS) - Mayor control

## 📋 Hoja de Ruta

### Fase 1: MVP Básico (2-3 semanas)
- ✅ Setup del proyecto (frontend + backend)
- ✅ Backend: API para recibir videos y extraer fotogramas
- ✅ Frontend: Interfaz de carga de videos y visualización de progreso
- ⏳ Integración con API de IA 3D para reconstrucción inicial
- ⏳ Exportación básica a STL/3MF

### Fase 2: Pipeline de Reparación de Mallas (3-4 semanas)
- ⏳ Implementación de algoritmos de reparación de mallas
- ⏳ Detección y corrección de geometría non-manifold
- ⏳ Cierre de huecos (watertight mesh)
- ⏳ Remeshing y simplificación de geometría
- ⏳ Validación para impresión 3D

### Fase 3: Visor 3D Interactivo (2-3 semanas)
- ⏳ Visor 3D con controles de cámara y iluminación
- ⏳ Herramientas de edición básica (escala, rotación)
- ⏳ Vista previa de soportes de impresión
- ⏳ Exportación multi-formato (STL, 3MF, OBJ)

## 🚀 Instalación y Configuración

### Paso 1: Configurar COLMAP API (Solución Gratuita)

#### Opción A: Docker (Recomendada)
```bash
# Iniciar COLMAP API con la configuración del proyecto
docker compose up -d colmap

# Verificar que funciona
curl http://localhost:8001/health
```

#### Opción B: Instalación Manual
Consulta `backend/COLMAP_SETUP.md` para instrucciones detalladas.

### Paso 2: Configurar el Backend

```bash
cd backend

# Crear entorno virtual
python -m venv .venv

# Activar entorno (Windows)
.venv\Scripts\activate

# Activar entorno (Linux/Mac)
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env y asegúrate de que COLMAP_API_URL=http://localhost:8001

# Ejecutar servidor
python main.py
```

El backend estará disponible en `http://localhost:8000`

### Frontend

```bash
cd frontend

# Instalar dependencias
npm install

# Configurar variables de entorno
cp .env.example .env
# Editar .env según necesites

# Ejecutar servidor de desarrollo
npm run dev
```

El frontend estará disponible en `http://localhost:5173`

## 📁 Estructura del Proyecto

```
print3d/
├── backend/
│   ├── main.py                 # API FastAPI principal
│   ├── mesh_processor.py       # Procesamiento de mallas 3D
│   ├── requirements.txt        # Dependencias Python
│   ├── .env.example           # Configuración de ejemplo
│   └── README.md              # Documentación backend
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── VideoUploader.jsx
│   │   │   ├── Model3DViewer.jsx
│   │   │   └── ProcessingStatus.jsx
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.js
│   ├── .env.example
│   └── README.md
└── README.md                  # Este archivo
```

## 🔧 Uso

### Prerrequisitos Importantes

Antes de usar la aplicación, asegúrate de:

1. **COLMAP API ejecutándose:**
   ```bash
   # Terminal 1 - COLMAP API
   docker compose up -d colmap
   ```

2. **Backend Print3D ejecutándose:**
   ```bash
   # Terminal 2 - Backend
   cd backend
   python main.py
   ```

3. **Frontend Print3D ejecutándose:**
   ```bash
   # Terminal 3 - Frontend
   cd frontend
   npm run dev
   ```

### Flujo de Trabajo

1. **Abrir el navegador:**
   - Navega a `http://localhost:5173`

2. **Elegir método de captura:**
   - **Video 360°:** Sube un video rotativo de tu objeto
   - **Imágenes:** Sube múltiples fotos desde diferentes ángulos

3. **Procesamiento automático:**
   - El sistema extrae frames (si usas video)
   - Analiza la calidad del material
   - Envía a COLMAP API para reconstrucción 3D

4. **Reconstrucción 3D:**
   - Selecciona "Iniciar Reconstrucción 3D"
   - El sistema usa COLMAP (gratuito) para generar el modelo
   - Monitorea el progreso en tiempo real

5. **Previsualización y descarga:**
   - Visualiza el modelo en el visor 3D interactivo
   - Descarga el archivo STL listo para impresión

## 🎨 Características Principales

### Backend
- ✅ Carga de videos (MP4, AVI, MOV, MKV)
- ✅ Extracción automática de fotogramas clave
- ✅ Análisis de calidad de video
- ✅ Preparación para reconstrucción 3D
- ✅ Herramientas de reparación y validación de mallas disponibles en el backend
- ⏳ Reparación automática integrada en la reconstrucción
- ✅ Exportación y descarga STL en el flujo principal (3MF/OBJ pendientes)

### Frontend
- ✅ Interfaz moderna y responsiva
- ✅ Carga de videos con drag & drop
- ✅ Seguimiento en tiempo real del procesamiento
- ✅ Visor 3D interactivo que carga el STL reconstruido
- ✅ Descarga de modelos STL (3MF/OBJ pendientes)
- ✅ Diseño intuitivo con guía paso a paso

## 🔮 Próximos Pasos

1. **Integración con APIs de IA 3D (opcional):**
   - Meshy.ai (alternativa premium)
   - Tripo3D (alternativa premium)
   - Luma AI (alternativa premium)

2. **Fotogrametría local avanzada:**
   - COLMAP para structure-from-motion ✅ (ya integrado)
   - OpenMVS para reconstrucción densa
   - MeshLab para post-procesamiento

3. **Mejoras del visor 3D:**
   - Carga real de archivos STL
   - Herramientas de edición
   - Análisis de imprimibilidad

4. **Optimizaciones:**
   - Cola de procesamiento (Celery + Redis)
   - Caché de modelos
   - Compresión de archivos

## 🆓 Opciones Gratuitas Disponibles

### COLMAP API (Integrado - Recomendado)
- **Coste:** 100% gratis
- **Calidad:** Profesional
- **Velocidad:** Media (mejor con GPU)
- **Uso:** Self-hosted con Docker
- **Documentación:** `backend/COLMAP_SETUP.md`

### Free.ai (Alternativa en la Nube)
- **Coste:** Freemium (5,000 tokens gratis/día)
- **Modelos:** InstantMesh, TripoSR
- **Calidad:** Muy buena para IA generativa
- **Velocidad:** Rápido
- **Uso:** API en la nube

### Fotogrametría Local (Avanzado)
- **Coste:** Gratis (requiere hardware)
- **Herramientas:** COLMAP + OpenMVS + MeshLab
- **Calidad:** Excelente
- **Velocidad:** Variable según hardware
- **Uso:** Software local

## 🛠️ Tecnologías

### Backend
- FastAPI
- OpenCV
- Open3D
- Trimesh
- NumPy
- Pillow

### Frontend
- React 18
- Three.js
- @react-three/fiber
- @react-three/drei
- Vite
- Axios

## 📝 Notas de Desarrollo

- El backend usa procesamiento en background para no bloquear la API
- El frontend implementa polling para actualización de estado en tiempo real
- El sistema está preparado para escalar con múltiples workers
- La arquitectura modular permite añadir nuevos métodos de reconstrucción fácilmente

## 🤝 Contribución

Este proyecto está en desarrollo activo. Las áreas donde se necesita ayuda:

- Integración con APIs de IA 3D específicas
- Implementación de fotogrametría local
- Mejoras en el visor 3D
- Optimización de rendimiento
- Testing y validación

## 📄 Licencia

Este proyecto es para fines educativos y de desarrollo.

## 🙋 Soporte

Para dudas o problemas, consulta la documentación específica:
- Backend: `backend/README.md`
- Frontend: `frontend/README.md`

---

**Desarrollado con ❤️ para la comunidad de impresión 3D**
