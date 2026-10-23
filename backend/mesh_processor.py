"""
Módulo para procesamiento y reparación de mallas 3D para impresión 3D.
Usa Open3D y Trimesh para operaciones de geometría.
"""

import open3d as o3d
import trimesh
import numpy as np
from pathlib import Path
from typing import Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MeshProcessor:
    """Clase principal para procesamiento de mallas 3D."""
    
    def __init__(self, mesh_path: str):
        self.mesh_path = Path(mesh_path)
        self.mesh = None
        self.original_mesh = None
        
    def load_mesh(self) -> bool:
        """Carga la malla desde archivo."""
        try:
            # Intentar cargar con trimesh primero (más robusto)
            self.mesh = trimesh.load(str(self.mesh_path))
            
            # Si es escena con múltiples mallas, combinarlas
            if isinstance(self.mesh, trimesh.Scene):
                geometries = list(self.mesh.geometry.values())
                if len(geometries) == 1:
                    self.mesh = geometries[0]
                else:
                    # Combinar mallas
                    self.mesh = trimesh.util.concatenate(geometries)
            
            # Guardar copia original
            self.original_mesh = self.mesh.copy()
            logger.info(f"Malla cargada exitosamente: {self.mesh_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error cargando malla: {e}")
            return False
    
    def analyze_mesh(self) -> dict:
        """Analiza la calidad de la malla."""
        if self.mesh is None:
            return {"error": "Malla no cargada"}
        
        analysis = {
            "vertices": len(self.mesh.vertices),
            "faces": len(self.mesh.faces),
            "is_watertight": self.mesh.is_watertight,
            "is_winding_consistent": self.mesh.is_winding_consistent,
            "euler_number": self.mesh.euler_number,
            "volume": self.mesh.volume,
            "surface_area": self.mesh.area,
            "bounds": self.mesh.bounds.tolist(),
            "extent": self.mesh.extents.tolist()
        }
        
        # Detectar problemas
        issues = []
        if not self.mesh.is_watertight:
            issues.append("non_watertight")
        if not self.mesh.is_winding_consistent:
            issues.append("winding_inconsistency")
        if self.mesh.euler_number != 2:
            issues.append("topology_issues")
        
        analysis["issues"] = issues
        analysis["has_issues"] = len(issues) > 0
        
        return analysis
    
    def fix_non_manifold(self) -> bool:
        """Repara geometría non-manifold."""
        try:
            logger.info("Reparando geometría non-manifold...")
            
            # Usar trimesh para reparar
            self.mesh.fix_normals()
            self.mesh.fill_holes()
            
            # Convertir a Open3D para operaciones avanzadas
            o3d_mesh = o3d.geometry.TriangleMesh()
            o3d_mesh.vertices = o3d.utility.Vector3dVector(self.mesh.vertices)
            o3d_mesh.triangles = o3d.utility.Vector3iVector(self.mesh.faces)
            
            # Eliminar vértices duplicados
            o3d_mesh.remove_duplicated_vertices()
            o3d_mesh.remove_duplicated_triangles()
            o3d_mesh.remove_degenerate_triangles()
            o3d_mesh.remove_unreferenced_vertices()
            
            # Convertir de vuelta a trimesh
            self.mesh.vertices = np.asarray(o3d_mesh.vertices)
            self.mesh.faces = np.asarray(o3d_mesh.triangles)
            
            logger.info("Geometría non-manifold reparada")
            return True
            
        except Exception as e:
            logger.error(f"Error reparando non-manifold: {e}")
            return False
    
    def make_watertight(self) -> bool:
        """Cierra huecos en la malla para hacerla watertight."""
        try:
            logger.info("Cerrando huecos para hacer malla watertight...")
            
            # Usar trimesh para cerrar huecos
            self.mesh.fill_holes()
            
            # Verificar si es watertight después de cerrar huecos
            if not self.mesh.is_watertight:
                logger.warning("La malla aún no es completamente watertight")
                return False
            
            logger.info("Malla ahora es watertight")
            return True
            
        except Exception as e:
            logger.error(f"Error haciendo watertight: {e}")
            return False
    
    def remesh(self, target_faces: Optional[int] = None) -> bool:
        """Remuestrea la malla para optimizarla."""
        try:
            logger.info(f"Remuestreando malla (objetivo: {target_faces} faces)...")
            
            if target_faces is None:
                target_faces = min(50000, len(self.mesh.faces))
            
            # Simplificar malla
            self.mesh = self.mesh.simplify_quadratic_decimation(target_faces)
            
            logger.info(f"Malla remuestreada: {len(self.mesh.faces)} faces")
            return True
            
        except Exception as e:
            logger.error(f"Error remuestreando: {e}")
            return False
    
    def scale_mesh(self, scale_factor: float = 1.0, target_size: Optional[float] = None) -> bool:
        """Escala la malla."""
        try:
            if target_size is not None:
                # Escalar a tamaño específico (mm)
                current_size = max(self.mesh.extents)
                scale_factor = target_size / current_size
            
            self.mesh.apply_scale(scale_factor)
            logger.info(f"Malla escalada por factor: {scale_factor}")
            return True
            
        except Exception as e:
            logger.error(f"Error escalando malla: {e}")
            return False
    
    def validate_for_printing(self, min_thickness: float = 1.0) -> dict:
        """Valida si la malla es adecuada para impresión 3D."""
        validation = {
            "is_printable": True,
            "warnings": [],
            "errors": []
        }
        
        # Verificar watertight
        if not self.mesh.is_watertight:
            validation["is_printable"] = False
            validation["errors"].append("La malla no es watertight (tiene huecos)")
        
        # Verificar winding consistency
        if not self.mesh.is_winding_consistent:
            validation["is_printable"] = False
            validation["errors"].append("Inconsistencia en la orientación de caras")
        
        # Verificar tamaño (en mm, asumiendo que la unidad es mm)
        extents = self.mesh.extents
        if max(extents) > 300:  # 300mm es tamaño típico de impresoras
            validation["warnings"].append(f"El modelo es muy grande: {max(extents):.1f}mm")
        
        if min(extents) < min_thickness:
            validation["warnings"].append(f"El modelo tiene secciones muy delgadas: {min(extents):.2f}mm")
        
        # Verificar número de caras (para rendimiento)
        if len(self.mesh.faces) > 100000:
            validation["warnings"].append(f"El modelo tiene muchas caras: {len(self.mesh.faces)}")
        
        return validation
    
    def export_mesh(self, output_path: str, file_format: str = "stl") -> bool:
        """Exporta la malla procesada."""
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if file_format.lower() == "stl":
                self.mesh.export(str(output_path), file_type="stl")
            elif file_format.lower() == "obj":
                self.mesh.export(str(output_path), file_type="obj")
            elif file_format.lower() == "3mf":
                # Trimesh no soporta 3MF nativamente, usar Open3D
                o3d_mesh = o3d.geometry.TriangleMesh()
                o3d_mesh.vertices = o3d.utility.Vector3dVector(self.mesh.vertices)
                o3d_mesh.triangles = o3d.utility.Vector3iVector(self.mesh.faces)
                o3d.io.write_triangle_mesh(str(output_path), o3d_mesh)
            else:
                raise ValueError(f"Formato no soportado: {file_format}")
            
            logger.info(f"Malla exportada exitosamente: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exportando malla: {e}")
            return False
    
    def process_pipeline(self, config: dict) -> dict:
        """Ejecuta el pipeline completo de procesamiento."""
        results = {
            "success": False,
            "steps_completed": [],
            "steps_failed": [],
            "final_analysis": None
        }
        
        # Cargar malla
        if not self.load_mesh():
            results["steps_failed"].append("load_mesh")
            return results
        results["steps_completed"].append("load_mesh")
        
        # Análisis inicial
        initial_analysis = self.analyze_mesh()
        results["initial_analysis"] = initial_analysis
        
        # Reparar non-manifold si es necesario
        if initial_analysis.get("has_issues"):
            if self.fix_non_manifold():
                results["steps_completed"].append("fix_non_manifold")
            else:
                results["steps_failed"].append("fix_non_manifold")
        
        # Hacer watertight
        if config.get("make_watertight", True):
            if self.make_watertight():
                results["steps_completed"].append("make_watertight")
            else:
                results["steps_failed"].append("make_watertight")
        
        # Remuestrear
        if config.get("remesh", False):
            target_faces = config.get("target_faces", 50000)
            if self.remesh(target_faces):
                results["steps_completed"].append("remesh")
            else:
                results["steps_failed"].append("remesh")
        
        # Escalar
        if config.get("scale", 1.0) != 1.0:
            if self.scale_mesh(scale_factor=config["scale"]):
                results["steps_completed"].append("scale")
            else:
                results["steps_failed"].append("scale")
        
        # Análisis final
        final_analysis = self.analyze_mesh()
        results["final_analysis"] = final_analysis
        
        # Validar para impresión
        validation = self.validate_for_printing(
            min_thickness=config.get("min_thickness", 1.0)
        )
        results["validation"] = validation
        
        # Exportar
        if config.get("export", True):
            output_path = config.get("output_path", f"processed_{self.mesh_path.name}")
            file_format = config.get("export_format", "stl")
            if self.export_mesh(output_path, file_format):
                results["steps_completed"].append("export")
                results["output_path"] = output_path
            else:
                results["steps_failed"].append("export")
        
        results["success"] = len(results["steps_failed"]) == 0
        return results


# Función de conveniencia para procesamiento rápido
def process_mesh_for_printing(
    input_path: str,
    output_path: str,
    config: Optional[dict] = None
) -> dict:
    """
    Procesa una malla para impresión 3D con configuración por defecto.
    
    Args:
        input_path: Ruta del archivo de entrada
        output_path: Ruta del archivo de salida
        config: Configuración de procesamiento (opcional)
    
    Returns:
        Diccionario con resultados del procesamiento
    """
    if config is None:
        config = {
            "make_watertight": True,
            "remesh": True,
            "target_faces": 50000,
            "scale": 1.0,
            "min_thickness": 1.0,
            "export": True,
            "export_format": "stl"
        }
    
    config["output_path"] = output_path
    
    processor = MeshProcessor(input_path)
    return processor.process_pipeline(config)


if __name__ == "__main__":
    # Ejemplo de uso
    example_config = {
        "make_watertight": True,
        "remesh": True,
        "target_faces": 30000,
        "scale": 1.0,
        "min_thickness": 1.5,
        "export": True,
        "export_format": "stl"
    }
    
    # Descomentar para probar con un archivo real
    # results = process_mesh_for_printing("input.stl", "output.stl", example_config)
    # print(results)
