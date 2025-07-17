# File: connectors/s3/parsers/hdf5_parser.py

import pandas as pd
import tempfile
import os
from .base_parser import FileParser

class Hdf5Parser(FileParser):
    """
    Concrete parser for HDF5 files (.h5, .hdf5).
    HDF5 is a hierarchical data format that can contain multiple datasets.
    """
    
    def parse(self, content: bytes) -> pd.DataFrame:
        """
        Parse HDF5 file content and return a DataFrame.
        
        For HDF5 files with multiple datasets, this parser will attempt to:
        1. Find pandas-compatible datasets
        2. Concatenate multiple datasets with a 'dataset_name' column
        3. Return the first readable dataset if concatenation fails
        
        Args:
            content (bytes): The binary content of the HDF5 file
            
        Returns:
            pd.DataFrame: Parsed data from the HDF5 file
        """
        try:
            # HDF5 requires file-based access, so we need to use a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.h5') as temp_file:
                temp_file.write(content)
                temp_file.flush()
                
                try:
                    # Try to read with pandas HDFStore first
                    try:
                        with pd.HDFStore(temp_file.name, mode='r') as store:
                            keys = store.keys()
                            
                            if not keys:
                                raise ValueError("HDF5 file contains no readable datasets")
                            
                            if len(keys) == 1:
                                # Single dataset
                                return store[keys[0]]
                            else:
                                # Multiple datasets - concatenate them
                                all_datasets = []
                                for key in keys:
                                    try:
                                        df = store[key]
                                        df['dataset_name'] = key.lstrip('/')  # Remove leading slash
                                        all_datasets.append(df)
                                    except Exception:
                                        # Skip datasets that can't be read as DataFrames
                                        continue
                                
                                if all_datasets:
                                    return pd.concat(all_datasets, ignore_index=True, sort=False)
                                else:
                                    raise ValueError("No datasets could be read as DataFrames")
                    
                    except Exception:
                        # Fallback: try using h5py for more flexibility
                        try:
                            import h5py
                            
                            with h5py.File(temp_file.name, 'r') as h5_file:
                                # Find datasets that look like tabular data
                                datasets = []
                                
                                def find_datasets(name, obj):
                                    if isinstance(obj, h5py.Dataset) and len(obj.shape) <= 2:
                                        datasets.append((name, obj))
                                
                                h5_file.visititems(find_datasets)
                                
                                if not datasets:
                                    raise ValueError("No suitable datasets found in HDF5 file")
                                
                                # Try to convert the first suitable dataset
                                for name, dataset in datasets:
                                    try:
                                        data = dataset[:]
                                        if len(data.shape) == 1:
                                            return pd.DataFrame({'data': data})
                                        elif len(data.shape) == 2:
                                            return pd.DataFrame(data)
                                    except Exception:
                                        continue
                                
                                raise ValueError("Could not convert any dataset to DataFrame")
                        
                        except ImportError:
                            raise ValueError("Failed to read HDF5 file. Install h5py for better HDF5 support.")
                
                finally:
                    # Clean up temp file
                    os.unlink(temp_file.name)
                    
        except Exception as e:
            raise ValueError(f"Failed to parse HDF5 file: {str(e)}")
    
    def _get_hdf5_info(self, file_path: str) -> dict:
        """
        Get information about the structure of an HDF5 file.
        
        Args:
            file_path (str): Path to the HDF5 file
            
        Returns:
            dict: Information about datasets in the file
        """
        try:
            import h5py
            info = {"datasets": [], "groups": []}
            
            with h5py.File(file_path, 'r') as h5_file:
                def collect_info(name, obj):
                    if isinstance(obj, h5py.Dataset):
                        info["datasets"].append({
                            "name": name,
                            "shape": obj.shape,
                            "dtype": str(obj.dtype)
                        })
                    elif isinstance(obj, h5py.Group):
                        info["groups"].append(name)
                
                h5_file.visititems(collect_info)
            
            return info
        except Exception:
            return {"datasets": [], "groups": [], "error": "Could not read HDF5 structure"}
