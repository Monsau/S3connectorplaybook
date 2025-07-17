"""
Validation utilities for the S3 Connector.
"""

import re
from typing import List, Dict, Any, Optional
from pathlib import Path


def validate_s3_bucket_name(bucket_name: str) -> bool:
    """
    Validate S3 bucket name according to AWS naming rules.
    
    Args:
        bucket_name: The bucket name to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not bucket_name or len(bucket_name) < 3 or len(bucket_name) > 63:
        return False
    
    # Check for valid characters and patterns
    pattern = r'^[a-z0-9][a-z0-9.-]*[a-z0-9]$'
    if not re.match(pattern, bucket_name):
        return False
    
    # Additional checks
    if '..' in bucket_name or '.-' in bucket_name or '-.' in bucket_name:
        return False
        
    # Check for IP address pattern
    ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if re.match(ip_pattern, bucket_name):
        return False
    
    return True


def validate_file_extensions(extensions: str) -> List[str]:
    """
    Validate and normalize file extensions.
    
    Args:
        extensions: Comma-separated string of file extensions
        
    Returns:
        List of validated extensions
    """
    if not extensions:
        return []
    
    valid_extensions = []
    for ext in extensions.split(','):
        ext = ext.strip().lower()
        if ext and not ext.startswith('.'):
            ext = '.' + ext
        if ext:
            valid_extensions.append(ext)
    
    return valid_extensions


def validate_tag_mapping(tag_mapping: str) -> Dict[str, str]:
    """
    Validate and parse tag mapping configuration.
    
    Args:
        tag_mapping: String in format "keyword1:tag1;keyword2:tag2"
        
    Returns:
        Dictionary mapping keywords to tags
    """
    if not tag_mapping:
        return {}
    
    mapping = {}
    for pair in tag_mapping.split(';'):
        if ':' in pair:
            keyword, tag = pair.split(':', 1)
            keyword = keyword.strip()
            tag = tag.strip()
            if keyword and tag:
                mapping[keyword] = tag
    
    return mapping


def validate_connection_config(config: Dict[str, Any]) -> List[str]:
    """
    Validate S3 connection configuration.
    
    Args:
        config: Connection configuration dictionary
        
    Returns:
        List of validation error messages
    """
    errors = []
    
    # Required fields
    required_fields = ['bucketName']
    for field in required_fields:
        if not config.get(field):
            errors.append(f"Missing required field: {field}")
    
    # Validate bucket name
    bucket_name = config.get('bucketName')
    if bucket_name and not validate_s3_bucket_name(bucket_name):
        errors.append(f"Invalid bucket name: {bucket_name}")
    
    # Validate credentials (either access keys or role-based)
    has_access_keys = config.get('awsAccessKeyId') and config.get('awsSecretAccessKey')
    has_role = config.get('useInstanceProfile') or config.get('roleArn')
    
    if not has_access_keys and not has_role:
        errors.append("Missing authentication: provide access keys or enable role-based authentication")
    
    # Validate endpoint URL format
    endpoint_url = config.get('endPointURL')
    if endpoint_url:
        if not endpoint_url.startswith(('http://', 'https://')):
            errors.append(f"Invalid endpoint URL format: {endpoint_url}")
    
    # Validate file formats
    file_formats = config.get('file_formats', '')
    if file_formats:
        try:
            validate_file_extensions(file_formats)
        except Exception as e:
            errors.append(f"Invalid file_formats: {e}")
    
    return errors


def sanitize_table_name(name: str) -> str:
    """
    Sanitize a table name for OpenMetadata compatibility.
    
    Args:
        name: Original table name
        
    Returns:
        Sanitized table name
    """
    # Replace invalid characters with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    
    # Ensure it starts with a letter or underscore
    if sanitized and sanitized[0].isdigit():
        sanitized = '_' + sanitized
    
    # Remove consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    
    # Ensure minimum length
    if not sanitized:
        sanitized = 'unnamed_table'
    
    return sanitized
