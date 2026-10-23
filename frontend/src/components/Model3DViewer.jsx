import React, { Suspense, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Grid, Environment } from '@react-three/drei';
import { Box, Loader } from 'lucide-react';

const Model3DViewer = ({ modelUrl, onDownload, downloading }) => {
  const [error, setError] = useState(null);

  const handleDownload = () => {
    if (onDownload) {
      onDownload();
    }
  };

  // Placeholder cuando no hay modelo cargado
  const Placeholder = () => (
    <mesh position={[0, 0, 0]}>
      <boxGeometry args={[2, 2, 2]} />
      <meshStandardMaterial color="#667eea" wireframe />
    </mesh>
  );

  // Componente para cargar modelo STL
  const STLModel = () => {
    // En una implementación real, aquí cargaríamos el archivo STL
    // Por ahora usamos un placeholder
    return <Placeholder />;
  };

  return (
    <div className="card">
      <div className="flex justify-between items-center mb-4">
        <h2><Box className="inline mr-2" /> Visor 3D</h2>
        {modelUrl && (
          <button
            onClick={handleDownload}
            className="btn btn-success"
            disabled={downloading}
          >
            {downloading ? 'Descargando...' : 'Descargar STL'}
          </button>
        )}
      </div>

      <div className="viewer-container">
        {error ? (
          <div className="error-message text-center" style={{ marginTop: '200px' }}>
            {error}
          </div>
        ) : (
          <Canvas
            camera={{ position: [5, 5, 5], fov: 50 }}
            style={{ width: '100%', height: '100%' }}
          >
            <Suspense fallback={null}>
              <ambientLight intensity={0.5} />
              <spotLight position={[10, 10, 10]} angle={0.15} penumbra={1} />
              <pointLight position={[-10, -10, -10]} />
              
              <STLModel />
              
              <Grid
                args={[20, 20]}
                cellSize={1}
                cellThickness={0.5}
                cellColor="#6b7280"
                sectionSize={5}
                sectionThickness={1}
                sectionColor="#9ca3af"
                fadeDistance={30}
                fadeStrength={1}
                followCamera={false}
                infiniteGrid={true}
              />
              
              <OrbitControls
                enablePan={true}
                enableZoom={true}
                enableRotate={true}
                minDistance={2}
                maxDistance={20}
              />
              
              <Environment preset="studio" />
            </Suspense>
          </Canvas>
        )}
      </div>

      {!modelUrl && (
        <div className="text-center mt-4 text-gray-500">
          <Loader className="mx-auto mb-2" size={32} />
          <p>Sube un video y espera a que se genere el modelo 3D</p>
        </div>
      )}
    </div>
  );
};

export default Model3DViewer;
