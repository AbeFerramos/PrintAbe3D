import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, Film, X } from 'lucide-react';

const VideoUploader = ({ onUpload, uploading }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [frameInterval, setFrameInterval] = useState(30);

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      setSelectedFile(acceptedFiles[0]);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'video/*': ['.mp4', '.avi', '.mov', '.mkv']
    },
    maxFiles: 1,
    disabled: uploading
  });

  const handleUpload = async () => {
    if (selectedFile && onUpload) {
      await onUpload(selectedFile, frameInterval);
    }
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
  };

  return (
    <div className="card">
      <h2><Film className="inline mr-2" /> Subir Video 360°</h2>
      
      {!selectedFile ? (
        <div
          {...getRootProps()}
          className={`dropzone ${isDragActive ? 'active' : ''}`}
        >
          <input {...getInputProps()} />
          <Upload size={48} className="mx-auto mb-4 text-gray-400" />
          <p className="text-lg mb-2">
            {isDragActive ? 'Suelta el video aquí' : 'Arrastra y suelta un video aquí'}
          </p>
          <p className="text-sm text-gray-500">
            O haz clic para seleccionar (MP4, AVI, MOV, MKV)
          </p>
        </div>
      ) : (
        <div className="selected-file">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <Film className="mr-3 text-purple-600" size={24} />
              <div>
                <p className="font-semibold">{selectedFile.name}</p>
                <p className="text-sm text-gray-500">
                  {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                </p>
              </div>
            </div>
            <button
              onClick={handleRemoveFile}
              className="text-red-500 hover:text-red-700"
              disabled={uploading}
            >
              <X size={20} />
            </button>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">
              Intervalo de extracción de frames: {frameInterval}
            </label>
            <input
              type="range"
              min="10"
              max="60"
              value={frameInterval}
              onChange={(e) => setFrameInterval(parseInt(e.target.value))}
              className="w-full"
              disabled={uploading}
            />
            <p className="text-xs text-gray-500 mt-1">
              Menor intervalo = más frames = mejor calidad pero más tiempo
            </p>
          </div>

          <button
            onClick={handleUpload}
            className="btn w-full"
            disabled={uploading}
          >
            {uploading ? 'Procesando...' : 'Iniciar Procesamiento'}
          </button>
        </div>
      )}
    </div>
  );
};

export default VideoUploader;
