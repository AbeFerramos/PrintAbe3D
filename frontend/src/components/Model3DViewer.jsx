import React, { Suspense, useEffect, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Grid, Environment, Html } from '@react-three/drei';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js';
import { Box, Download, Loader, MousePointer2, Rotate3D } from 'lucide-react';
import * as THREE from 'three';

function STLModel({ url }) {
  const [geometry, setGeometry] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    let loadedGeometry;
    setGeometry(null);
    setError(null);
    new STLLoader().load(url, (source) => {
      if (!active) { source.dispose(); return; }
      source.computeVertexNormals();
      const bounds = new THREE.Box3().setFromBufferAttribute(source.attributes.position);
      const center = bounds.getCenter(new THREE.Vector3());
      const size = bounds.getSize(new THREE.Vector3());
      const maxDimension = Math.max(size.x, size.y, size.z);
      if (!Number.isFinite(maxDimension) || maxDimension === 0) {
        source.dispose();
        setError('El archivo STL no contiene una malla válida.');
        return;
      }
      source.translate(-center.x, -center.y, -center.z);
      source.scale(3 / maxDimension, 3 / maxDimension, 3 / maxDimension);
      loadedGeometry = source;
      setGeometry(source);
    }, undefined, () => active && setError('No se pudo cargar el modelo STL.'));

    return () => { active = false; loadedGeometry?.dispose(); };
  }, [url]);

  if (error) return <Html center><div className="error-message">{error}</div></Html>;
  if (!geometry) return null;
  return <mesh geometry={geometry}><meshStandardMaterial color="#b9db83" metalness={0.12} roughness={0.56} /></mesh>;
}

class ViewerErrorBoundary extends React.Component {
  state = { hasError: false };
  static getDerivedStateFromError() { return { hasError: true }; }
  componentDidUpdate(previousProps) {
    if (previousProps.resetKey !== this.props.resetKey && this.state.hasError) this.setState({ hasError: false });
  }
  render() {
    return this.state.hasError ? <div className="error-message">No se pudo mostrar el modelo 3D.</div> : this.props.children;
  }
}

const Model3DViewer = ({ modelUrl, onDownload, downloading }) => (
  <section className="panel viewer-panel">
    <div className="panel-heading">
      <div className="panel-title">
        <div className="panel-icon"><Box size={17} /></div>
        <div><h2>Vista previa 3D</h2><p>{modelUrl ? 'Malla lista para inspeccionar' : 'El resultado aparecerá en este espacio'}</p></div>
      </div>
      {modelUrl ? (
        <button onClick={onDownload} className="download-button" disabled={downloading}>
          {downloading ? <Loader className="spinner" size={14} /> : <Download size={14} />}
          {downloading ? 'Preparando…' : 'Exportar STL'}
        </button>
      ) : <span className="viewer-heading-right"><span className="viewer-live-dot" /> PREVISUALIZACIÓN</span>}
    </div>

    <div className="viewer-container">
      <ViewerErrorBoundary resetKey={modelUrl}>
        <Canvas camera={{ position: [5, 5, 5], fov: 50 }} style={{ width: '100%', height: '100%' }}>
          <Suspense fallback={null}>
            <ambientLight intensity={0.75} />
            <directionalLight position={[5, 8, 5]} intensity={1.35} />
            {modelUrl && <STLModel key={modelUrl} url={modelUrl} />}
            <Grid args={[20, 20]} cellSize={1} cellThickness={0.5} cellColor="#50645a" sectionSize={5} sectionThickness={1} sectionColor="#789079" fadeDistance={30} fadeStrength={1} followCamera={false} infiniteGrid />
            <OrbitControls makeDefault enablePan enableZoom enableRotate minDistance={2} maxDistance={20} />
            <Environment preset="studio" />
          </Suspense>
        </Canvas>
      </ViewerErrorBoundary>
      {!modelUrl && (
        <div className="viewer-placeholder">
          <div className="placeholder-cube"><Box size={34} strokeWidth={1.35} /></div>
          <strong>Tu modelo tomará forma aquí</strong>
          <span>Cuando la reconstrucción termine, podrás rotar la pieza y revisar su geometría.</span>
        </div>
      )}
    </div>

    <div className="viewer-footer">
      <span><Rotate3D size={13} /> Arrastra para rotar</span>
      <span><MousePointer2 size={12} /> Rueda para acercar</span>
    </div>
  </section>
);

export default Model3DViewer;
