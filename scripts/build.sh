#!/bin/bash
# Build and installation script for S3 Connector

set -e

echo "🚀 S3 Connector Build Script"
echo "============================"

# Check Python version
echo "📊 Checking Python version..."
python_version=$(python --version 2>&1 | cut -d' ' -f2)
echo "✅ Python version: $python_version"

# Check if we're in virtual environment (recommended)
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Warning: Not in a virtual environment"
    echo "   Consider running: python -m venv venv && source venv/bin/activate"
fi

# Install dependencies
echo -e "\n📦 Installing dependencies..."
pip install -r requirements.txt

# Install development dependencies (optional)
if [[ "${1:-}" == "--dev" ]]; then
    echo "📦 Installing development dependencies..."
    pip install -e ".[dev]"
fi

# Install the package in development mode
echo -e "\n🔧 Installing S3 Connector in development mode..."
pip install -e .

# Run basic tests
echo -e "\n🧪 Running basic tests..."
python -c "
import sys
sys.path.insert(0, 'src')
try:
    from s3_connector import S3Source
    print('✅ S3Source import successful')
except Exception as e:
    print(f'❌ Import failed: {e}')
    sys.exit(1)
"

# Set up pre-commit hooks (if in dev mode)
if [[ "${1:-}" == "--dev" ]] && command -v pre-commit &> /dev/null; then
    echo -e "\n🔧 Setting up pre-commit hooks..."
    pre-commit install
fi

echo -e "\n✨ Build completed successfully!"
echo "📖 Next steps:"
echo "   1. Configure your settings in config/ingestion.yaml"
echo "   2. Set PYTHONPATH: export PYTHONPATH=\$(pwd)/src"
echo "   3. Run ingestion: metadata ingest -c config/ingestion.yaml"
