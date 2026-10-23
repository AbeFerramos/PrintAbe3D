# 🚀 Guía de Inicio Rápido - Print3D con COLMAP API

## 📋 Resumen de la Solución Implementada

He integrado **COLMAP API** en tu proyecto Print3D, que es una solución **100% gratuita y open source** para reconstrucción 3D desde imágenes/videos.

### ✅ Lo que ya está implementado:

1. **Backend Python con FastAPI**
   - API completa para carga de videos/imágenes
   - Extracción automática de fotogramas
   - Integración con COLMAP API
   - Procesamiento de mallas 3D
   - Exportación a STL para impresión

2. **Frontend React**
   - Interfaz moderna con dos modos: Video e Imágenes
   - Carga con drag & drop
   - Visor 3D interactivo
   - Seguimiento en tiempo real del procesamiento

3. **COLMAP Integration**
   - Cliente Python para comunicación con COLMAP API
   - Conversión automática a STL
   - Manejo de errores robusto

## 🔧 Pasos para Poner en Marcha

### Paso 1: Iniciar Docker Desktop

**Importante:** Debes iniciar Docker Desktop manualmente en Windows:

1. Busca "Docker Desktop" en el menú de inicio
2. Inicia la aplicación
3. Espera a que el icono de Docker esté activo en la barra de tareas
4. Verifica que Docker está funcionando:
   ```bash
   docker --version
   docker ps
   ```

### Paso 2: Iniciar COLMAP API

Una vez Docker Desktop esté corriendo:

```bash
# Descargar la imagen de COLMAP API
docker pull jourdelune876/colmap-api:latest

# Ejecutar COLMAP API en el puerto 8001
docker run --ipc=host -p 8001:8000 jourdelune876/colmap-api:latest
```

**Verificar que funciona:**
```bash
curl http://localhost:8001/health
# Debería responder: {"status":"ok"}
```

### Paso 3: Configurar e Iniciar el Backend

```bash
cd backend

# Crear entorno virtual
python -m venv venv

# Activar entorno (Windows)
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
copy .env.example .env
# Editar .env y asegúrate de que COLMAP_API_URL=http://localhost:8001

# Iniciar servidor
python main.py
```

El backend estará disponible en `http://localhost:8000`

### Paso 4: Configurar e Iniciar el Frontend

```bash
cd frontend

# Instalar dependencias
npm install

# Configurar variables de entorno
copy .env.example .env
# Editar .env si necesitas cambiar la URL del API

# Iniciar servidor de desarrollo
npm run dev
```

El frontend estará disponible en `http://localhost:5173`

## 🎯 Probar con tu Video

Una vez todo esté corriendo:

1. **Abre el navegador:** `http://localhost:5173`

2. **Sube tu video:**
   - Usa el botón "Video 360°"
   - Arrastra tu video "WhatsApp Video 2026-09-06 at 19.59.50.mp4"
   - O haz clic para seleccionarlo

3. **Configura el intervalo de frames:**
   - Usa el slider para ajustar (recomendado: 20-30)
   - Menor intervalo = más detalle pero más tiempo

4. **Inicia el procesamiento:**
   - Haz clic en "Iniciar Procesamiento"
   - Espera a que se extraigan los frames
   - Verás el progreso en tiempo real

5. **Reconstrucción 3D:**
   - Cuando los frames estén listos, haz clic en "Iniciar Reconstrucción 3D"
   - El sistema usará COLMAP API (gratuito) para generar el modelo
   - Este proceso puede tomar varios minutos

6. **Descargar el modelo:**
   - Cuando la reconstrucción esté completa
   - Previsualiza el modelo en el visor 3D
   - Descarga el archivo STL listo para impresión

## 🎨 Usar el Modo de Imágenes (Alternativa)

Si prefieres usar imágenes en lugar de video:

1. **Selecciona "Imágenes"** en la interfaz
2. **Sube múltiples fotos** desde diferentes ángulos
3. **Mínimo 8-12 imágenes** para buena reconstrucción
4. **Captura 360°** alrededor del objeto
5. **Iluminación uniforme** y fondo neutro

## 📊 Estructura de Terminales

Necesitarás 3 terminales:

**Terminal 1 - COLMAP API:**
```bash
docker run --ipc=host -p 8001:8000 jourdelune876/colmap-api:latest
```

**Terminal 2 - Backend:**
```bash
cd backend
venv\Scripts\activate
python main.py
```

**Terminal 3 - Frontend:**
```bash
cd frontend
npm run dev
```

## 🔍 Solución de Problemas

### Docker no responde
```bash
# Asegúrate de que Docker Desktop está corriendo
# Abre Docker Desktop desde el menú de inicio
# Espera a que el icono esté activo en la barra de tareas
```

### COLMAP API no arranca
```bash
# Verifica que el puerto 8001 está libre
netstat -ano | findstr :8001

# Si está ocupado, usa otro puerto
docker run --ipc=host -p 8002:8000 jourdelune876/colmap-api:latest
# Y actualiza backend/.env: COLMAP_API_URL=http://localhost:8002
```

### Error de dependencias Python
```bash
# Asegúrate de tener Python 3.7+
python --version

# Actualizar pip
python -m pip install --upgrade pip

# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall
```

### Error de dependencias Node
```bash
# Limpiar caché de npm
npm cache clean --force

# Reinstalar dependencias
rm -rf node_modules package-lock.json
npm install
```

## 📚 Documentación Adicional

- **COLMAP Setup:** `backend/COLMAP_SETUP.md` - Guía detallada de COLMAP
- **Backend README:** `backend/README.md` - Documentación del backend
- **Frontend README:** `frontend/README.md` - Documentación del frontend
- **Main README:** `README.md` - Documentación general del proyecto

## 🎓 Consejos para Mejores Resultados

### Para Videos:
- ✅ Rotación suave y constante del objeto
- ✅ Iluminación uniforme (evita sombras duras)
- ✅ Fondo neutro o liso
- ✅ Objeto centrado en el frame
- ✅ Duración de 10-30 segundos es ideal

### Para Imágenes:
- ✅ Mínimo 8-12 imágenes (ideal 20-30)
- ✅ Captura cada 15-30° de rotación
- ✅ Iluminación constante en todas las fotos
- ✅ Fondo neutro o transparente
- ✅ Enfoque nítido en el objeto

### Para Impresión 3D:
- ✅ El modelo STL estará listo para slicer
- ✅ Verifica la escala antes de imprimir
- ✅ Revisa si hay agujeros o geometría no válida
- ✅ Considera añadir soportes si es necesario

## 🆓 ¿Por qué COLMAP API?

**Ventajas:**
- ✅ 100% gratis y open source
- ✅ Calidad profesional para impresión 3D
- ✅ Sin límites de uso
- ✅ Control total del proceso
- ✅ Funciona offline (self-hosted)
- ✅ Comunidad activa y documentación extensa

**Comparación:**
- **COLMAP API:** Gratis, calidad profesional, tú controlas todo
- **Free.ai:** Freemium (5k tokens/día), más rápido pero límites
- **Meshy/Tripo3D:** De pago, muy rápido pero costoso a largo plazo

## 🚀 Siguientes Pasos

Una que todo funcione con tu video:

1. **Experimenta con diferentes intervalos de frames**
2. **Prueba con diferentes configuraciones de COLMAP**
3. **Añade más características de edición de mallas**
4. **Optimiza el rendimiento para tu hardware**
5. **Considera integrar otras APIs de pago para opciones más rápidas**

¡Disfruta tu solución de conversión de video a 3D completamente gratuita! 🎉
