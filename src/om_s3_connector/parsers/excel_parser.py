# File: connectors/s3/parsers/excel_parser.py

import pandas as pd
import io
from .base_parser import FileParser

class ExcelParser(FileParser):
    """
    Concrete parser for Excel files (.xlsx, .xls).
    Handles multiple sheets by concatenating them into a single DataFrame.
    """
    
    def parse(self, content: bytes) -> pd.DataFrame:
        """
        Parse Excel file content and return a DataFrame.
        
        For files with multiple sheets, concatenates all sheets into a single DataFrame
        with an additional 'sheet_name' column to identify the source sheet.
        
        Args:
            content (bytes): The binary content of the Excel file
            
        Returns:
            pd.DataFrame: Parsed data from all sheets
        """
        try:
            # Read Excel file from bytes
            excel_file = pd.ExcelFile(io.BytesIO(content))
            
            # Get all sheet names
            sheet_names = excel_file.sheet_names
            
            if len(sheet_names) == 1:
                # Single sheet - return as is
                return pd.read_excel(io.BytesIO(content), sheet_name=0)
            else:
                # Multiple sheets - concatenate with sheet name identifier
                all_sheets = []
                for sheet_name in sheet_names:
                    df = pd.read_excel(io.BytesIO(content), sheet_name=sheet_name)
                    # Add sheet name as a column for identification
                    df['sheet_name'] = sheet_name
                    all_sheets.append(df)
                
                # Concatenate all sheets
                return pd.concat(all_sheets, ignore_index=True, sort=False)
                
        except Exception as e:
            # If Excel parsing fails, try to provide a helpful error message
            raise ValueError(f"Failed to parse Excel file: {str(e)}")
