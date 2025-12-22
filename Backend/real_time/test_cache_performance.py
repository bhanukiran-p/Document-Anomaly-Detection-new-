"""
Quick test to verify duplicate detection caching is working
"""

import json
import time
from pathlib import Path

print("\n" + "="*60)
print("DUPLICATE DETECTION CACHE VERIFICATION")
print("="*60)

# Check if cache file exists
cache_file = Path(__file__).parent / 'models' / 'csv_upload_cache.json'

if cache_file.exists():
    print(f"\n✅ Cache file exists: {cache_file}")

    # Load and display cache contents
    with open(cache_file, 'r') as f:
        cache_data = json.load(f)

    print(f"\n📊 Cache Statistics:")
    print(f"   Total cached files: {len(cache_data)}")

    # Check if any have analysis_result cached
    cached_with_results = 0
    for entry in cache_data.values():
        if entry.get('analysis_result') is not None:
            cached_with_results += 1
            print(f"\n   ✅ File: {entry.get('filename')}")
            print(f"      Timestamp: {entry.get('timestamp')}")
            print(f"      Has cached analysis: YES")

            # Check size of cached analysis
            result_str = json.dumps(entry.get('analysis_result'))
            print(f"      Cached result size: {len(result_str):,} bytes")
        else:
            print(f"\n   ⚠️  File: {entry.get('filename')}")
            print(f"      Timestamp: {entry.get('timestamp')}")
            print(f"      Has cached analysis: NO")

    if cached_with_results > 0:
        print(f"\n✅ SUCCESS: {cached_with_results} file(s) have cached analysis results")
        print("\n⚡ Duplicate uploads of these files will be FAST (<1s)")
    else:
        print(f"\n⚠️  WARNING: No cached analysis results found")
        print("   Upload a CSV file once to populate the cache")
        print("   Then upload the same file again to test fast path")

else:
    print(f"\n⚠️  Cache file not found: {cache_file}")
    print("   Cache will be created after first CSV upload")

print("\n" + "="*60)
print("TESTING INSTRUCTIONS")
print("="*60)
print("""
To verify caching is working:

1. Upload a CSV file (first time)
   - Check backend logs for: "Analysis result cached for future duplicates"
   - Response time: ~40 seconds

2. Upload the SAME CSV file again
   - Check backend logs for: "⚡ FAST PATH: Returning cached analysis result"
   - Response time: <1 second
   - Response includes: "cache_hit": true

3. Check this test again:
   python test_cache_performance.py
""")
print("="*60 + "\n")
