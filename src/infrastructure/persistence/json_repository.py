"""
Repository JSON pour sauvegarder les highlights extraits individuellement
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

from src.domain.entities.highlight import Highlight
from src.domain.entities.extraction_task import ExtractionTask


class JsonHighlightRepository:
    """Sauvegarde les highlights en JSON et TXT avec fiches individuelles."""
    
    def __init__(self, output_dir: str = "extractions"):
        """
        Initialise le repository.
        
        Args:
            output_dir: Dossier de sortie pour les fichiers
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    async def save_task(self, task: ExtractionTask) -> None:
        """
        Sauvegarde les résultats d'une tâche d'extraction avec fiches individuelles.
        
        Args:
            task: La tâche avec ses highlights individuels
        """
        if not task.highlights_extracted:
            return
        
        # Nom de fichier avec timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"extraction_{timestamp}"
        
        # Sauvegarder en JSON avec structure individuelle
        await self._save_json_individual(task, base_name)
        
        # Sauvegarder en TXT avec fiches séparées
        await self._save_txt_individual(task, base_name)
        
        print(f"✓ Résultats sauvegardés:")
        print(f"  - JSON: {self.output_dir}/{base_name}.json")
        print(f"  - TXT: {self.output_dir}/{base_name}.txt")
        print(f"  - {len(task.highlights_extracted)} surlignements individuels")
    
    async def _save_json_individual(self, task: ExtractionTask, base_name: str) -> None:
        """Sauvegarde au format JSON avec structure individuelle."""
        json_file = self.output_dir / f"{base_name}.json"
        
        # Groupement des highlights par page pour les statistiques
        highlights_by_page = self._group_highlights_by_page(task.highlights_extracted)
        
        # Calcul des statistiques
        stats = self._calculate_statistics(task.highlights_extracted)
        
        data = {
            "metadata": {
                "task_id": str(task.id),
                "extraction_date": datetime.now().isoformat(),
                "session_id": task.highlights_extracted[0].session_id if task.highlights_extracted else None,
                "pages_scanned": task.pages_scanned,
                "pages_with_content": task.pages_with_content,
                "total_highlights": len(task.highlights_extracted),
                "extraction_method": "individual_highlights",
                "version": "3.0"
            },
            "statistics": stats,
            "highlights": [
                self._highlight_to_dict(highlight) for highlight in sorted(task.highlights_extracted)
            ],
            "pages": highlights_by_page
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    async def _save_txt_individual(self, task: ExtractionTask, base_name: str) -> None:
        """Sauvegarde au format TXT avec fiches individuelles séparées."""
        txt_file = self.output_dir / f"{base_name}.txt"
        
        # Groupement et tri des highlights
        highlights_by_page = {}
        for h in task.highlights_extracted:
            if h.page_number not in highlights_by_page:
                highlights_by_page[h.page_number] = []
            highlights_by_page[h.page_number].append(h)
        
        # Tri des highlights par numéro dans chaque page
        for page_highlights in highlights_by_page.values():
            page_highlights.sort(key=lambda h: getattr(h, 'highlight_number', 1))
        
        with open(txt_file, 'w', encoding='utf-8') as f:
            # En-tête global
            f.write(f"EXTRACTION KINDLE - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Pages scannées: {task.pages_scanned}\n")
            f.write(f"Pages avec contenu: {task.pages_with_content}\n")
            f.write(f"Highlights extraits: {len(task.highlights_extracted)}\n")
            f.write("=" * 80 + "\n\n")
            
            # Écriture page par page avec fiches individuelles
            for page in sorted(highlights_by_page.keys()):
                page_highlights = highlights_by_page[page]
                
                f.write(f"--- PAGE {page} ---\n\n")
                
                # Chaque surlignement devient une fiche séparée
                for highlight in page_highlights:
                    highlight_num = getattr(highlight, 'highlight_number', 1)
                    
                    f.write(f"=== SURLIGNEMENT #{highlight_num} ===\n")
                    f.write(f"{highlight.text}\n")
                    f.write(f"(Confiance: {highlight.confidence:.0f}%)\n")
                    
                    # Informations détaillées si disponibles
                    if hasattr(highlight, 'word_count'):
                        f.write(f"(Mots: {highlight.word_count})\n")
                    
                    if highlight.position:
                        x, y, w, h = highlight.position
                        f.write(f"(Position: x={x}, y={y}, taille={w}x{h})\n")
                    
                    if hasattr(highlight, 'unique_id'):
                        f.write(f"(ID: {highlight.unique_id})\n")
                    
                    f.write("\n" + "-" * 40 + "\n\n")
                
                # Séparateur entre pages
                f.write("\n")
    
    def _highlight_to_dict(self, highlight: Highlight) -> Dict[str, Any]:
        """Convertit un highlight en dictionnaire pour JSON."""
        # Utiliser la méthode to_dict si disponible (nouvelle entité)
        if hasattr(highlight, 'to_dict'):
            return highlight.to_dict()
        
        # Fallback pour l'ancienne entité
        return {
            "id": str(highlight.id),
            "page_number": highlight.page_number,
            "highlight_number": getattr(highlight, 'highlight_number', 1),
            "text": highlight.text,
            "confidence": round(highlight.confidence, 1),
            "extracted_at": highlight.extracted_at.isoformat(),
            "position": {
                "x": highlight.position[0],
                "y": highlight.position[1],
                "width": highlight.position[2],
                "height": highlight.position[3]
            } if highlight.position else None,
            "session_id": getattr(highlight, 'session_id', None),
            "metrics": {
                "word_count": len(highlight.text.split()),
                "character_count": len(highlight.text),
                "preview": highlight.text[:100] + "..." if len(highlight.text) > 100 else highlight.text
            }
        }
    
    def _group_highlights_by_page(self, highlights: List[Highlight]) -> Dict[str, Any]:
        """Groupe les highlights par page pour le JSON."""
        pages = {}
        
        for highlight in highlights:
            page_num = highlight.page_number
            if page_num not in pages:
                pages[page_num] = {
                    "page_number": page_num,
                    "highlight_count": 0,
                    "highlights": []
                }
            
            pages[page_num]["highlight_count"] += 1
            pages[page_num]["highlights"].append({
                "highlight_number": getattr(highlight, 'highlight_number', 1),
                "text": highlight.text,
                "confidence": highlight.confidence,
                "word_count": len(highlight.text.split()),
                "character_count": len(highlight.text),
                "preview": highlight.text[:50] + "..." if len(highlight.text) > 50 else highlight.text
            })
        
        # Tri des highlights par numéro dans chaque page
        for page_data in pages.values():
            page_data["highlights"].sort(key=lambda h: h["highlight_number"])
        
        return pages
    
    def _calculate_statistics(self, highlights: List[Highlight]) -> Dict[str, Any]:
        """Calcule les statistiques des highlights."""
        if not highlights:
            return {}
        
        confidences = [h.confidence for h in highlights]
        word_counts = [len(h.text.split()) for h in highlights]
        
        # Distribution par niveau de confiance
        high_conf = sum(1 for c in confidences if c >= 90)
        medium_conf = sum(1 for c in confidences if 70 <= c < 90)
        low_conf = sum(1 for c in confidences if c < 70)
        
        # Pages uniques
        pages = set(h.page_number for h in highlights)
        
        return {
            "confidence": {
                "average": round(sum(confidences) / len(confidences), 1),
                "min": min(confidences),
                "max": max(confidences),
                "distribution": {
                    "high": high_conf,
                    "medium": medium_conf,
                    "low": low_conf
                }
            },
            "text": {
                "total_words": sum(word_counts),
                "average_words_per_highlight": round(sum(word_counts) / len(word_counts), 1),
                "min_words": min(word_counts),
                "max_words": max(word_counts)
            },
            "pages": {
                "total_pages": len(pages),
                "highlights_per_page": round(len(highlights) / len(pages), 1)
            }
        }
    
    async def load_extraction(self, filename: str) -> Dict[str, Any]:
        """Charge une extraction depuis un fichier JSON."""
        json_file = self.output_dir / filename
        
        if not json_file.exists():
            raise FileNotFoundError(f"Fichier non trouvé: {json_file}")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def list_extractions(self) -> List[str]:
        """Liste les fichiers d'extraction disponibles."""
        json_files = list(self.output_dir.glob("extraction_*.json"))
        return [f.name for f in sorted(json_files, reverse=True)]