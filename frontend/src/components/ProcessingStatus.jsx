import React from 'react';
import { Clock, CheckCircle, XCircle, Loader, Layers } from 'lucide-react';

const ProcessingStatus = ({ status, onReconstruct, reconstructing }) => {
  if (!status) return null;

  const getStatusIcon = () => {
    switch (status.status) {
      case 'queued':
        return <Clock className="text-yellow-500" size={24} />;
      case 'processing':
        return <Loader className="text-blue-500 animate-spin" size={24} />;
      case 'completed':
        return <CheckCircle className="text-green-500" size={24} />;
      case 'failed':
        return <XCircle className="text-red-500" size={24} />;
      default:
        return null;
    }
  };

  const getStatusBadge = () => {
    const badges = {
      queued: 'status-pending',
      processing: 'status-processing',
      completed: 'status-completed',
      failed: 'status-failed'
    };
    return badges[status.status] || 'status-pending';
  };

  const canReconstruct = status.status === 'completed' && 
                        status.stage === 'ready_for_reconstruction';

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h2><Layers className="inline mr-2" /> Estado del Procesamiento</h2>
        <div className="flex items-center">
          {getStatusIcon()}
          <span className={`status-badge ${getStatusBadge()}`}>
            {status.status.toUpperCase()}
          </span>
        </div>
      </div>

      {status.message && (
        <div className="mb-4">
          <p className="text-gray-700">{status.message}</p>
        </div>
      )}

      {status.progress !== undefined && status.status === 'processing' && (
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${status.progress}%` }}
          >
            {status.progress}%
          </div>
        </div>
      )}

      {status.stage && (
        <div className="mb-4">
          <p className="text-sm text-gray-600">
            <strong>Fase actual:</strong> {status.stage.replace(/_/g, ' ')}
          </p>
        </div>
      )}

      {status.quality_analysis && (
        <div className="mb-4 p-4 bg-gray-50 rounded-lg">
          <h3 className="font-semibold mb-2">Análisis de Calidad del Video</h3>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="info-item">
              <span className="info-label">Resolución:</span>
              <span className="info-value">{status.quality_analysis.resolution}</span>
            </div>
            <div className="info-item">
              <span className="info-label">FPS:</span>
              <span className="info-value">{status.quality_analysis.fps?.toFixed(1)}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Duración:</span>
              <span className="info-value">{status.quality_analysis.duration?.toFixed(1)}s</span>
            </div>
            <div className="info-item">
              <span className="info-label">Calidad:</span>
              <span className="info-value">{status.quality_analysis.quality_score?.toFixed(0)}/100</span>
            </div>
          </div>
        </div>
      )}

      {status.frame_extraction && (
        <div className="mb-4 p-4 bg-gray-50 rounded-lg">
          <h3 className="font-semibold mb-2">Extracción de Frames</h3>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="info-item">
              <span className="info-label">Frames totales:</span>
              <span className="info-value">{status.frame_extraction.total_frames}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Frames extraídos:</span>
              <span className="info-value">{status.frame_extraction.extracted_frames}</span>
            </div>
          </div>
        </div>
      )}

      {canReconstruct && (
        <button
          onClick={onReconstruct}
          className="btn w-full"
          disabled={reconstructing}
        >
          {reconstructing ? 'Reconstruyendo...' : 'Iniciar Reconstrucción 3D'}
        </button>
      )}

      {status.error && (
        <div className="error-message mt-4">
          <strong>Error:</strong> {status.error}
        </div>
      )}
    </div>
  );
};

export default ProcessingStatus;
