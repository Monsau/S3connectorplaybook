# File: src/om_s3_connector/parsers/orc_parser.py

import pandas as pd
from typing import Optional, Dict, Any
from .base_parser import FileParser

class OrcParser(FileParser):
    """Parser for Apache ORC files"""
    
    def __init__(self):
        super().__init__()
        self.file_format = "orc"
    
    def can_parse(self, file_path: str) -> bool:
        """Check if this parser can handle the given file"""
        return file_path.lower().endswith('.orc')
    
    def parse_schema(self, file_path: str, sample_size: int = 1000) -> Dict[str, Any]:
        """Parse schema from ORC file"""
        try:
            # Try to read with pyarrow if available, otherwise use pandas
            try:
                import pyarrow.orc as orc
                table = orc.read_table(file_path)
                df = table.to_pandas(limit=sample_size)
            except ImportError:
                # Fallback to pandas (requires pyorc)
                import pyorc
                with open(file_path, 'rb') as f:
                    reader = pyorc.Reader(f)
                    records = []
                    for i, row in enumerate(reader):
                        if i >= sample_size:
                            break
                        records.append(row)
                    
                    if records:
                        df = pd.DataFrame(records)
                    else:
                        df = pd.DataFrame()
            
            return self._extract_schema_from_dataframe(df)
            
        except Exception as e:
            self.logger.error(f"Error parsing ORC file {file_path}: {e}")
            return {}
    
    def parse_data(self, file_path: str, limit: Optional[int] = None) -> pd.DataFrame:
        """Parse data from ORC file"""
        try:
            # Try to read with pyarrow if available
            try:
                import pyarrow.orc as orc
                table = orc.read_table(file_path)
                df = table.to_pandas()
                if limit:
                    df = df.head(limit)
                return df
            except ImportError:
                # Fallback to pandas (requires pyorc)
                import pyorc
                with open(file_path, 'rb') as f:
                    reader = pyorc.Reader(f)
                    records = []
                    for i, row in enumerate(reader):
                        if limit and i >= limit:
                            break
                        records.append(row)
                    
                    return pd.DataFrame(records) if records else pd.DataFrame()
                    
        except Exception as e:
            self.logger.error(f"Error reading ORC file {file_path}: {e}")
            return pd.DataFrame()
    
    def get_file_stats(self, file_path: str) -> Dict[str, Any]:
        """Get file statistics for ORC file"""
        stats = super().get_file_stats(file_path)
        
        try:
            # Try to get ORC-specific metadata
            try:
                import pyarrow.orc as orc
                with orc.ORCFile(file_path) as orc_file:
                    stats.update({
                        'row_count': orc_file.nrows,
                        'compression': orc_file.compression,
                        'stripe_count': orc_file.nstripes,
                    })
            except ImportError:
                # Fallback approach
                import pyorc
                with open(file_path, 'rb') as f:
                    reader = pyorc.Reader(f)
                    stats.update({
                        'row_count': reader.num_of_rows,
                        'compression': reader.compression,
                        'stripe_count': reader.num_of_stripes,
                    })
        except Exception as e:
            self.logger.warning(f"Could not get ORC metadata for {file_path}: {e}")
            
        return stats