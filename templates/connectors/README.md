# Universal Connector Templates

This directory contains ready-to-use templates for creating OpenMetadata connectors for any data source type.

## Available Templates

### Connector Types
- **[file-based-connector.py](file-based-connector.py)** - For HDFS, local files, FTP, network shares, etc.
- **[database-connector.py](database-connector.py)** - For MySQL, PostgreSQL, Oracle, MongoDB, etc.
- **[api-connector.py](api-connector.py)** - For REST APIs, SaaS platforms, web services
- **[streaming-connector.py](streaming-connector.py)** - For Kafka, Kinesis, Pulsar, event streams

### Base Classes
- **[base-connector.py](base-connector.py)** - Common base class with shared functionality
- **[common-methods.py](common-methods.py)** - Utility methods and helpers

## Usage

1. **Choose Your Template**: Select the template that best matches your data source type
2. **Copy Template**: Copy to your connector directory
3. **Customize**: Implement the specific methods for your data source
4. **Test**: Use the provided test templates
5. **Deploy**: Follow the deployment patterns

## Template Features

- ✅ **Standard Interface**: All templates implement the OpenMetadata connector interface
- ✅ **Error Handling**: Comprehensive error handling and logging
- ✅ **Security Integration**: Built-in RBAC and authentication support
- ✅ **Performance Optimized**: Configurable parallel processing
- ✅ **Audit Ready**: Automatic audit trail generation
- ✅ **Testing Support**: Integrated with testing framework

## Quick Start

```bash
# Copy the appropriate template
cp templates/connectors/file-based-connector.py connectors/my_connector/connector.py

# Customize for your data source
nano connectors/my_connector/connector.py

# Test your implementation
python -m pytest tests/test_my_connector.py
```

See the main [README_UNIVERSAL.md](../../README_UNIVERSAL.md) for complete implementation guidance.
