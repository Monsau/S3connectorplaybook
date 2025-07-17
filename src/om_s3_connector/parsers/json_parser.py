# File: connectors/s3/parsers/json_parser.py

import pandas as pd
import io
from .base_parser import FileParser

class JsonParser(FileParser):
    """
    Concrete parser for JSON files. It handles both standard and line-delimited JSON.
    """
    def parse(self, content: bytes) -> pd.DataFrame:
        try:
            # First, try to read as a multi-line JSON (common in data lakes)
            return pd.read_json(io.BytesIO(content), lines=True)
        except ValueError:
            # If that fails, try to read as a standard JSON object
            return pd.read_json(io.BytesIO(content))
