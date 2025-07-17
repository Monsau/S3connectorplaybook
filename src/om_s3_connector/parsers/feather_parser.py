# File: connectors/s3/parsers/feather_parser.py

import pandas as pd
import io
from .base_parser import FileParser

class FeatherParser(FileParser):
    """
    Concrete parser for Feather files (.feather).
    Feather is a fast, interoperable data frame storage format.
    """
    
    def parse(self, content: bytes) -> pd.DataFrame:
        """
        Parse Feather file content and return a DataFrame.
        
        Args:
            content (bytes): The binary content of the Feather file
            
        Returns:
            pd.DataFrame: Parsed data from the Feather file
        """
        try:
            # Try using pyarrow for better performance
            try:
                import pyarrow.feather as feather
                
                # Read feather file from bytes
                df = feather.read_feather(io.BytesIO(content))
                return df
                
            except ImportError:
                # Fallback to pandas if pyarrow is not available
                # Note: pandas.read_feather also uses pyarrow under the hood
                # but this provides a clearer error message
                df = pd.read_feather(io.BytesIO(content))
                return df
                
        except Exception as e:
            # If direct reading fails, try with a temporary file
            try:
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.feather') as temp_file:
                    temp_file.write(content)
                    temp_file.flush()
                    
                    try:
                        df = pd.read_feather(temp_file.name)
                        return df
                    finally:
                        os.unlink(temp_file.name)
                        
            except Exception as temp_e:
                raise ValueError(f"Failed to parse Feather file: Original error: {str(e)}, Temp file error: {str(temp_e)}")
