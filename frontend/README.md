# Frontend - Print3D Converter

Frontend en React para la aplicación de conversión de video a modelo 3D.

## Características

- ✅ Interfaz moderna y responsiva
- ✅ Carga de videos con drag & drop
- ✅ Seguimiento en tiempo real del procesamiento
- ✅ Visor 3D interactivo con Three.js
- ✅ Descarga de modelos STL/3MF/OBJ
- ✅ Diseño intuitivo con guía paso a paso

## Instalación

```bash
# Instalar dependencias
npm install

# Copiar configuración de entorno
cp .env.example .env
```

## Configuración

Edita el archivo `.env`:

```env
VITE_API_URL=http://localhost:8000
```

## Ejecución

```bash
# Desarrollo
npm run dev

# Producción
npm run build
npm run preview
```

## Componentes

### VideoUploader
Componente para carga de videos con drag & drop y configuración de intervalo de frames.

### Model3DViewer
Visor 3D interactivo usando Three.js y React Three Fiber con controles de órbita.

### ProcessingStatus
Muestra el estado del procesamiento con barras de progreso y análisis de calidad.

## Stack Tecnológico

- **React 18** - Framework UI
- **Vite** - Build tool y dev server
- **Three.js** - Motor 3D
- **@react-three/fiber** - Renderer React para Three.js
- **@react-three/drei** - Helpers y abstracciones para R3F
- **Axios** - Cliente HTTP
- **React Dropzone** - Carga de archivos
- **Lucide React** - Iconos

## Integración con Backend

El frontend se comunica con el backend Python a través de la API REST:

```javascript
import { uploadVideo, getJobStatus, reconstruct3D, downloadModel } from './services/api';

// Subir video
const response = await uploadVideo(file, 30);

// Obtener estado
const status = await getJobStatus(response.job_id);

// Reconstruir 3D
await reconstruct3D(jobId, 'api_external');

// Descargar modelo
await downloadModel(jobId, 'stl');
```

## Desarrollo

```bash
# Iniciar servidor de desarrollo
npm run dev

# Abrir http://localhost:5173
```

## Estructura del Proyecto

```
frontend/
├── src/
│   ├── components/
│   │   ├── VideoUploader.jsx      # Carga de videos
│   │   ├── Model3DViewer.jsx      # Visor 3D
│   │   └── ProcessingStatus.jsx   # Estado del procesamiento
│   ├── services/
│   │   └── api.js                 # Cliente API
│   ├── App.jsx                    # Componente principal
│   ├── main.jsx                   # Entry point
│   └── index.css                  # Estilos globales
├── index.html                     # HTML template
├── package.json                   # Dependencias
├── vite.config.js                 # Configuración Vite
└── README.md                      # Este archivo
```

## Próximas Características

- [ ] Carga de múltiples imágenes como alternativa a video
- [ ] Editor de mallas básico (escala, rotación)
- [ ] Vista previa de soportes de impresión
- [ ] Comparación de diferentes métodos de reconstrucción
- [ ] Historial de proyectos
- [ ] Modo oscuro/claro
