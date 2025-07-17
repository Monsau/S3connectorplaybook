# File: connectors/s3/parsers/jsonl_parser.py

import pandas as pd
import json
import io
from .base_parser import FileParser

class JsonlParser(FileParser):
    """
    Concrete parser for JSON Lines files (.jsonl, .ndjson).
    JSON Lines format contains one JSON object per line.
    """
    
    def parse(self, content: bytes) -> pd.DataFrame:
        """
        Parse JSON Lines file content and return a DataFrame.
        
        Each line in the file should contain a valid JSON object.
        All objects will be combined into a single DataFrame.
        
        Args:
            content (bytes): The binary content of the JSONL file
            
        Returns:
            pd.DataFrame: Parsed data from the JSONL file
        """
        try:
            # Decode bytes to string
            text_content = content.decode('utf-8')
            
            # Split into lines and parse each JSON object
            json_objects = []
            lines = text_content.strip().split('\n')
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                
                try:
                    json_obj = json.loads(line)
                    json_objects.append(json_obj)
                except json.JSONDecodeError as e:
                    # Add line number to error for debugging
                    raise ValueError(f"Invalid JSON on line {line_num}: {str(e)}")
            
            if not json_objects:
                raise ValueError("No valid JSON objects found in JSONL file")
            
            # Convert list of JSON objects to DataFrame
            df = pd.DataFrame(json_objects)
            return df
            
        except UnicodeDecodeError as e:
            # Try alternative encodings
            try:
                text_content = content.decode('latin-1')
                json_objects = []
                lines = text_content.strip().split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        json_obj = json.loads(line)
                        json_objects.append(json_obj)
                    except json.JSONDecodeError as e:
                        raise ValueError(f"Invalid JSON on line {line_num}: {str(e)}")
                
                if json_objects:
                    return pd.DataFrame(json_objects)
                else:
                    raise ValueError("No valid JSON objects found")
                    
            except Exception:
                raise ValueError(f"Failed to decode JSONL file: {str(e)}")
                
        except Exception as e:
            raise ValueError(f"Failed to parse JSONL file: {str(e)}")
    
    def _validate_jsonl_line(self, line: str) -> bool:
        """
        Validate if a line contains valid JSON.
        
        Args:
            line (str): The line to validate
            
        Returns:
            bool: True if the line contains valid JSON
        """
        try:
            json.loads(line.strip())
            return True
        except json.JSONDecodeError:
            return False
    
    def _preview_jsonl_structure(self, content: bytes, max_lines: int = 10) -> dict:
        """
        Preview the structure of a JSONL file.
        
        Args:
            content (bytes): The JSONL file content
            max_lines (int): Maximum number of lines to analyze
            
        Returns:
            dict: Information about the JSONL structure
        """
        try:
            text_content = content.decode('utf-8')
            lines = text_content.strip().split('\n')
            
            preview_info = {
                "total_lines": len([l for l in lines if l.strip()]),
                "sample_objects": [],
                "common_keys": set(),
                "data_types": {}
            }
            
            analyzed = 0
            for line in lines:
                if analyzed >= max_lines:
                    break
                    
                line = line.strip()
                if not line:
                    continue
                
                try:
                    obj = json.loads(line)
                    preview_info["sample_objects"].append(obj)
                    
                    if isinstance(obj, dict):
                        preview_info["common_keys"].update(obj.keys())
                    
                    analyzed += 1
                except json.JSONDecodeError:
                    continue
            
            # Convert set to list for JSON serialization
            preview_info["common_keys"] = list(preview_info["common_keys"])
            
            return preview_info
            
        except Exception as e:
            return {"error": f"Could not preview JSONL structure: {str(e)}"}
