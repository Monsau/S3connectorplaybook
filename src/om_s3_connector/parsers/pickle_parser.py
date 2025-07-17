# File: connectors/s3/parsers/pickle_parser.py

import pandas as pd
import pickle
import io
from .base_parser import FileParser

class PickleParser(FileParser):
    """
    Concrete parser for Python pickle files (.pkl, .pickle).
    Handles pickled pandas DataFrames and other Python objects that can be converted to DataFrames.
    """
    
    def parse(self, content: bytes) -> pd.DataFrame:
        """
        Parse pickle file content and return a DataFrame.
        
        This parser can handle:
        - Pickled pandas DataFrames (returned as-is)
        - Pickled lists/dicts that can be converted to DataFrames
        - Other Python objects (attempts conversion)
        
        Args:
            content (bytes): The binary content of the pickle file
            
        Returns:
            pd.DataFrame: Parsed data from the pickle file
        """
        try:
            # Unpickle the content
            obj = pickle.loads(content)
            
            # If it's already a DataFrame, return it
            if isinstance(obj, pd.DataFrame):
                return obj
            
            # If it's a Series, convert to DataFrame
            elif isinstance(obj, pd.Series):
                return obj.to_frame()
            
            # If it's a list of dictionaries, convert to DataFrame
            elif isinstance(obj, list) and len(obj) > 0 and isinstance(obj[0], dict):
                return pd.DataFrame(obj)
            
            # If it's a dictionary, try to convert to DataFrame
            elif isinstance(obj, dict):
                try:
                    return pd.DataFrame(obj)
                except ValueError:
                    # If dict can't be converted directly, try to create a single-row DataFrame
                    return pd.DataFrame([obj])
            
            # If it's a list, convert to DataFrame with a single column
            elif isinstance(obj, list):
                return pd.DataFrame({'data': obj})
            
            # If it's a numpy array, convert to DataFrame
            elif hasattr(obj, 'shape') and hasattr(obj, 'dtype'):  # numpy-like array
                import numpy as np
                if len(obj.shape) == 1:
                    return pd.DataFrame({'data': obj})
                elif len(obj.shape) == 2:
                    return pd.DataFrame(obj)
                else:
                    # Flatten multi-dimensional arrays
                    return pd.DataFrame({'data': obj.flatten()})
            
            # For other objects, try to convert to string representation
            else:
                return pd.DataFrame({'data': [str(obj)]})
                
        except pickle.UnpicklingError as e:
            raise ValueError(f"Failed to unpickle file: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to parse pickle file: {str(e)}")
    
    def _is_safe_to_unpickle(self, content: bytes) -> bool:
        """
        Basic safety check for pickle content.
        Note: This is a simple check and doesn't guarantee complete safety.
        In production, consider using restricted unpickling or allowlists.
        
        Args:
            content (bytes): The pickle content to check
            
        Returns:
            bool: True if basic safety checks pass
        """
        try:
            # Check if it starts with pickle protocol markers
            if len(content) < 2:
                return False
            
            # Check for common pickle protocol markers
            valid_protocols = [b'\x80\x02', b'\x80\x03', b'\x80\x04', b'\x80\x05']  # Protocols 2-5
            for protocol in valid_protocols:
                if content.startswith(protocol):
                    return True
            
            # Check for protocol 0 (ASCII)
            if content.startswith(b'('):
                return True
                
            return False
        except:
            return False
