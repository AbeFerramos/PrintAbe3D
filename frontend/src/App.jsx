import React, { useRef, useState } from 'react';
import VideoUploader from './components/VideoUploader';
import ImageUploader from './components/ImageUploader';
import Model3DViewer from './components/Model3DViewer';
import ProcessingStatus from './components/ProcessingStatus';
import {
  uploadVideo, uploadImages, getJobStatus, reconstruct3D, downloadModel,
  pollJobStatus, cleanupJob, getModelUrl
} from './services/api';
import {
  Box, Camera, Check, ChevronRight, HelpCircle, Film,
  Image as ImageIcon, Layers, RefreshCw, ScanLine, Sparkles, Trash2
} from 'lucide-react';

function App() {
  const [uploadMode, setUploadMode] = useState('video');
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [reconstructing, setReconstructing] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [modelUrl, setModelUrl] = useState(null);
  const [error, setError] = useState(null);
  const stopPolling = useRef(null);

  const getErrorMessage = (err) => err.response?.data?.detail || err.message || 'Error desconocido';

  const handleUpload = async (file, frameInterval) => {
    setUploading(true);
    setError(null);
    setModelUrl(null);
    setStatus(null);
    setJobId(null);
    try {
      const response = await uploadVideo(file, frameInterval);
      setJobId(response.job_id);
      stopPolling.current = pollJobStatus(response.job_id, (jobStatus) => {
        setStatus(jobStatus);
        if (jobStatus.status === 'failed' || jobStatus.status === 'error') {
          setError(jobStatus.error || 'Error en el procesamiento');
          setUploading(false);
        } else if (jobStatus.status === 'completed') {
          setUploading(false);
        }
      });
    } catch (err) {
      setError('Error al subir el vídeo: ' + getErrorMessage(err));
      setUploading(false);
    }
  };

  const handleImageUpload = async (files) => {
    setUploading(true);
    setError(null);
    setModelUrl(null);
    setStatus(null);
    setJobId(null);
    try {
      const response = await uploadImages(files);
      setJobId(response.job_id);
      setStatus({
        status: 'completed',
        stage: 'ready_for_reconstruction',
        progress: 100,
        message: `${response.total_images} imágenes listas para reconstrucción 3D`,
        total_images: response.total_images
      });
      setUploading(false);
      return true;
    } catch (err) {
      setError('Error al subir las imágenes: ' + getErrorMessage(err));
      setUploading(false);
      return false;
    }
  };

  const handleReconstruct = async () => {
    if (!jobId) return;
    setReconstructing(true);
    setError(null);
    try {
      await reconstruct3D(jobId, 'colmap');
      stopPolling.current = pollJobStatus(jobId, (jobStatus) => {
        setStatus(jobStatus);
        if (jobStatus.status === 'failed' || jobStatus.status === 'error') {
          setError(jobStatus.error || 'Error en la reconstrucción');
          setReconstructing(false);
        } else if (jobStatus.status === 'completed' && jobStatus.stage === 'reconstruction_completed') {
          setReconstructing(false);
          setModelUrl(getModelUrl(jobId));
        }
      });
    } catch (err) {
      setError('Error al iniciar la reconstrucción: ' + getErrorMessage(err));
      setReconstructing(false);
    }
  };

  const handleDownload = async () => {
    if (!jobId) return;
    setDownloading(true);
    try {
      await downloadModel(jobId, 'stl');
    } catch (err) {
      setError('Error al descargar el modelo: ' + getErrorMessage(err));
    } finally {
      setDownloading(false);
    }
  };

  const handleReset = async () => {
    stopPolling.current?.();
    stopPolling.current = null;
    if (jobId) {
      try { await cleanupJob(jobId); }
      catch (err) { console.error('Error limpiando job:', err); }
    }
    setJobId(null);
    setStatus(null);
    setModelUrl(null);
    setError(null);
    setUploading(false);
    setReconstructing(false);
    setDownloading(false);
  };

  const captureDone = Boolean(status && (status.stage === 'ready_for_reconstruction' || status.stage?.startsWith('reconstruction')));
  const processActive = reconstructing || status?.stage === 'ready_for_reconstruction' || Boolean(status?.stage?.startsWith('reconstruct'));

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><Box size={21} strokeWidth={2.4} /></div>
          <div className="brand-name">Print3D<span>STUDIO</span></div>
        </div>

        <p className="nav-label">Workspace</p>
        <nav className="side-nav" aria-label="Navegación principal">
          <a className="nav-link active" href="#workspace"><ScanLine size={17} /><span>Nueva reconstrucción</span></a>
          <a className="nav-link" href="#workflow"><Layers size={17} /><span>Flujo de trabajo</span></a>
          <a className="nav-link" href="#guide"><HelpCircle size={17} /><span>Guía de captura</span></a>
        </nav>

        <div className="sidebar-spacer" />
        <div className="capture-tip">
          <div className="capture-tip-icon"><Sparkles size={16} /></div>
          <strong>Un buen escaneo empieza aquí</strong>
          <p>Rodea el objeto con la cámara y mantén una iluminación constante.</p>
        </div>
        <div className="sidebar-foot"><span />Fotogrametría COLMAP</div>
      </aside>

      <div className="main-column">
        <header className="topbar">
          <div className="breadcrumb"><span>Print3D Studio</span><ChevronRight size={13} /><strong>Espacio de trabajo</strong></div>
          <div className="topbar-meta"><span className="service-dot" /> Proyecto local <span aria-hidden="true">·</span> Exportación STL</div>
        </header>

        <main className="workspace" id="workspace">
          <section className="page-heading">
            <div>
              <p className="eyebrow">Fotogrametría · Impresión 3D</p>
              <h1>De la captura al modelo.</h1>
              <p>Convierte un recorrido alrededor de tu objeto en una malla 3D lista para revisar y exportar.</p>
            </div>
            <div className="format-tag"><Box size={15} /> Modelo final <strong>STL</strong></div>
          </section>

          <section className="workflow" id="workflow" aria-label="Pasos del proceso">
            <div className={`workflow-step ${captureDone ? 'done' : 'active'}`}>
              <span className="step-number">{captureDone ? <Check size={14} /> : '01'}</span>
              <span className="step-copy">Captura<small>Vídeo o imágenes</small></span>
            </div>
            <div className={`workflow-step ${processActive ? 'active' : ''} ${modelUrl ? 'done' : ''}`}>
              <span className="step-number">{modelUrl ? <Check size={14} /> : '02'}</span>
              <span className="step-copy">Reconstrucción<small>Procesamiento COLMAP</small></span>
            </div>
            <div className={`workflow-step ${modelUrl ? 'active done' : ''}`}>
              <span className="step-number">{modelUrl ? <Check size={14} /> : '03'}</span>
              <span className="step-copy">Revisión y exportación<small>Previsualiza y descarga</small></span>
            </div>
          </section>

          {error && (
            <div className="error-message notice" role="alert">
              <span><strong>Se produjo un error.</strong> {error}</span>
              <button onClick={() => setError(null)} className="error-dismiss" aria-label="Cerrar aviso">×</button>
            </div>
          )}

          <section className="studio-grid" aria-label="Panel de reconstrucción">
            <div className="panel">
              <div className="panel-heading">
                <div className="panel-title">
                  <div className="panel-icon"><Camera size={17} /></div>
                  <div><h2>Fuente del modelo</h2><p>Elige cómo quieres capturar tu objeto</p></div>
                </div>
                <span className="viewer-heading-right">PASO 01</span>
              </div>
              <div className="panel-body">
                <div className="mode-switch" role="tablist" aria-label="Modo de captura">
                  <button role="tab" aria-selected={uploadMode === 'video'} onClick={() => setUploadMode('video')} className={`mode-button ${uploadMode === 'video' ? 'active' : ''}`}>
                    <Film size={15} /> Vídeo 360°
                  </button>
                  <button role="tab" aria-selected={uploadMode === 'images'} onClick={() => setUploadMode('images')} className={`mode-button ${uploadMode === 'images' ? 'active' : ''}`}>
                    <ImageIcon size={15} /> Imágenes
                  </button>
                </div>

                {uploadMode === 'video' ? (
                  <VideoUploader onUpload={handleUpload} uploading={uploading} />
                ) : (
                  <ImageUploader onUpload={handleImageUpload} uploading={uploading} />
                )}
              </div>
            </div>

            <Model3DViewer modelUrl={modelUrl} onDownload={handleDownload} downloading={downloading} />
          </section>

          {status && <ProcessingStatus status={status} onReconstruct={handleReconstruct} reconstructing={reconstructing} />}

          {jobId && (
            <section className="panel job-card">
              <div className="job-copy">
                <span>Sesión de trabajo</span>
                <strong>{jobId}</strong>
                <p>Consulta el estado o limpia los archivos de esta sesión.</p>
              </div>
              <div className="job-actions">
                <button onClick={() => getJobStatus(jobId).then(setStatus).catch((err) => setError(getErrorMessage(err)))} className="secondary-button" disabled={uploading || reconstructing}>
                  <RefreshCw size={14} /> Actualizar
                </button>
                <button onClick={handleReset} className="secondary-button" disabled={uploading || reconstructing}>
                  <Trash2 size={14} /> Limpiar sesión
                </button>
              </div>
            </section>
          )}

          <section className="panel guide-card" id="guide">
            <div className="panel-body">
              <div className="guide-header"><div className="panel-icon"><Sparkles size={16} /></div><h2>Consejos para un mejor resultado</h2></div>
              <div className="guide-grid">
                <div className="guide-item"><span className="guide-number">01</span><div><strong>Cubre todos los ángulos</strong><p>Rodea el objeto y mantén bastante solapamiento entre imágenes consecutivas.</p></div></div>
                <div className="guide-item"><span className="guide-number">02</span><div><strong>Cuida la iluminación</strong><p>Usa luz uniforme, evita reflejos y procura que el objeto no se mueva.</p></div></div>
                <div className="guide-item"><span className="guide-number">03</span><div><strong>Enfoca los detalles</strong><p>Mantén el objeto centrado y enfocado contra un fondo sin movimiento.</p></div></div>
              </div>
            </div>
          </section>

          <footer className="footer-note">Diseñado para transformar buenas capturas en <span>modelos imprimibles</span>.</footer>
        </main>
      </div>
    </div>
  );
}

export default App;
