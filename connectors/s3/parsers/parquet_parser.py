# File: connectors/s3/parsers/parquet_parser.py

import pandas as pd
import io
from .base_parser import FileParser

class ParquetParser(FileParser):
    """
    Concrete parser for Parquet files.
    """
    def parse(self, content: bytes) -> pd.DataFrame:
        return pd.read_parquet(io.BytesIO(content))
