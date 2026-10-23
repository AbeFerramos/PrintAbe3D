import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, Image as ImageIcon, X, Plus } from 'lucide-react';

const ImageUploader = ({ onUpload, uploading }) => {
  const [selectedFiles, setSelectedFiles] = useState([]);

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      setSelectedFiles(prev => [...prev, ...acceptedFiles]);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpg', '.jpeg', '.png', '.webp']
    },
    multiple: true,
    disabled: uploading
  });

  const handleRemoveFile = (index) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (selectedFiles.length > 0 && onUpload) {
      await onUpload(selectedFiles);
    }
  };

  const handleClearAll = () => {
    setSelectedFiles([]);
  };

  return (
    <div className="card">
      <h2><ImageIcon className="inline mr-2" /> Subir Imágenes 360°</h2>
      
      <div
        {...getRootProps()}
        className={`dropzone ${isDragActive ? 'active' : ''}`}
        style={{ marginBottom: '20px' }}
      >
        <input {...getInputProps()} />
        <Upload size={48} className="mx-auto mb-4 text-gray-400" />
        <p className="text-lg mb-2">
          {isDragActive ? 'Suelta las imágenes aquí' : 'Arrastra y suelta imágenes aquí'}
        </p>
        <p className="text-sm text-gray-500">
          O haz clic para seleccionar (JPG, PNG, WebP)
        </p>
        <p className="text-xs text-gray-400 mt-2">
          Múltiples imágenes permitidas
        </p>
      </div>

      {selectedFiles.length > 0 && (
        <div className="selected-files">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-semibold">
              {selectedFiles.length} {selectedFiles.length === 1 ? 'imagen' : 'imágenes'} seleccionada{selectedFiles.length > 1 ? 's' : ''}
            </h3>
            <button
              onClick={handleClearAll}
              className="text-red-500 hover:text-red-700 text-sm"
              disabled={uploading}
            >
              Limpiar todas
            </button>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
            {selectedFiles.map((file, index) => (
              <div key={index} className="relative group">
                <div className="aspect-square bg-gray-100 rounded-lg overflow-hidden flex items-center justify-center">
                  <img
                    src={URL.createObjectURL(file)}
                    alt={`Preview ${index + 1}`}
                    className="w-full h-full object-cover"
                  />
                </div>
                <button
                  onClick={() => handleRemoveFile(index)}
                  className="absolute top-2 right-2 bg-red-500 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                  disabled={uploading}
                >
                  <X size={16} />
                </button>
                <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-50 text-white text-xs p-1 truncate">
                  {file.name}
                </div>
              </div>
            ))}
          </div>

          <div className="flex gap-2">
            <button
              onClick={handleUpload}
              className="btn flex-1"
              disabled={uploading || selectedFiles.length === 0}
            >
              {uploading ? 'Procesando...' : 'Iniciar Reconstrucción 3D'}
            </button>
          </div>

          {selectedFiles.length > 0 && (
            <div className="mt-4 p-4 bg-blue-50 rounded-lg">
              <h4 className="font-semibold text-blue-800 mb-2">💡 Consejos para mejores resultados</h4>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• Mínimo 8-12 imágenes para buena reconstrucción</li>
                <li>• Captura desde diferentes ángulos (360° alrededor del objeto)</li>
                <li>• Usa iluminación uniforme y evita sombras duras</li>
                <li>• Mantén el objeto centrado en todas las fotos</li>
                <li>• Fondo neutro o transparente funciona mejor</li>
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ImageUploader;
