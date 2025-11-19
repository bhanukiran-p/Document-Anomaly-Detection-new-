#!/usr/bin/env python3
"""
Test script to verify calibrated fraud detection with multiple PDFs
"""
import requests
import json
from pathlib import Path

API_BASE_URL = "http://localhost:5001/api"
PDF_DIR = Path("/Users/vikramramanathan/Desktop/Document-Anomaly-Detection-new-/sample bank statement")

def test_pdf(pdf_path):
    """Test a single PDF"""
    if not pdf_path.exists():
        return None
    
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': (pdf_path.name, f, 'application/pdf')}
            response = requests.post(
                f"{API_BASE_URL}/fraud/validate-pdf",
                files=files,
                timeout=30
            )
        
        if response.status_code == 200:
            result = response.json()
            data = result.get('data', {})
            return {
                'file': pdf_path.name,
                'risk_score': data.get('risk_score'),
                'verdict': data.get('verdict'),
                'is_suspicious': data.get('is_suspicious'),
                'indicators': len(data.get('suspicious_indicators', []))
            }
    except Exception as e:
        print(f"Error testing {pdf_path.name}: {e}")
    
    return None

def main():
    print("="*70)
    print("FRAUD DETECTION CALIBRATION TEST")
    print("="*70)
    
    # Test all PDFs in sample directory
    results = []
    if PDF_DIR.exists():
        for pdf_file in sorted(PDF_DIR.glob("*.pdf")):
            print(f"\n📄 Testing: {pdf_file.name}")
            result = test_pdf(pdf_file)
            if result:
                results.append(result)
                print(f"   Score: {result['risk_score']} - {result['verdict']}")
                print(f"   Suspicious: {result['is_suspicious']} ({result['indicators']} indicators)")
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    high_risk = [r for r in results if r['risk_score'] >= 0.70]
    medium_risk = [r for r in results if 0.45 <= r['risk_score'] < 0.70]
    low_risk = [r for r in results if 0.25 <= r['risk_score'] < 0.45]
    clean = [r for r in results if r['risk_score'] < 0.25]
    
    print(f"\n🔴 HIGH RISK (≥0.70): {len(high_risk)}")
    for r in high_risk:
        print(f"   • {r['file']}: {r['risk_score']}")
    
    print(f"\n🟡 MEDIUM RISK (0.45-0.70): {len(medium_risk)}")
    for r in medium_risk:
        print(f"   • {r['file']}: {r['risk_score']}")
    
    print(f"\n🔵 LOW RISK (0.25-0.45): {len(low_risk)}")
    for r in low_risk:
        print(f"   • {r['file']}: {r['risk_score']}")
    
    print(f"\n🟢 CLEAN (<0.25): {len(clean)}")
    for r in clean:
        print(f"   • {r['file']}: {r['risk_score']}")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()
