"""
JSON export functionality for pdfalyzer.
Serializes PDF analysis results to JSON format while preserving PDF structure.
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from anytree import LevelOrderIter, SymlinkNode
from pypdf.generic import (
    ArrayObject, BooleanObject, DictionaryObject, FloatObject, 
    IndirectObject, NameObject, NullObject, NumberObject, 
    StreamObject, TextStringObject
)

from pdfalyzer.decorators.pdf_tree_node import PdfTreeNode
from pdfalyzer.pdfalyzer import Pdfalyzer
from yaralyzer.util.logging import log


class PdfJsonEncoder(json.JSONEncoder):
    """Custom JSON encoder for PDF objects."""
    
    def default(self, obj):
        # Handle PDF-specific types
        if isinstance(obj, (NameObject, TextStringObject)):
            return str(obj)
        elif isinstance(obj, (NumberObject, FloatObject)):
            return float(obj)
        elif isinstance(obj, BooleanObject):
            return bool(obj)
        elif isinstance(obj, NullObject):
            return None
        elif isinstance(obj, IndirectObject):
            return {
                "_type": "IndirectObject",
                "idnum": obj.idnum,
                "generation": obj.generation
            }
        elif isinstance(obj, ArrayObject):
            return list(obj)
        elif isinstance(obj, DictionaryObject):
            return {str(k): v for k, v in obj.items()}
        elif isinstance(obj, StreamObject):
            return {
                "_type": "StreamObject",
                "dictionary": {str(k): v for k, v in obj.items()},
                "length": len(obj._data) if hasattr(obj, '_data') else 0
            }
        elif isinstance(obj, bytes):
            # For binary data, encode as base64 or just indicate presence
            return {
                "_type": "bytes",
                "length": len(obj),
                "preview": str(obj[:100]) if len(obj) <= 100 else str(obj[:100]) + "..."
            }
        elif hasattr(obj, '__dict__'):
            # For custom objects, try to serialize their attributes
            return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
        else:
            return super().default(obj)


class JsonExporter:
    """Handles JSON export of PDF analysis results."""
    
    def __init__(self, pdfalyzer: Pdfalyzer):
        self.pdfalyzer = pdfalyzer
        self.encoder = PdfJsonEncoder(indent=2)
    
    def export_all(self, output_dir: Path) -> Dict[str, Path]:
        """Export all analysis results to JSON files."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        exported_files = {}
        
        # Export each analysis type
        exported_files['docinfo'] = self.export_document_info(output_dir)
        exported_files['tree'] = self.export_tree(output_dir)
        exported_files['summary'] = self.export_summary(output_dir)
        exported_files['fonts'] = self.export_fonts(output_dir)
        exported_files['streams'] = self.export_streams(output_dir)
        
        return exported_files
    
    def export_document_info(self, output_dir: Path) -> Path:
        """Export document metadata and hashes to JSON."""
        data = {
            "pdf_file": self.pdfalyzer.pdf_basename,
            "pdf_path": str(self.pdfalyzer.pdf_path),
            "metadata": self._serialize_metadata(),
            "hashes": {
                "md5": self.pdfalyzer.pdf_bytes_info.md5,
                "sha1": self.pdfalyzer.pdf_bytes_info.sha1,
                "sha256": self.pdfalyzer.pdf_bytes_info.sha256
            },
            "file_size": self.pdfalyzer.pdf_bytes_info.size,
            "pdf_version": str(self.pdfalyzer.pdf_reader.pdf_header) if hasattr(self.pdfalyzer.pdf_reader, 'pdf_header') else None,
            "max_generation": self.pdfalyzer.max_generation,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        output_path = output_dir / f"{self.pdfalyzer.pdf_basename}_docinfo.json"
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, cls=PdfJsonEncoder)
        
        return output_path
    
    def export_tree(self, output_dir: Path) -> Path:
        """Export PDF tree structure to JSON."""
        data = {
            "pdf_file": self.pdfalyzer.pdf_basename,
            "root": self._serialize_node(self.pdfalyzer.pdf_tree),
            "total_nodes": len(list(LevelOrderIter(self.pdfalyzer.pdf_tree)))
        }
        
        output_path = output_dir / f"{self.pdfalyzer.pdf_basename}_tree.json"
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, cls=PdfJsonEncoder)
        
        return output_path
    
    def export_summary(self, output_dir: Path) -> Path:
        """Export node type counts and statistics to JSON."""
        data = self._analyze_tree()
        data["pdf_file"] = self.pdfalyzer.pdf_basename
        
        output_path = output_dir / f"{self.pdfalyzer.pdf_basename}_summary.json"
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, sort_keys=True)
        
        return output_path
    
    def export_fonts(self, output_dir: Path) -> Path:
        """Export font information to JSON."""
        fonts_data = []
        
        for font_info in self.pdfalyzer.font_infos:
            font_data = {
                "idnum": font_info.idnum if hasattr(font_info, 'idnum') else None,
                "label": font_info.label if hasattr(font_info, 'label') else None,
                "type": str(font_info.font_obj.get('/Type', '')) if hasattr(font_info, 'font_obj') else None,
                "subtype": str(font_info.font_obj.get('/Subtype', '')) if hasattr(font_info, 'font_obj') else None,
                "base_font": str(font_info.font_obj.get('/BaseFont', '')) if hasattr(font_info, 'font_obj') else None,
                "encoding": str(font_info.font_obj.get('/Encoding', '')) if hasattr(font_info, 'font_obj') else None,
                "has_font_file": font_info.font_file is not None if hasattr(font_info, 'font_file') else False,
                "has_to_unicode": font_info.font_obj.get('/ToUnicode') is not None if hasattr(font_info, 'font_obj') else False
            }
            
            # Add character mapping info if available
            if hasattr(font_info, 'character_mapping') and font_info.character_mapping:
                font_data["character_count"] = len(font_info.character_mapping)
                font_data["character_mapping_sample"] = dict(list(font_info.character_mapping.items())[:10])
            
            fonts_data.append(font_data)
        
        data = {
            "pdf_file": self.pdfalyzer.pdf_basename,
            "total_fonts": len(fonts_data),
            "fonts": fonts_data
        }
        
        output_path = output_dir / f"{self.pdfalyzer.pdf_basename}_fonts.json"
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return output_path
    
    def export_streams(self, output_dir: Path, include_data: bool = False) -> Path:
        """Export stream information to JSON."""
        streams_data = []
        
        for node in self.pdfalyzer.stream_nodes():
            stream_data = {
                "idnum": node.idnum,
                "generation": node.obj.generation if hasattr(node.obj, 'generation') else 0,
                "type": str(node.type),
                "subtype": str(node.sub_type) if node.sub_type else None,
                "stream_length": node.stream_length,
                "filters": self._get_stream_filters(node),
                "first_address": node.first_address
            }
            
            # Optionally include stream data (be careful with large PDFs)
            if include_data and node.stream_data:
                if len(node.stream_data) <= 1000:  # Only include small streams
                    stream_data["data_preview"] = str(node.stream_data[:500])
                else:
                    stream_data["data_preview"] = f"Stream too large ({len(node.stream_data)} bytes)"
            
            streams_data.append(stream_data)
        
        data = {
            "pdf_file": self.pdfalyzer.pdf_basename,
            "total_streams": len(streams_data),
            "streams": streams_data
        }
        
        output_path = output_dir / f"{self.pdfalyzer.pdf_basename}_streams.json"
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return output_path
    
    def export_yara_results(self, output_dir: Path, yara_matches: List[Any]) -> Path:
        """Export YARA scan results to JSON."""
        matches_data = []
        
        for match in yara_matches:
            match_data = {
                "rule": match.rule,
                "namespace": match.namespace,
                "tags": list(match.tags) if match.tags else [],
                "meta": dict(match.meta) if match.meta else {},
                "strings": []
            }
            
            for string in match.strings:
                string_data = {
                    "offset": string[0],
                    "identifier": string[1],
                    "string": str(string[2])
                }
                match_data["strings"].append(string_data)
            
            matches_data.append(match_data)
        
        data = {
            "pdf_file": self.pdfalyzer.pdf_basename,
            "total_matches": len(matches_data),
            "matches": matches_data
        }
        
        output_path = output_dir / f"{self.pdfalyzer.pdf_basename}_yara.json"
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return output_path
    
    def _serialize_node(self, node: PdfTreeNode) -> Dict[str, Any]:
        """Serialize a PDF tree node to a dictionary."""
        if isinstance(node, SymlinkNode):
            return {
                "_type": "SymlinkNode",
                "target_idnum": node.target.idnum if hasattr(node.target, 'idnum') else None,
                "reference_key": str(node.reference_key) if hasattr(node, 'reference_key') else None
            }
        
        node_data = {
            "idnum": node.idnum,
            "type": str(node.type),
            "subtype": str(node.sub_type) if node.sub_type else None,
            "label": node.label,
            "first_address": node.first_address,
            "known_to_parent_as": node.known_to_parent_as,
            "generation": node.obj.generation if hasattr(node.obj, 'generation') else 0,
            "has_stream": node.stream_data is not None if hasattr(node, 'stream_data') else False,
            "stream_length": node.stream_length if hasattr(node, 'stream_length') and node.stream_length > 0 else None
        }
        
        # Add PDF object data (simplified)
        if node.obj:
            try:
                if isinstance(node.obj, DictionaryObject):
                    node_data["object_data"] = {str(k): v for k, v in node.obj.items()}
                elif isinstance(node.obj, ArrayObject):
                    node_data["object_data"] = list(node.obj)
                else:
                    node_data["object_data"] = str(node.obj)
            except Exception as e:
                node_data["object_data"] = f"Error serializing object: {str(e)}"
        
        # Add children
        if node.children:
            node_data["children"] = [self._serialize_node(child) for child in node.children]
        
        # Add non-tree relationships
        if node.non_tree_relationships:
            node_data["references"] = [
                {
                    "to_idnum": rel.to_obj.idnum if hasattr(rel.to_obj, 'idnum') else None,
                    "reference_key": str(rel.reference_key),
                    "is_link": rel.is_link
                }
                for rel in node.non_tree_relationships
            ]
        
        return node_data
    
    def _serialize_metadata(self) -> Dict[str, Any]:
        """Serialize PDF metadata."""
        metadata = {}
        if self.pdfalyzer.pdf_reader.metadata:
            for key, value in self.pdfalyzer.pdf_reader.metadata.items():
                key_str = str(key)
                if hasattr(value, 'strftime'):  # It's a datetime
                    metadata[key_str] = value.isoformat()
                else:
                    metadata[key_str] = str(value)
        return metadata
    
    def _analyze_tree(self) -> Dict[str, Any]:
        """Analyze tree structure and return statistics."""
        node_type_counts = {}
        node_subtype_counts = {}
        total_stream_bytes = 0
        
        for node in LevelOrderIter(self.pdfalyzer.pdf_tree):
            if isinstance(node, SymlinkNode):
                continue
            
            # Count by type
            type_str = str(node.type)
            node_type_counts[type_str] = node_type_counts.get(type_str, 0) + 1
            
            # Count by subtype
            if node.sub_type:
                subtype_str = str(node.sub_type)
                node_subtype_counts[subtype_str] = node_subtype_counts.get(subtype_str, 0) + 1
            
            # Sum stream bytes
            if hasattr(node, 'stream_length') and node.stream_length and node.stream_length > 0:
                total_stream_bytes += node.stream_length
        
        return {
            "total_objects": len(list(LevelOrderIter(self.pdfalyzer.pdf_tree))),
            "node_type_counts": node_type_counts,
            "node_subtype_counts": node_subtype_counts,
            "total_stream_bytes": total_stream_bytes,
            "max_tree_depth": self.pdfalyzer.pdf_tree.height
        }
    
    def _get_stream_filters(self, node: PdfTreeNode) -> List[str]:
        """Extract filter information from a stream node."""
        filters = []
        if hasattr(node.obj, 'get') and '/Filter' in node.obj:
            filter_obj = node.obj['/Filter']
            if isinstance(filter_obj, ArrayObject):
                filters = [str(f) for f in filter_obj]
            else:
                filters = [str(filter_obj)]
        return filters