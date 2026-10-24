import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Film, Upload, X } from 'lucide-react';

const VideoUploader = ({ onUpload, uploading }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [frameInterval, setFrameInterval] = useState(30);

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) setSelectedFile(acceptedFiles[0]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'video/*': ['.mp4', '.avi', '.mov', '.mkv'] },
    maxFiles: 1,
    disabled: uploading
  });

  const handleUpload = async () => {
    if (selectedFile && onUpload) await onUpload(selectedFile, frameInterval);
  };

  return (
    <div className="uploader-card">
      {!selectedFile ? (
        <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}>
          <input {...getInputProps()} />
          <div className="upload-icon"><Upload size={22} /></div>
          <p className="dropzone-title">{isDragActive ? 'Suelta el vídeo para añadirlo' : 'Arrastra aquí tu vídeo 360°'}</p>
          <p className="dropzone-subtitle">o haz clic para buscarlo en tu equipo</p>
          <span className="dropzone-hint">MP4 · AVI · MOV · MKV</span>
        </div>
      ) : (
        <div className="selected-file">
          <div className="file-row">
            <div className="file-kind"><Film size={18} /></div>
            <div className="file-info">
              <strong title={selectedFile.name}>{selectedFile.name}</strong>
              <span>{(selectedFile.size / (1024 * 1024)).toFixed(2)} MB · Vídeo seleccionado</span>
            </div>
            <button type="button" onClick={() => setSelectedFile(null)} className="icon-button" aria-label="Quitar vídeo" disabled={uploading}><X size={15} /></button>
          </div>

          <label className="field-label" htmlFor="frame-interval">
            <span>Frecuencia de fotogramas</span><output>{frameInterval} frames</output>
          </label>
          <input id="frame-interval" type="range" min="10" max="60" value={frameInterval} onChange={(event) => setFrameInterval(Number(event.target.value))} disabled={uploading} />
          <p className="field-hint">Un valor menor extrae más imágenes y puede mejorar el detalle, con un tiempo de proceso mayor.</p>

          <button type="button" onClick={handleUpload} className="primary-button" disabled={uploading}>
            {uploading ? 'Preparando fotogramas…' : <><Upload size={15} /> Extraer fotogramas</>}
          </button>
        </div>
      )}
    </div>
  );
};

export default VideoUploader;
