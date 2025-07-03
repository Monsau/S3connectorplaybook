# File: connectors/s3/parsers/csv_parser.py

import pandas as pd
import io
from .base_parser import FileParser

class CsvParser(FileParser):
    """
    Concrete parser for CSV files.
    """
    def parse(self, content: bytes) -> pd.DataFrame:
        return pd.read_csv(io.BytesIO(content))
