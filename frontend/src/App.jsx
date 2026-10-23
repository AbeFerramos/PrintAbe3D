import React, { useState, useEffect } from 'react';
import VideoUploader from './components/VideoUploader';
import ImageUploader from './components/ImageUploader';
import Model3DViewer from './components/Model3DViewer';
import ProcessingStatus from './components/ProcessingStatus';
import { uploadVideo, uploadImages, getJobStatus, reconstruct3D, downloadModel, pollJobStatus, cleanupJob } from './services/api';
import { Download, RefreshCw, Trash2, Film, ImageIcon } from 'lucide-react';

function App() {
  const [uploadMode, setUploadMode] = useState('video'); // 'video' or 'images'
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [reconstructing, setReconstructing] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [modelUrl, setModelUrl] = useState(null);
  const [error, setError] = useState(null);

  const handleUpload = async (file, frameInterval) => {
    setUploading(true);
    setError(null);
    setModelUrl(null);

    try {
      const response = await uploadVideo(file, frameInterval);
      setJobId(response.job_id);
      
      // Iniciar polling del estado
      pollJobStatus(response.job_id, (jobStatus) => {
        setStatus(jobStatus);
        
        if (jobStatus.status === 'failed') {
          setError(jobStatus.error || 'Error en el procesamiento');
          setUploading(false);
        } else if (jobStatus.status === 'completed') {
          setUploading(false);
        }
      });
    } catch (err) {
      setError('Error al subir el video: ' + err.message);
      setUploading(false);
    }
  };

  const handleImageUpload = async (files) => {
    setUploading(true);
    setError(null);
    setModelUrl(null);

    try {
      const response = await uploadImages(files);
      setJobId(response.job_id);
      
      // Las imágenes ya están listas para reconstrucción
      setStatus({
        status: 'completed',
        stage: 'ready_for_reconstruction',
        progress: 100,
        message: `${response.total_images} imágenes listas para reconstrucción 3D`,
        total_images: response.total_images
      });
      
      setUploading(false);
    } catch (err) {
      setError('Error al subir las imágenes: ' + err.message);
      setUploading(false);
    }
  };

  const handleReconstruct = async () => {
    if (!jobId) return;

    setReconstructing(true);
    setError(null);

    try {
      // Usar COLMAP por defecto (gratuito y open source)
      await reconstruct3D(jobId, 'colmap');
      
      // Continuar polling para la reconstrucción
      pollJobStatus(jobId, (jobStatus) => {
        setStatus(jobStatus);
        
        if (jobStatus.status === 'failed') {
          setError(jobStatus.error || 'Error en la reconstrucción');
          setReconstructing(false);
        } else if (jobStatus.status === 'completed' && 
                   jobStatus.stage === 'reconstruction_completed') {
          setReconstructing(false);
          setModelUrl(`/api/v1/download/${jobId}`);
        }
      });
    } catch (err) {
      setError('Error al iniciar reconstrucción: ' + err.message);
      setReconstructing(false);
    }
  };

  const handleDownload = async () => {
    if (!jobId) return;

    setDownloading(true);
    try {
      await downloadModel(jobId, 'stl');
    } catch (err) {
      setError('Error al descargar el modelo: ' + err.message);
    } finally {
      setDownloading(false);
    }
  };

  const handleReset = async () => {
    if (jobId) {
      try {
        await cleanupJob(jobId);
      } catch (err) {
        console.error('Error limpiando job:', err);
      }
    }
    
    setJobId(null);
    setStatus(null);
    setModelUrl(null);
    setError(null);
    setUploading(false);
    setReconstructing(false);
    setDownloading(false);
  };

  return (
    <div className="min-h-screen">
      <header className="header">
        <h1>🎥 Print3D Converter</h1>
        <p>Convierte videos 360° en modelos 3D listos para impresión</p>
      </header>

      <div className="container">
        {error && (
          <div className="error-message">
            <strong>Error:</strong> {error}
            <button
              onClick={() => setError(null)}
              className="float-right text-red-700 hover:text-red-900"
            >
              ×
            </button>
          </div>
        )}

        <div className="card">
          <div className="flex gap-4 mb-4">
            <button
              onClick={() => setUploadMode('video')}
              className={`flex-1 py-3 px-4 rounded-lg font-semibold transition-all ${
                uploadMode === 'video'
                  ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <Film className="inline mr-2" size={20} />
              Video 360°
            </button>
            <button
              onClick={() => setUploadMode('images')}
              className={`flex-1 py-3 px-4 rounded-lg font-semibold transition-all ${
                uploadMode === 'images'
                  ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <ImageIcon className="inline mr-2" size={20} />
              Imágenes
            </button>
          </div>

          {uploadMode === 'video' ? (
            <VideoUploader 
              onUpload={handleUpload} 
              uploading={uploading} 
            />
          ) : (
            <ImageUploader 
              onUpload={handleImageUpload} 
              uploading={uploading} 
            />
          )}
        </div>
        
        {status && (
          <ProcessingStatus
            status={status}
            onReconstruct={handleReconstruct}
            reconstructing={reconstructing}
          />
        )}

        <Model3DViewer
          modelUrl={modelUrl}
          onDownload={handleDownload}
          downloading={downloading}
        />

        {jobId && (
          <div className="card">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="font-semibold">ID del Job: {jobId}</h3>
                <p className="text-sm text-gray-500">
                  Usa este ID para rastrear el estado del procesamiento
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    if (jobId) {
                      getJobStatus(jobId).then(setStatus);
                    }
                  }}
                  className="btn btn-secondary"
                  disabled={uploading || reconstructing}
                >
                  <RefreshCw size={16} className="inline mr-1" />
                  Actualizar
                </button>
                <button
                  onClick={handleReset}
                  className="btn btn-secondary"
                  disabled={uploading || reconstructing}
                >
                  <Trash2 size={16} className="inline mr-1" />
                  Limpiar
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="card">
          <h2>📋 Instrucciones</h2>
          <ol className="list-decimal list-inside space-y-2 text-gray-700">
            <li>Sube un video rotativo de 360° de tu objeto</li>
            <li>Espera a que se extraigan los fotogramas clave</li>
            <li>Inicia la reconstrucción 3D automática</li>
            <li>Previsualiza el modelo en el visor 3D</li>
            <li>Descarga el archivo STL listo para impresión</li>
          </ol>
          
          <div className="mt-4 p-4 bg-blue-50 rounded-lg">
            <h3 className="font-semibold text-blue-800 mb-2">💡 Consejos</h3>
            <ul className="list-disc list-inside text-sm text-blue-700 space-y-1">
              <li>Usa iluminación uniforme para mejores resultados</li>
              <li>Mantén el objeto centrado durante el video</li>
              <li>Evita fondos muy complejos o en movimiento</li>
              <li>Un intervalo de frames menor da más detalle pero tarda más</li>
            </ul>
          </div>
        </div>
      </div>

      <footer className="text-center py-8 text-white opacity-75">
        <p>Print3D Converter - Transforma videos en modelos 3D imprimibles</p>
      </footer>
    </div>
  );
}

export default App;
