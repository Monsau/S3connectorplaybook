#!/bin/bash
# Activation script for the S3 Connector project
# Usage: source activate.sh

# Check if we're already in the virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    echo "🔄 Already in virtual environment: $VIRTUAL_ENV"
else
    # Navigate to project directory if not already there
    if [ ! -f "venv/bin/activate" ]; then
        cd /home/mustapha.fonsau/projects/S3connectorplaybook
    fi
    
    # Activate virtual environment
    echo "🚀 Activating virtual environment..."
    source venv/bin/activate
    
    # Add src to Python path for development
    export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
    
    echo "✅ Virtual environment activated!"
    echo "📍 Project directory: $(pwd)"
    echo "🐍 Python version: $(python --version)"
    echo "📦 Pip version: $(pip --version)"
    echo ""
    echo "🎯 You can now run:"
    echo "   python -c 'import om_s3_connector; print(\"S3 Connector ready!\")'"
    echo "   pip list"
    echo "   pytest tests/"
fi
