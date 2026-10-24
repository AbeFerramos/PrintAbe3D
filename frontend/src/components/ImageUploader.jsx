import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Image as ImageIcon, Lightbulb, Plus, Upload, X } from 'lucide-react';

const ImageUploader = ({ onUpload, uploading }) => {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const previews = useMemo(() => selectedFiles.map((file) => URL.createObjectURL(file)), [selectedFiles]);

  useEffect(() => () => previews.forEach((url) => URL.revokeObjectURL(url)), [previews]);

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) setSelectedFiles((current) => [...current, ...acceptedFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.jpg', '.jpeg', '.png', '.webp'] },
    multiple: true,
    disabled: uploading
  });

  const handleUpload = async () => {
    if (selectedFiles.length > 0 && onUpload) {
      const uploaded = await onUpload(selectedFiles);
      if (uploaded !== false) setSelectedFiles([]);
    }
  };

  return (
    <div className="uploader-card">
      <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}>
        <input {...getInputProps()} />
        <div className="upload-icon"><Plus size={22} /></div>
        <p className="dropzone-title">{isDragActive ? 'Suelta las imágenes para añadirlas' : 'Arrastra tus imágenes aquí'}</p>
        <p className="dropzone-subtitle">o haz clic para seleccionar varias imágenes</p>
        <span className="dropzone-hint">JPG · PNG · WEBP</span>
      </div>

      {selectedFiles.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <div className="image-tools">
            <strong>{selectedFiles.length} {selectedFiles.length === 1 ? 'imagen seleccionada' : 'imágenes seleccionadas'}</strong>
            <button type="button" onClick={() => setSelectedFiles([])} className="text-button" disabled={uploading}>Limpiar todo</button>
          </div>
          <div className="preview-grid">
            {selectedFiles.map((file, index) => (
              <div key={`${file.name}-${file.lastModified}-${index}`} className="preview-tile">
                <img src={previews[index]} alt={`Vista previa ${index + 1}`} />
                <button type="button" onClick={() => setSelectedFiles((current) => current.filter((_, fileIndex) => fileIndex !== index))} className="icon-button" aria-label={`Quitar ${file.name}`} disabled={uploading}><X size={13} /></button>
              </div>
            ))}
          </div>
          <button type="button" onClick={handleUpload} className="primary-button" disabled={uploading || selectedFiles.length < 2}>
            {uploading ? 'Subiendo imágenes…' : <><Upload size={15} /> Subir {selectedFiles.length} {selectedFiles.length === 1 ? 'imagen' : 'imágenes'}</>}
          </button>
          {selectedFiles.length < 2 && <p className="field-hint">Añade al menos dos imágenes para continuar.</p>}
          <p className="image-helper"><Lightbulb size={14} /> Para una buena reconstrucción, captura el objeto desde varios ángulos con buena luz y bastante solapamiento.</p>
        </div>
      )}
    </div>
  );
};

export default ImageUploader;
