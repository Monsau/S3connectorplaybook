# File: connectors/s3/parsers/delta_parser.py

import pandas as pd
import tempfile
import os
from .base_parser import FileParser

class DeltaParser(FileParser):
    """
    Concrete parser for Delta Lake files.
    Delta tables are stored as a collection of Parquet files with transaction logs.
    This parser attempts to read the underlying Parquet files.
    """
    
    def parse(self, content: bytes) -> pd.DataFrame:
        """
        Parse Delta Lake content and return a DataFrame.
        
        Note: Delta tables are complex structures with transaction logs.
        This implementation attempts to extract data from individual Parquet files
        within the Delta table structure. For full Delta table functionality,
        consider using the delta-rs or deltalake library.
        
        Args:
            content (bytes): The binary content of a Delta file (usually Parquet)
            
        Returns:
            pd.DataFrame: Parsed data from the Delta file
        """
        try:
            # Delta tables typically contain Parquet files
            # Try to parse as Parquet first
            import pyarrow.parquet as pq
            import io
            
            # Read as Parquet file
            parquet_file = pq.ParquetFile(io.BytesIO(content))
            table = parquet_file.read()
            df = table.to_pandas()
            
            return df
            
        except ImportError:
            # Fallback if pyarrow is not available
            try:
                # Try using pandas parquet reader
                df = pd.read_parquet(io.BytesIO(content))
                return df
            except Exception as fallback_e:
                raise ValueError(f"Failed to parse Delta file as Parquet (pyarrow not available): {str(fallback_e)}")
                
        except Exception as e:
            # If direct Parquet parsing fails, try alternative approaches
            try:
                # Alternative: save to temp file and try different methods
                with tempfile.NamedTemporaryFile(delete=False, suffix='.parquet') as temp_file:
                    temp_file.write(content)
                    temp_file.flush()
                    
                    try:
                        # Try reading with pandas
                        df = pd.read_parquet(temp_file.name)
                        return df
                    finally:
                        # Clean up temp file
                        os.unlink(temp_file.name)
                        
            except Exception as temp_e:
                raise ValueError(f"Failed to parse Delta file: Original error: {str(e)}, Temp file error: {str(temp_e)}")
    
    def _is_delta_log_file(self, filename: str) -> bool:
        """
        Check if the file is a Delta transaction log file.
        
        Args:
            filename (str): The filename to check
            
        Returns:
            bool: True if it's a Delta log file
        """
        return filename.startswith('_delta_log/') and filename.endswith('.json')
    
    def _is_delta_data_file(self, filename: str) -> bool:
        """
        Check if the file is a Delta data file (Parquet).
        
        Args:
            filename (str): The filename to check
            
        Returns:
            bool: True if it's a Delta data file
        """
        return filename.endswith('.parquet') and not filename.startswith('_delta_log/')
