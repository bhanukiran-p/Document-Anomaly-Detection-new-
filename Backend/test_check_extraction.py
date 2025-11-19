"""
Test script to verify check extraction accuracy
Tests the two training check images to ensure all fields are extracted correctly
"""

import os
import sys
import json
import importlib.util

# Import the extractor module (handles hyphen in filename)
spec = importlib.util.spec_from_file_location(
    "production_google_vision_extractor",
    os.path.join(os.path.dirname(__file__), "production_google_vision-extractor.py")
)
extractor_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(extractor_module)
ProductionCheckExtractor = extractor_module.ProductionCheckExtractor

def test_check_extraction(image_path):
    """Test extraction from a single check image"""
    print(f"\n{'='*80}")
    print(f"Testing: {os.path.basename(image_path)}")
    print(f"{'='*80}")
    
    if not os.path.exists(image_path):
        print(f"ERROR: File not found: {image_path}")
        return None
    
    try:
        # Initialize extractor
        extractor = ProductionCheckExtractor()
        
        # Extract check details
        details = extractor.extract_check_details(image_path)
        
        # Display results
        print(f"\nExtraction Results:")
        print(f"  Bank Name: {details.get('bank_name', 'N/A')}")
        print(f"  Bank Type: {details.get('bank_type', 'N/A')}")
        print(f"  Payee Name: {details.get('payee_name', 'N/A')}")
        print(f"  Amount: {details.get('amount_numeric', 'N/A')}")
        print(f"  Amount in Words: {details.get('amount_words', 'N/A')}")
        print(f"  Date: {details.get('date', 'N/A')}")
        print(f"  Check Number: {details.get('check_number', 'N/A')}")
        print(f"  Account Number: {details.get('account_number', 'N/A')}")
        print(f"  Routing Number: {details.get('routing_number', 'N/A')}")
        print(f"  MICR Code: {details.get('micr_code', 'N/A')}")
        print(f"  Memo: {details.get('memo', 'N/A')}")
        print(f"  Signature Detected: {'YES' if details.get('signature_detected') else 'NO'}")
        print(f"  Confidence Score: {details.get('confidence_score', 0)}%")
        
        # Validation checks
        print(f"\nValidation:")
        issues = []
        
        # Check signature - should be False for training checks
        if details.get('signature_detected'):
            issues.append("WARNING: SIGNATURE DETECTED AS YES (should be NO for training checks)")
        else:
            print("  [OK] Signature correctly detected as NO")
        
        # Check critical fields
        if not details.get('payee_name'):
            issues.append("WARNING: Payee name is missing")
        else:
            print(f"  [OK] Payee name extracted: {details.get('payee_name')}")
        
        if not details.get('bank_name'):
            issues.append("WARNING: Bank name is missing")
        else:
            print(f"  [OK] Bank name extracted: {details.get('bank_name')}")
        
        if not details.get('amount_numeric'):
            issues.append("WARNING: Amount is missing")
        else:
            print(f"  [OK] Amount extracted: {details.get('amount_numeric')}")
        
        if not details.get('date'):
            issues.append("WARNING: Date is missing")
        else:
            print(f"  [OK] Date extracted: {details.get('date')}")
        
        if not details.get('check_number'):
            issues.append("WARNING: Check number is missing")
        else:
            print(f"  [OK] Check number extracted: {details.get('check_number')}")
        
        # Check amount in words
        amount_words = details.get('amount_words', '')
        if amount_words and 'MEMO' in amount_words.upper():
            issues.append("WARNING: Amount in words may be incorrectly extracted (contains MEMO)")
        elif amount_words:
            print(f"  [OK] Amount in words extracted: {amount_words[:50]}...")
        
        # Display issues if any
        if issues:
            print(f"\nWARNING: ISSUES FOUND:")
            for issue in issues:
                print(f"  {issue}")
        else:
            print(f"\n[SUCCESS] All validations passed!")
        
        return details
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    # Get base directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)
    
    # Test images - check if they exist
    checks_dir = os.path.join(project_root, 'Checks')
    test_images = []
    for filename in ['boa_logo_check_3003.png', 'chase_logo_check_4001.png']:
        full_path = os.path.join(checks_dir, filename)
        if os.path.exists(full_path):
            test_images.append(full_path)
        else:
            print(f"WARNING: {filename} not found in {checks_dir}")
    
    print("="*80)
    print("CHECK EXTRACTION TEST")
    print("="*80)
    print(f"Testing {len(test_images)} check images...")
    
    results = []
    for image_path in test_images:
        result = test_check_extraction(image_path)
        if result:
            results.append({
                'file': os.path.basename(image_path),
                'result': result
            })
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Tested {len(results)} checks")
    print(f"Successfully extracted: {len(results)}")
    
    # Summary of key fields
    print(f"\nField Extraction Summary:")
    for r in results:
        print(f"\n  {r['file']}:")
        print(f"    Signature: {'YES' if r['result'].get('signature_detected') else 'NO'}")
        print(f"    Payee: {r['result'].get('payee_name', 'MISSING')}")
        print(f"    Bank: {r['result'].get('bank_name', 'MISSING')}")
        print(f"    Amount: {r['result'].get('amount_numeric', 'MISSING')}")
        print(f"    Date: {r['result'].get('date', 'MISSING')}")
        print(f"    Check #: {r['result'].get('check_number', 'MISSING')}")

