"""
Test script for CSV Duplicate Detection Guardrail
Run this to verify duplicate detection is working correctly
"""

import sys
import logging
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from csv_duplicate_detector import CSVDuplicateDetector

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_exact_file_duplicate():
    """Test detection of exact same file uploaded twice"""
    print("\n" + "=" * 60)
    print("TEST 1: Exact File Duplicate Detection")
    print("=" * 60)

    detector = CSVDuplicateDetector(cache_file='test_cache.json', cache_ttl_hours=24)
    detector.clear_cache()

    # Find a CSV file in the current directory or models directory
    test_file = Path(__file__).parent / 'models' / 'training_data.csv'
    if not test_file.exists():
        print("⚠ Warning: test file not found, creating mock file")
        test_file = Path('test_transactions.csv')
        with open(test_file, 'w') as f:
            f.write("transaction_id,amount,merchant,date\n")
            f.write("TXN001,100.50,Amazon,2025-01-01\n")
            f.write("TXN002,250.00,Walmart,2025-01-02\n")

    # First upload - should NOT be duplicate
    is_dup, dup_type, prev = detector.check_duplicate(
        filepath=str(test_file),
        filename='transactions.csv'
    )
    assert not is_dup, "First upload should not be duplicate"
    print("✅ First upload correctly identified as NEW")

    # Second upload - should BE duplicate (exact file)
    is_dup, dup_type, prev = detector.check_duplicate(
        filepath=str(test_file),
        filename='transactions.csv'
    )
    assert is_dup, "Second upload should be duplicate"
    assert dup_type == 'exact_file', f"Should be exact_file duplicate, got {dup_type}"
    print(f"✅ Second upload correctly identified as DUPLICATE ({dup_type})")
    print(f"   Previous upload: {prev['timestamp']}")

    print("\n✅ Exact file duplicate test passed!")


def test_content_fingerprint():
    """Test detection of same content with different formatting"""
    print("\n" + "=" * 60)
    print("TEST 2: Content Fingerprint Detection")
    print("=" * 60)

    detector = CSVDuplicateDetector(cache_file='test_cache.json', cache_ttl_hours=24)
    detector.clear_cache()

    # Create two CSV files with same data but different formatting
    file1 = Path('test_file1.csv')
    file2 = Path('test_file2.csv')

    # File 1: Original format
    with open(file1, 'w') as f:
        f.write("amount,merchant,date\n")
        f.write("100.50,Amazon,2025-01-01\n")
        f.write("250.00,Walmart,2025-01-02\n")

    # File 2: Same data, different column order
    with open(file2, 'w') as f:
        f.write("merchant,amount,date\n")
        f.write("Amazon,100.50,2025-01-01\n")
        f.write("Walmart,250.00,2025-01-02\n")

    # First upload
    is_dup, dup_type, prev = detector.check_duplicate(
        filepath=str(file1),
        filename='file1.csv'
    )
    assert not is_dup, "First upload should not be duplicate"
    print("✅ First file uploaded successfully")

    # Second upload - same content, different format
    is_dup, dup_type, prev = detector.check_duplicate(
        filepath=str(file2),
        filename='file2.csv'
    )
    assert is_dup, "Second file should be detected as duplicate (same content)"
    assert dup_type in ['same_content', 'same_transactions'], f"Should detect content match, got {dup_type}"
    print(f"✅ Duplicate content detected ({dup_type})")

    # Clean up
    file1.unlink()
    file2.unlink()

    print("\n✅ Content fingerprint test passed!")


def test_transaction_signature():
    """Test detection of same transactions in different files"""
    print("\n" + "=" * 60)
    print("TEST 3: Transaction Signature Detection")
    print("=" * 60)

    detector = CSVDuplicateDetector(cache_file='test_cache.json', cache_ttl_hours=24)
    detector.clear_cache()

    file1 = Path('test_txn1.csv')
    file2 = Path('test_txn2.csv')

    # File 1: Original transactions
    with open(file1, 'w') as f:
        f.write("transaction_id,amount,merchant\n")
        f.write("TXN001,100.50,Amazon\n")
        f.write("TXN002,250.00,Walmart\n")
        f.write("TXN003,75.25,Target\n")

    # File 2: Same amounts and merchants, different IDs (common in re-exports)
    with open(file2, 'w') as f:
        f.write("transaction_id,amount,merchant\n")
        f.write("TXN999,100.50,Amazon\n")
        f.write("TXN888,250.00,Walmart\n")
        f.write("TXN777,75.25,Target\n")

    # First upload
    is_dup, dup_type, prev = detector.check_duplicate(
        filepath=str(file1),
        filename='transactions1.csv'
    )
    assert not is_dup, "First upload should not be duplicate"
    print("✅ First transaction set uploaded")

    # Second upload - same transaction values
    is_dup, dup_type, prev = detector.check_duplicate(
        filepath=str(file2),
        filename='transactions2.csv'
    )
    assert is_dup, "Should detect duplicate transactions"
    assert dup_type == 'same_transactions', f"Should detect transaction match, got {dup_type}"
    print(f"✅ Duplicate transactions detected ({dup_type})")

    # Clean up
    file1.unlink()
    file2.unlink()

    print("\n✅ Transaction signature test passed!")


def test_cache_persistence():
    """Test that cache persists across detector instances"""
    print("\n" + "=" * 60)
    print("TEST 4: Cache Persistence")
    print("=" * 60)

    cache_file = 'test_persistent_cache.json'

    # Create first detector and add a file
    detector1 = CSVDuplicateDetector(cache_file=cache_file, cache_ttl_hours=24)
    detector1.clear_cache()

    test_file = Path('test_persistence.csv')
    with open(test_file, 'w') as f:
        f.write("amount,merchant\n100,Amazon\n")

    is_dup, _, _ = detector1.check_duplicate(str(test_file), 'persistence.csv')
    assert not is_dup, "First upload should not be duplicate"
    print("✅ File cached by first detector instance")

    # Create second detector (simulates app restart)
    detector2 = CSVDuplicateDetector(cache_file=cache_file, cache_ttl_hours=24)

    # Should detect duplicate from cached data
    is_dup, dup_type, prev = detector2.check_duplicate(str(test_file), 'persistence.csv')
    assert is_dup, "Second detector should load cache and detect duplicate"
    print(f"✅ Second detector loaded cache and detected duplicate ({dup_type})")

    # Clean up
    test_file.unlink()
    Path(cache_file).unlink()

    print("\n✅ Cache persistence test passed!")


def test_upload_stats():
    """Test upload statistics tracking"""
    print("\n" + "=" * 60)
    print("TEST 5: Upload Statistics")
    print("=" * 60)

    detector = CSVDuplicateDetector(cache_file='test_stats_cache.json')
    detector.clear_cache()

    # Upload multiple files
    for i in range(3):
        test_file = Path(f'test_file_{i}.csv')
        with open(test_file, 'w') as f:
            f.write(f"amount,merchant\n{100 + i},Store{i}\n")

        detector.check_duplicate(str(test_file), f'file_{i}.csv')
        test_file.unlink()

    stats = detector.get_upload_stats()
    assert stats['total_uploads'] == 3, f"Should have 3 uploads, got {stats['total_uploads']}"
    print(f"✅ Upload stats tracked correctly: {stats['total_uploads']} uploads")
    print(f"   Cache file: {stats['cache_file']}")
    print(f"   Oldest upload: {stats['oldest_upload']}")
    print(f"   Newest upload: {stats['newest_upload']}")

    # Clean up
    Path('test_stats_cache.json').unlink()

    print("\n✅ Upload statistics test passed!")


def run_all_tests():
    """Run all duplicate detection tests"""
    print("\n" + "=" * 70)
    print(" " * 15 + "CSV DUPLICATE DETECTION TEST SUITE")
    print("=" * 70)

    try:
        test_exact_file_duplicate()
        test_content_fingerprint()
        test_transaction_signature()
        test_cache_persistence()
        test_upload_stats()

        print("\n" + "=" * 70)
        print(" " * 15 + "🎉 ALL TESTS PASSED! 🎉")
        print("=" * 70)
        print("\nDuplicate Detection Guardrail is working correctly and ready for production use.")
        print("\nKey Features Tested:")
        print("  ✅ Exact file duplicate detection (MD5 hash)")
        print("  ✅ Content fingerprint matching (same data, different format)")
        print("  ✅ Transaction signature matching (same transactions)")
        print("  ✅ Cache persistence across restarts")
        print("  ✅ Upload statistics tracking")
        print("\n" + "=" * 70)

        return True

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
