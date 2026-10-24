"""
Integración con COLMAP API para fotogrametría gratuita y open source.
COLMAP es un pipeline de Structure-from-Motion y Multi-View Stereo de alta calidad.
"""

import requests
import os
import zipfile
import shutil
from pathlib import Path
from typing import Optional, List
import logging
from contextlib import ExitStack
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class COLMAPIntegration:
    """Cliente para integración con COLMAP API."""
    
    def __init__(self, colmap_api_url: str = "http://localhost:8001"):
        """
        Inicializa el cliente de COLMAP API.
        
        Args:
            colmap_api_url: URL del servidor COLMAP API (default: http://localhost:8001)
                           Nota: Usamos puerto 8001 para no conflictuar con nuestro backend en 8000
        """
        self.colmap_api_url = colmap_api_url.rstrip('/')
        self.health_endpoint = f"{self.colmap_api_url}/health"
        self.sfm_endpoint = f"{self.colmap_api_url}/sfm"
        
    def check_health(self) -> bool:
        """Verifica si el servidor COLMAP API está disponible."""
        try:
            # Intentar hacer una petición simple al endpoint principal
            # Como /health no existe en esta versión, probamos con /
            response = requests.get(f"{self.colmap_api_url}/", timeout=5)
            # Si responde (aunque sea 404), el servidor está disponible
            return True
        except Exception as e:
            print(f"Error checking COLMAP API health: {e}")
            return False
    
    def reconstruct_from_images(
        self,
        image_paths: List[str],
        output_dir: str,
        retrieval_conf: str = "netvlad",
        feature_conf: str = "superpoint_aachen",
        matcher_conf: str = "superpoint+lightglue"
    ) -> dict:
        """
        Realiza reconstrucción 3D desde imágenes usando COLMAP API.
        
        Args:
            image_paths: Lista de rutas a las imágenes
            output_dir: Directorio donde guardar los resultados
            retrieval_conf: Configuración de recuperación de imágenes
            feature_conf: Configuración de extracción de características
            matcher_conf: Configuración de matching de características
        
        Returns:
            Diccionario con resultados de la reconstrucción
        """
        if not self.check_health():
            raise ConnectionError("COLMAP API no está disponible")
        
        logger.info(f"Iniciando reconstrucción COLMAP con {len(image_paths)} imágenes")
        
        # Preparar archivos para subida
        valid_paths = [path for path in image_paths if os.path.isfile(path)]
        missing_paths = set(image_paths) - set(valid_paths)
        for image_path in missing_paths:
            logger.warning("Imagen no encontrada: %s", image_path)
        if len(valid_paths) < 2:
            raise ValueError("No se encontraron imágenes válidas para procesar")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        with ExitStack() as stack:
            files = [('images', (Path(path).name, stack.enter_context(open(path, 'rb')), 'application/octet-stream')) for path in valid_paths]
            # Llamar a COLMAP API
            data = {
                'retrieval_conf_key': retrieval_conf,
                'feature_conf_key': feature_conf,
                'matcher_conf_key': matcher_conf
            }
            
            logger.info("Enviando imágenes a COLMAP API...")
            response = requests.post(
                self.sfm_endpoint,
                files=files,
                data=data,
                timeout=(15, 1800)  # 30 minutos para reconstrucciones pesadas
            )
            if not response.ok:
                raise RuntimeError(f"COLMAP API respondió {response.status_code}: {response.text[:1000]}")
            
            # Guardar resultado ZIP
            zip_path = output_path / "colmap_result.zip"
            if not response.content.startswith(b"PK"):
                raise RuntimeError("COLMAP respondió con un formato inesperado; se esperaba un archivo ZIP")
            zip_path.write_bytes(response.content)
            
            logger.info(f"Reconstrucción completada. Resultado guardado en: {zip_path}")
            
            # Extraer ZIP
            extract_dir = output_path / "colmap_extracted"
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
            extract_dir.mkdir(parents=True)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                root = extract_dir.resolve()
                for member in zip_ref.infolist():
                    target = (extract_dir / member.filename).resolve()
                    if target != root and root not in target.parents:
                        raise ValueError("La respuesta ZIP de COLMAP contiene una ruta no válida")
                zip_ref.extractall(extract_dir)
            
            logger.info(f"Archivos extraídos en: {extract_dir}")
            
            # Buscar archivos de malla generados
            mesh_files = self._find_mesh_files(extract_dir)
            
            return {
                "success": True,
                "zip_path": str(zip_path),
                "extract_dir": str(extract_dir),
                "mesh_files": mesh_files,
                "num_images": len(valid_paths),
                "method": "colmap_photogrammetry"
            }
        
    def _find_mesh_files(self, directory: Path) -> dict:
        """Busca archivos de malla en el directorio extraído."""
        mesh_files = {
            "ply": None,
            "obj": None,
            "point_cloud": None,
            "all_files": []
        }
        
        # Buscar archivos comunes de COLMAP
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                mesh_files["all_files"].append(str(file_path))
                if file_path.suffix.lower() == ".ply":
                    mesh_files["ply"] = str(file_path)
                elif file_path.suffix.lower() == ".obj":
                    mesh_files["obj"] = str(file_path)
                elif "point" in file_path.name.lower() and file_path.suffix.lower() in [".ply", ".txt"]:
                    mesh_files["point_cloud"] = str(file_path)
        
        print(f"Archivos encontrados en COLMAP output: {len(mesh_files['all_files'])}")
        for f in mesh_files["all_files"][:10]:  # Mostrar primeros 10 archivos
            print(f"  - {f}")
        
        return mesh_files
    
    def convert_to_stl(self, input_mesh: str, output_stl: str) -> bool:
        """
        Convierte una malla COLMAP a formato STL para impresión 3D.
        
        Args:
            input_mesh: Ruta del archivo de malla de entrada (PLY/OBJ)
            output_stl: Ruta del archivo STL de salida
        
        Returns:
            True si la conversión fue exitosa
        """
        try:
            # Intentar usar Open3D primero
            try:
                import open3d as o3d
                
                # Leer malla
                if input_mesh.endswith('.ply'):
                    mesh = o3d.io.read_triangle_mesh(input_mesh)
                elif input_mesh.endswith('.obj'):
                    mesh = o3d.io.read_triangle_mesh(input_mesh)
                else:
                    raise ValueError(f"Formato no soportado: {input_mesh}")
                
                # COLMAP suele devolver nubes de puntos PLY. Crear una superficie
                # imprimible cuando el archivo todavía no contiene triángulos.
                if len(mesh.vertices) == 0 or len(mesh.triangles) == 0:
                    cloud = o3d.io.read_point_cloud(input_mesh)
                    if len(cloud.points) < 30:
                        logger.warning("COLMAP no devolvió suficientes puntos para crear una malla")
                        return False
                    distances = cloud.compute_nearest_neighbor_distance()
                    if len(distances) == 0:
                        return False
                    average_spacing = float(np.mean(distances))
                    cloud.estimate_normals(
                        search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=average_spacing * 4, max_nn=30)
                    )
                    cloud.orient_normals_consistent_tangent_plane(30)
                    mesh, _density = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
                        cloud, depth=9, width=0, scale=1.1, linear_fit=False
                    )
                    # Elimina fragmentos muy pequeños que suelen ser ruido de reconstrucción.
                    components, component_counts, _ = mesh.cluster_connected_triangles()
                    if len(component_counts):
                        largest = int(np.argmax(component_counts))
                        mesh.remove_triangles_by_mask(np.asarray(components) != largest)
                    mesh.remove_unreferenced_vertices()
                    mesh.remove_degenerate_triangles()
                    if len(mesh.triangles) == 0:
                        return False
                
                # El exportador STL requiere normales de caras y de vértices.
                mesh.compute_triangle_normals()
                mesh.compute_vertex_normals()
                
                # Guardar como STL
                if not o3d.io.write_triangle_mesh(output_stl, mesh, write_ascii=False):
                    return False
                
                logger.info(f"Malla convertida a STL con Open3D: {output_stl}")
                return True
                
            except ImportError:
                logger.warning("Open3D no está instalado, usando trimesh como alternativa")
                
                # Usar trimesh como alternativa
                import trimesh
                
                # Leer malla
                mesh = trimesh.load(input_mesh)
                
                # Verificar que la malla tiene geometría
                if len(mesh.vertices) == 0 or len(mesh.faces) == 0:
                    logger.warning("La malla no tiene geometría válida")
                    return False
                
                # Exportar como STL
                mesh.export(output_stl)
                
                logger.info(f"Malla convertida a STL con trimesh: {output_stl}")
                return True
                
        except Exception as e:
            logger.error(f"Error convirtiendo a STL: {e}")
            return False


# Función de conveniencia para usar en el pipeline principal
def reconstruct_with_colmap(
    image_paths: List[str],
    output_dir: str,
    colmap_api_url: str = "http://localhost:8001"
) -> dict:
    """
    Función de alto nivel para reconstrucción 3D con COLMAP.
    
    Args:
        image_paths: Lista de rutas a las imágenes
        output_dir: Directorio de salida
        colmap_api_url: URL del servidor COLMAP API
    
    Returns:
        Diccionario con resultados de la reconstrucción
    """
    colmap = COLMAPIntegration(colmap_api_url)
    
    # Realizar reconstrucción
    result = colmap.reconstruct_from_images(image_paths, output_dir)
    
    # Convertir a STL si se encontró malla
    if result["success"] and result["mesh_files"].get("ply"):
        ply_file = result["mesh_files"]["ply"]
        stl_file = Path(output_dir) / "reconstructed.stl"
        
        if colmap.convert_to_stl(ply_file, str(stl_file)):
            result["stl_file"] = str(stl_file)
            result["stl_conversion_success"] = True
        else:
            result["stl_conversion_success"] = False
    
    return result


if __name__ == "__main__":
    # Ejemplo de uso
    import sys
    
    # Verificar argumentos
    if len(sys.argv) < 3:
        print("Uso: python colmap_integration.py <imagen1> <imagen2> ... <directorio_salida>")
        sys.exit(1)
    
    # Obtener imágenes y directorio de salida
    image_paths = sys.argv[1:-1]
    output_dir = sys.argv[-1]
    
    print(f"Procesando {len(image_paths)} imágenes...")
    print(f"Directorio de salida: {output_dir}")
    
    # Realizar reconstrucción
    try:
        result = reconstruct_with_colmap(image_paths, output_dir)
        
        if result["success"]:
            print("✅ Reconstrucción completada exitosamente")
            print(f"📁 Directorio: {result['extract_dir']}")
            print(f"🎨 Archivos de malla: {result['mesh_files']}")
            if result.get("stl_file"):
                print(f"🖨️  STL para impresión: {result['stl_file']}")
        else:
            print("❌ La reconstrucción falló")
            
    except Exception as e:
        print(f"❌ Error: {e}")
