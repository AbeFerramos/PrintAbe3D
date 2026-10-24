import React from 'react';
import { CheckCircle2, Clock3, Layers, Loader, XCircle } from 'lucide-react';

const ProcessingStatus = ({ status, onReconstruct, reconstructing }) => {
  if (!status) return null;

  const badgeClass = {
    queued: 'status-queued',
    processing: 'status-processing',
    completed: 'status-completed',
    failed: 'status-failed',
    error: 'status-failed'
  }[status.status] || 'status-queued';

  const statusLabel = {
    queued: 'En cola',
    processing: 'En proceso',
    completed: status.stage === 'ready_for_reconstruction' ? 'Captura lista' : 'Completado',
    failed: 'Error',
    error: 'Error'
  }[status.status] || 'Preparando';

  const canReconstruct = (status.status === 'completed' && status.stage === 'ready_for_reconstruction') ||
    ((status.status === 'failed' || status.status === 'error') && status.stage === 'reconstruction_error');

  const stageLabel = status.stage?.replace(/_/g, ' ');
  const quality = status.quality_analysis;
  const extraction = status.frame_extraction;
  const details = [
    quality?.resolution && ['Resolución', quality.resolution],
    quality?.fps != null && ['Fotogramas por segundo', `${quality.fps.toFixed(1)} FPS`],
    quality?.duration != null && ['Duración', `${quality.duration.toFixed(1)} s`],
    quality?.quality_score != null && ['Calidad de captura', `${quality.quality_score.toFixed(0)}/100`],
    extraction?.total_frames != null && ['Fotogramas del vídeo', extraction.total_frames],
    extraction?.extracted_frames != null && ['Fotogramas extraídos', extraction.extracted_frames],
    status.total_images != null && ['Imágenes listas', status.total_images]
  ].filter(Boolean);

  return (
    <section className="panel status-card" aria-live="polite">
      <div className="panel-body">
        <div className="status-top">
          <div className="status-title"><div className="panel-icon"><Layers size={17} /></div><h2>Estado del proceso</h2></div>
          <span className={`status-chip ${badgeClass}`}>
            {status.status === 'processing' ? <Loader className="spinner" size={13} /> : status.status === 'completed' ? <CheckCircle2 size={13} /> : status.status === 'failed' || status.status === 'error' ? <XCircle size={13} /> : <Clock3 size={13} />}
            {statusLabel}
          </span>
        </div>

        {status.message && <p className="status-message">{status.message}</p>}

        {status.status === 'processing' && status.progress !== undefined && (
          <div className="progress-track" role="progressbar" aria-valuenow={status.progress} aria-valuemin="0" aria-valuemax="100">
            <span style={{ width: `${Math.max(0, Math.min(100, status.progress))}%` }} />
          </div>
        )}

        {stageLabel && <p className="status-stage">Etapa actual · <strong>{stageLabel}</strong></p>}

        {details.length > 0 && (
          <div className="status-details">
            {details.map(([label, value]) => <div className="status-detail" key={label}><span>{label}</span><strong>{value}</strong></div>)}
          </div>
        )}

        {canReconstruct && (
          <div className="status-action">
            <button onClick={onReconstruct} className="primary-button" disabled={reconstructing}>
              {reconstructing ? <><Loader className="spinner" size={15} /> Preparando reconstrucción…</> : <><Layers size={15} /> {status.stage === 'reconstruction_error' ? 'Reintentar reconstrucción' : 'Iniciar reconstrucción 3D'}</>}
            </button>
          </div>
        )}

        {status.error && <div className="error-message" style={{ marginTop: 14 }}><XCircle size={16} /><span><strong>Detalle:</strong> {status.error}</span></div>}
      </div>
    </section>
  );
};

export default ProcessingStatus;
