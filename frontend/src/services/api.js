import axios from 'axios';

export const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Subir video
export const uploadVideo = async (file, frameInterval = 30) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('frame_interval', frameInterval);

  const response = await api.post('/api/v1/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

// Subir imágenes
export const uploadImages = async (files) => {
  const formData = new FormData();
  files.forEach(file => {
    formData.append('images', file);
  });

  const response = await api.post('/api/v1/upload-images', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

// Obtener estado del job
export const getJobStatus = async (jobId) => {
  const response = await api.get(`/api/v1/status/${jobId}`);
  return response.data;
};

// Obtener información de frames
export const getFramesInfo = async (jobId) => {
  const response = await api.get(`/api/v1/frames/${jobId}`);
  return response.data;
};

// Iniciar reconstrucción 3D
export const reconstruct3D = async (jobId, method = 'api_external') => {
  const response = await api.post(`/api/v1/reconstruct/${jobId}`, null, {
    params: { method }
  });
  return response.data;
};

// Descargar modelo 3D
export const downloadModel = async (jobId, format = 'stl') => {
  const response = await api.get(`/api/v1/download/${jobId}`, {
    params: { format },
    responseType: 'blob'
  });

  // Crear URL para descarga
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `model_3d_${jobId}.${format}`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);

  return response.data;
};

// Limpiar job
export const cleanupJob = async (jobId) => {
  const response = await api.delete(`/api/v1/cleanup/${jobId}`);
  return response.data;
};

export const getModelUrl = (jobId) => `${API_BASE_URL}/api/v1/download/${jobId}?format=stl`;

// Polling de estado (para actualización continua)
export const pollJobStatus = async (jobId, callback, interval = 2000) => {
  let cancelled = false;
  let timer;
  const poll = async () => {
    if (cancelled) return;
    try {
      const status = await getJobStatus(jobId);
      if (cancelled) return;
      callback(status);

      if (status.status === 'processing' || status.status === 'queued') {
        timer = setTimeout(poll, interval);
      }
    } catch (error) {
      if (!cancelled) callback({ status: 'error', error: error.response?.data?.detail || error.message });
    }
  };

  poll();
  return () => {
    cancelled = true;
    clearTimeout(timer);
  };
};

export default api;
