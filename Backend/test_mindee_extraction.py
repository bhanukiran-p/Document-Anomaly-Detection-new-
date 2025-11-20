#!/usr/bin/env python3
"""
Test script for Mindee SDK extraction
Usage: python test_mindee_extraction.py <file_path> [api_key] [model_id]
"""

import sys
import os
from pathlib import Path

# Configuration
input_path = "/path/to/the/file.ext"  # Change this to your file path
api_key = "md_GWYWbwGsjj6K6mzB7AhOT7SjuJhG5mbS"
model_id = "82f0edbf-7afb-4566-b5f5-5ffcad8647b4"

# Allow command line overrides
if len(sys.argv) > 1:
    input_path = sys.argv[1]
if len(sys.argv) > 2:
    api_key = sys.argv[2]
if len(sys.argv) > 3:
    model_id = sys.argv[3]

# Import the extractor
from mindee_extractor import MindeeExtractor

print("="*70)
print("MINDEE SDK EXTRACTION TEST")
print("="*70)
print(f"File Path: {input_path}")
print(f"API Key: {api_key[:15]}...")
print(f"Model ID: {model_id}")
print()

# Check if file exists
if not os.path.exists(input_path):
    print(f"❌ ERROR: File not found: {input_path}")
    print("\nUsage: python test_mindee_extraction.py <file_path> [api_key] [model_id]")
    print("\nExample:")
    print("  python test_mindee_extraction.py /Users/vikramramanathan/Documents/statement.pdf")
    sys.exit(1)

# Initialize extractor
print("Initializing Mindee Extractor...")
print("-" * 70)

try:
    extractor = MindeeExtractor(api_key, bank_statement_model_id=model_id)
    print("✓ Extractor initialized successfully\n")
except Exception as e:
    print(f"❌ Failed to initialize extractor: {e}")
    sys.exit(1)

# Determine file type and extract accordingly
file_ext = Path(input_path).suffix.lower()

print(f"File Type: {file_ext}")
print("Extraction Type: Bank Statement")
print("-" * 70)

try:
    print("\nExtracting...")
    result = extractor.extract_bank_statement(input_path)

    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    print(f"Success: {result['success']}")
    print(f"Method: {result['extraction_method']}")

    if result['success']:
        print("\n✓ Extraction successful!")
        print(f"\nExtracted Data:")
        print("-" * 70)

        data = result['data']
        if isinstance(data, dict):
            for key, value in data.items():
                if value:
                    print(f"  {key}: {value}")
        else:
            print(str(data))
    else:
        print(f"\n❌ Extraction failed!")
        print(f"Error: {result.get('error', 'Unknown error')}")

except Exception as e:
    print(f"❌ Exception during extraction: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*70)
