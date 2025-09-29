"""
Gestionnaire du format propriétaire AllamBik (.allambik)
Gère la création, sauvegarde et chargement des projets d'extraction
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class ExtractionMetadata:
    """Métadonnées d'une session d'extraction."""
    version: str = "1.0"
    created_at: str = ""
    modified_at: str = ""
    extraction_session: str = ""
    total_pages_scanned: int = 0
    pages_with_content: int = 0
    app_version: str = "AllamBik v3.0"
    extraction_zone: Optional[Tuple[int, int, int, int]] = None
    original_total_highlights: int = 0
    current_total_highlights: int = 0
    deleted_count: int = 0
    modified_count: int = 0


@dataclass
class ModificationEntry:
    """Entrée dans l'historique des modifications."""
    timestamp: str
    action: str  # "edit", "delete", "add"
    details: Dict[str, Any]


class AllambikProject:
    """Gestionnaire principal du format propriétaire AllamBik."""
    
    def __init__(self, project_path: Optional[str] = None):
        self.project_path = project_path
        self.metadata = ExtractionMetadata()
        self.highlights = []
        self.modifications_log = []
        
        if project_path and os.path.exists(project_path):
            self.load_project()
    
    def create_new_project(self, extraction_zone: Optional[Tuple[int, int, int, int]] = None) -> str:
        """Crée un nouveau projet d'extraction."""
        timestamp = datetime.now()
        session_id = timestamp.strftime("session_%Y%m%d_%H%M%S")
        
        self.metadata = ExtractionMetadata(
            created_at=timestamp.isoformat(),
            modified_at=timestamp.isoformat(),
            extraction_session=session_id,
            extraction_zone=extraction_zone
        )
        
        # Générer le chemin du fichier
        extractions_dir = "extractions"
        if not os.path.exists(extractions_dir):
            os.makedirs(extractions_dir)
        
        filename = f"extraction_{timestamp.strftime('%Y%m%d_%H%M%S')}.allambik"
        self.project_path = os.path.join(extractions_dir, filename)
        
        # Sauvegarder le projet initial
        self.save_project()
        
        return self.project_path
    
    def add_highlight(self, highlight_data: Dict[str, Any]) -> bool:
        """Ajoute un highlight au projet."""
        try:
            # Ajouter timestamp si manquant
            if 'timestamp' not in highlight_data:
                highlight_data['timestamp'] = datetime.now().isoformat()
            
            # Ajouter ID unique si manquant
            if 'id' not in highlight_data:
                highlight_data['id'] = f"hl_{len(self.highlights)}_{int(datetime.now().timestamp())}"
            
            self.highlights.append(highlight_data)
            
            # Mettre à jour les métadonnées
            self.metadata.modified_at = datetime.now().isoformat()
            self.metadata.current_total_highlights = len(self.highlights)
            self.metadata.original_total_highlights = max(
                self.metadata.original_total_highlights, 
                len(self.highlights)
            )
            
            # Log de l'ajout
            self.modifications_log.append(ModificationEntry(
                timestamp=datetime.now().isoformat(),
                action="add",
                details={
                    "page": highlight_data.get('page'),
                    "highlight_id": highlight_data.get('id')
                }
            ))
            
            # Sauvegarde automatique
            self.save_project()
            
            return True
        except Exception as e:
            print(f"ERREUR: Impossible d'ajouter highlight: {e}")
            return False
    
    def update_highlight(self, highlight_id: str, updated_data: Dict[str, Any]) -> bool:
        """Met à jour un highlight existant."""
        try:
            for i, highlight in enumerate(self.highlights):
                if highlight.get('id') == highlight_id:
                    # Sauvegarder les anciennes valeurs pour le log
                    old_values = {}
                    for key, new_value in updated_data.items():
                        if key in highlight:
                            old_values[key] = highlight[key]
                    
                    # Appliquer les modifications
                    highlight.update(updated_data)
                    highlight['modified'] = True
                    highlight['modified_date'] = datetime.now().isoformat()
                    
                    # Mettre à jour les métadonnées
                    self.metadata.modified_at = datetime.now().isoformat()
                    self.metadata.modified_count += 1
                    
                    # Log de la modification
                    self.modifications_log.append(ModificationEntry(
                        timestamp=datetime.now().isoformat(),
                        action="edit",
                        details={
                            "highlight_id": highlight_id,
                            "page": highlight.get('page'),
                            "changes": updated_data,
                            "old_values": old_values
                        }
                    ))
                    
                    # Sauvegarde automatique
                    self.save_project()
                    
                    return True
            
            print(f"ERREUR: Highlight {highlight_id} non trouvé")
            return False
            
        except Exception as e:
            print(f"ERREUR: Impossible de mettre à jour highlight: {e}")
            return False
    
    def delete_highlights(self, highlight_ids: List[str]) -> int:
        """Supprime plusieurs highlights."""
        try:
            deleted_count = 0
            deleted_highlights = []
            
            # Identifier les highlights à supprimer
            for highlight_id in highlight_ids:
                for highlight in self.highlights:
                    if highlight.get('id') == highlight_id:
                        deleted_highlights.append(highlight.copy())
                        break
            
            # Supprimer les highlights
            self.highlights = [h for h in self.highlights if h.get('id') not in highlight_ids]
            deleted_count = len(deleted_highlights)
            
            if deleted_count > 0:
                # Mettre à jour les métadonnées
                self.metadata.modified_at = datetime.now().isoformat()
                self.metadata.current_total_highlights = len(self.highlights)
                self.metadata.deleted_count += deleted_count
                
                # Log de la suppression
                self.modifications_log.append(ModificationEntry(
                    timestamp=datetime.now().isoformat(),
                    action="delete",
                    details={
                        "count": deleted_count,
                        "deleted_highlights": deleted_highlights,
                        "highlight_ids": highlight_ids
                    }
                ))
                
                # Sauvegarde automatique
                self.save_project()
            
            return deleted_count
            
        except Exception as e:
            print(f"ERREUR: Impossible de supprimer highlights: {e}")
            return 0
    
    def update_extraction_stats(self, pages_scanned: int, pages_with_content: int):
        """Met à jour les statistiques d'extraction."""
        self.metadata.total_pages_scanned = pages_scanned
        self.metadata.pages_with_content = pages_with_content
        self.metadata.modified_at = datetime.now().isoformat()
    
    def save_project(self) -> bool:
        """Sauvegarde le projet au format .allambik."""
        if not self.project_path:
            print("ERREUR: Aucun chemin de projet défini")
            return False
        
        try:
            project_data = {
                "metadata": asdict(self.metadata),
                "highlights": self.highlights,
                "modifications_log": [asdict(entry) for entry in self.modifications_log]
            }
            
            with open(self.project_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"ERREUR: Impossible de sauvegarder projet: {e}")
            return False
    
    def load_project(self) -> bool:
        """Charge un projet depuis un fichier .allambik."""
        if not self.project_path or not os.path.exists(self.project_path):
            print(f"ERREUR: Fichier projet non trouvé: {self.project_path}")
            return False
        
        try:
            with open(self.project_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            # Charger les métadonnées
            metadata_dict = project_data.get('metadata', {})
            self.metadata = ExtractionMetadata(**metadata_dict)
            
            # Charger les highlights
            self.highlights = project_data.get('highlights', [])
            
            # Charger l'historique des modifications
            self.modifications_log = []
            for entry_data in project_data.get('modifications_log', []):
                self.modifications_log.append(ModificationEntry(**entry_data))
            
            return True
            
        except Exception as e:
            print(f"ERREUR: Impossible de charger projet: {e}")
            return False
    
    @staticmethod
    def import_from_json(json_path: str) -> 'AllambikProject':
        """Importe un JSON existant vers le format .allambik."""
        project = AllambikProject()
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Créer nouveau projet
            project.create_new_project()
            
            # Traiter les données JSON
            highlights = []
            if isinstance(data, list):
                highlights = data
            elif isinstance(data, dict):
                highlights = data.get('highlights', data.get('results', []))
            
            # Ajouter les highlights
            for i, h in enumerate(highlights):
                if isinstance(h, dict):
                    highlight_data = {
                        'id': f"imported_{i}_{int(datetime.now().timestamp())}",
                        'page': h.get('page', h.get('page_number', i // 3 + 1)),
                        'text': h.get('text', h.get('extracted_text', '')),
                        'confidence': h.get('confidence', h.get('confidence_score', 85)),
                        'timestamp': h.get('timestamp', "2024-01-01T00:00:00"),
                        'source_image': h.get('source_image', None),
                        'coordinates': h.get('coordinates', None),
                        'validated': h.get('validated', False),
                        'modified': h.get('modified', False),
                        'custom_name': h.get('custom_name', '')
                    }
                    project.highlights.append(highlight_data)
            
            # Mettre à jour les métadonnées
            project.metadata.original_total_highlights = len(project.highlights)
            project.metadata.current_total_highlights = len(project.highlights)
            
            # Log de l'import
            project.modifications_log.append(ModificationEntry(
                timestamp=datetime.now().isoformat(),
                action="import",
                details={
                    "source_file": os.path.basename(json_path),
                    "imported_count": len(project.highlights)
                }
            ))
            
            # Sauvegarder
            project.save_project()
            
            return project
            
        except Exception as e:
            print(f"ERREUR: Impossible d'importer JSON: {e}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques du projet."""
        return {
            "total_highlights": len(self.highlights),
            "original_count": self.metadata.original_total_highlights,
            "deleted_count": self.metadata.deleted_count,
            "modified_count": self.metadata.modified_count,
            "pages_scanned": self.metadata.total_pages_scanned,
            "pages_with_content": self.metadata.pages_with_content,
            "session_id": self.metadata.extraction_session,
            "created_at": self.metadata.created_at,
            "last_modified": self.metadata.modified_at
        }
    
    def export_to_json(self, output_path: str) -> bool:
        """Exporte les données actuelles vers un fichier JSON standard."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.highlights, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"ERREUR: Impossible d'exporter JSON: {e}")
            return False