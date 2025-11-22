"""
Test Mindee API connection and credentials
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials from environment
api_key = os.getenv("MINDEE_API_KEY")
model_id = os.getenv("MINDEE_MODEL_ID_CHECK")

print(f"API Key: {api_key}")
print(f"Model ID: {model_id}")
print()

# Test the Mindee API
try:
    from mindee import ClientV2, InferenceParameters, PathInput

    client = ClientV2(api_key)
    print("[OK] Mindee client initialized successfully")
    print()

    # Try to get account info or make a test request
    print("Testing API key validity...")

    # We'll need a test image to verify
    import tempfile
    from PIL import Image

    # Create a simple test image
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        img = Image.new('RGB', (100, 100), color='white')
        img.save(tmp.name)
        test_file = tmp.name

    print(f"Created test image: {test_file}")

    # Try to make a prediction
    try:
        input_source = PathInput(test_file)
        params = InferenceParameters(model_id=model_id)
        response = client.enqueue_and_get_inference(input_source, params)
        print("[SUCCESS] API call successful! Your Mindee credentials are valid.")
        print(f"Response type: {type(response)}")
    except Exception as e:
        print(f"[ERROR] API call failed: {e}")
        print()
        print("This might indicate:")
        print("  1. Your free trial has expired")
        print("  2. The API key is invalid")
        print("  3. The model ID is incorrect")
        print("  4. You need to activate your Mindee account")

    # Cleanup
    os.unlink(test_file)

except ImportError as e:
    print(f"[ERROR] Mindee library not available: {e}")
except Exception as e:
    print(f"[ERROR] Error: {e}")
