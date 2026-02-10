#!/usr/bin/env python3
"""
Database Data Quality Assessment for Model Retraining
Checks if your database has sufficient high-quality data for automated retraining
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.supabase_client import get_supabase
import json

# Try to import tabulate, if not available use simple printing
try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False
    def tabulate(data, headers=None, tablefmt=None):
        """Simple fallback for tabulate"""
        if not data:
            return "No data"
        if headers == 'keys' and data:
            headers = list(data[0].keys())
        result = []
        if headers:
            result.append(" | ".join(str(h) for h in headers))
            result.append("-" * 80)
        for row in data:
            if isinstance(row, dict):
                result.append(" | ".join(str(row.get(h, '')) for h in headers))
            else:
                result.append(" | ".join(str(v) for v in row))
        return "\n".join(result)


def print_section(title):
    """Print section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def check_overall_availability():
    """Check total documents and AI recommendations"""
    print_section("SECTION 1: OVERALL DATA AVAILABILITY")

    supabase = get_supabase()
    results = []

    for table in ['paystubs', 'checks', 'money_orders', 'bank_statements']:
        try:
            # Get total count
            total_response = supabase.table(table).select('id', count='exact').execute()
            total = total_response.count if total_response.count else 0

            # Get count with ai_recommendation
            with_rec_response = supabase.table(table)\
                .select('id', count='exact')\
                .not_.is_('ai_recommendation', 'null')\
                .execute()
            with_rec = with_rec_response.count if with_rec_response.count else 0

            results.append({
                'Document Type': table,
                'Total': total,
                'With AI Recommendation': with_rec,
                'Without AI Recommendation': total - with_rec
            })
        except Exception as e:
            print(f"Error querying {table}: {e}")
            results.append({
                'Document Type': table,
                'Total': 'Error',
                'With AI Recommendation': 'Error',
                'Without AI Recommendation': 'Error'
            })

    print(tabulate(results, headers='keys', tablefmt='grid'))
    return results


def check_recommendation_distribution(table_name):
    """Check distribution of APPROVE/REJECT/ESCALATE"""
    supabase = get_supabase()

    try:
        response = supabase.table(table_name)\
            .select('ai_recommendation', 'fraud_risk_score')\
            .not_.is_('ai_recommendation', 'null')\
            .execute()

        if not response.data:
            return []

        # Group by recommendation
        stats = {}
        for row in response.data:
            rec = row.get('ai_recommendation')
            score = row.get('fraud_risk_score', 0)

            if rec not in stats:
                stats[rec] = {'count': 0, 'scores': []}
            stats[rec]['count'] += 1
            if score is not None:
                stats[rec]['scores'].append(score)

        # Format results
        results = []
        total = sum(s['count'] for s in stats.values())

        for rec, data in sorted(stats.items(), key=lambda x: x[1]['count'], reverse=True):
            avg_score = sum(data['scores']) / len(data['scores']) if data['scores'] else 0
            min_score = min(data['scores']) if data['scores'] else 0
            max_score = max(data['scores']) if data['scores'] else 0

            results.append({
                'Recommendation': rec,
                'Count': data['count'],
                'Percentage': f"{data['count'] * 100 / total:.1f}%",
                'Avg Fraud Score': f"{avg_score:.3f}",
                'Min Score': f"{min_score:.3f}",
                'Max Score': f"{max_score:.3f}"
            })

        return results
    except Exception as e:
        print(f"Error: {e}")
        return []


def check_confidence_distribution(table_name):
    """Check confidence score distribution"""
    supabase = get_supabase()

    try:
        response = supabase.table(table_name)\
            .select('ai_recommendation', 'model_confidence', 'fraud_risk_score')\
            .in_('ai_recommendation', ['APPROVE', 'REJECT'])\
            .not_.is_('model_confidence', 'null')\
            .execute()

        if not response.data:
            return []

        # Group by confidence range and recommendation
        stats = {}
        for row in response.data:
            conf = row.get('model_confidence', 0)
            rec = row.get('ai_recommendation')
            score = row.get('fraud_risk_score', 0)

            # Determine range
            if conf >= 0.90:
                range_key = '0.90-1.00 (Excellent)'
            elif conf >= 0.80:
                range_key = '0.80-0.89 (Good)'
            elif conf >= 0.70:
                range_key = '0.70-0.79 (Fair)'
            elif conf >= 0.60:
                range_key = '0.60-0.69 (Low)'
            else:
                range_key = '< 0.60 (Very Low)'

            key = (range_key, rec)
            if key not in stats:
                stats[key] = {'count': 0, 'conf_scores': [], 'fraud_scores': []}

            stats[key]['count'] += 1
            stats[key]['conf_scores'].append(conf)
            stats[key]['fraud_scores'].append(score)

        # Format results
        results = []
        for (conf_range, rec), data in sorted(stats.items()):
            avg_conf = sum(data['conf_scores']) / len(data['conf_scores'])
            avg_fraud = sum(data['fraud_scores']) / len(data['fraud_scores'])

            results.append({
                'Confidence Range': conf_range,
                'Recommendation': rec,
                'Count': data['count'],
                'Avg Confidence': f"{avg_conf:.3f}",
                'Avg Fraud Score': f"{avg_fraud:.3f}"
            })

        return results
    except Exception as e:
        print(f"Error: {e}")
        return []


def check_high_confidence_readiness():
    """Check training readiness with high-confidence data (≥0.80)"""
    print_section("SECTION 4: HIGH-CONFIDENCE DATA (≥0.80) - TRAINING READINESS")

    supabase = get_supabase()
    results = []

    for table in ['paystubs', 'checks', 'money_orders', 'bank_statements']:
        try:
            # Get all usable data
            response = supabase.table(table)\
                .select('ai_recommendation', 'model_confidence')\
                .in_('ai_recommendation', ['APPROVE', 'REJECT'])\
                .execute()

            total_usable = len(response.data) if response.data else 0

            # Filter high confidence
            high_conf = [r for r in response.data if r.get('model_confidence', 0) >= 0.80] if response.data else []
            high_conf_count = len(high_conf)

            approve_count = len([r for r in high_conf if r.get('ai_recommendation') == 'APPROVE'])
            reject_count = len([r for r in high_conf if r.get('ai_recommendation') == 'REJECT'])

            fraud_ratio = reject_count / high_conf_count if high_conf_count > 0 else 0

            # Determine mode
            if high_conf_count >= 500:
                mode = 'REAL MODE (100% real)'
            elif high_conf_count >= 100:
                mode = 'HYBRID MODE (synth+real)'
            else:
                mode = 'SYNTHETIC MODE (100% synth)'

            # Determine status
            if high_conf_count >= 50 and approve_count >= 20 and reject_count >= 20 \
               and 0.10 <= fraud_ratio <= 0.60:
                status = '✅ READY'
                status_color = '\033[92m'  # Green
            elif high_conf_count < 50:
                status = '❌ NOT READY - Insufficient samples'
                status_color = '\033[91m'  # Red
            elif approve_count < 20:
                status = '❌ NOT READY - Too few APPROVE'
                status_color = '\033[91m'
            elif reject_count < 20:
                status = '❌ NOT READY - Too few REJECT'
                status_color = '\033[91m'
            elif fraud_ratio < 0.10:
                status = '⚠️  WARNING - Fraud ratio too low'
                status_color = '\033[93m'  # Yellow
            elif fraud_ratio > 0.60:
                status = '⚠️  WARNING - Fraud ratio too high'
                status_color = '\033[93m'
            else:
                status = '❓ CHECK DATA'
                status_color = '\033[93m'

            results.append({
                'Document Type': table,
                'Total Usable': total_usable,
                'High-Conf (≥0.80)': high_conf_count,
                'APPROVE': approve_count,
                'REJECT': reject_count,
                'Fraud %': f"{fraud_ratio * 100:.1f}%",
                'Mode': mode,
                'Status': status
            })

        except Exception as e:
            print(f"Error checking {table}: {e}")
            results.append({
                'Document Type': table,
                'Total Usable': 'Error',
                'High-Conf (≥0.80)': 'Error',
                'APPROVE': 'Error',
                'REJECT': 'Error',
                'Fraud %': 'Error',
                'Mode': 'Error',
                'Status': '❌ ERROR'
            })

    print(tabulate(results, headers='keys', tablefmt='grid'))
    print("\n📊 INTERPRETATION:")
    print("  ✅ READY: Can proceed with retraining using real data")
    print("  ❌ NOT READY: Use synthetic data only (insufficient high-confidence samples)")
    print("  ⚠️  WARNING: Can train but check fraud ratio (should be 10-60%)")

    return results


def check_schema():
    """Check if model_confidence column exists"""
    print_section("SECTION 5: SCHEMA CHECK - Model Confidence Column")

    supabase = get_supabase()
    results = []

    for table in ['paystubs', 'checks', 'money_orders', 'bank_statements']:
        try:
            # Try to query model_confidence
            response = supabase.table(table).select('model_confidence').limit(1).execute()
            exists = True
            sample_value = response.data[0].get('model_confidence') if response.data else None
        except:
            exists = False
            sample_value = None

        results.append({
            'Table': table,
            'Model Confidence Column Exists': '✅ Yes' if exists else '❌ No',
            'Sample Value': sample_value if sample_value is not None else 'N/A'
        })

    print(tabulate(results, headers='keys', tablefmt='grid'))

    missing = [r['Table'] for r in results if '❌' in r['Model Confidence Column Exists']]
    if missing:
        print(f"\n⚠️  WARNING: model_confidence column missing in: {', '.join(missing)}")
        print("   You'll need to add this column for confidence filtering to work.")

    return results


def main():
    """Run all checks"""
    print("\n" + "🔍 " * 40)
    print(" " * 20 + "DATABASE DATA QUALITY ASSESSMENT")
    print(" " * 15 + "Model Retraining Readiness Check")
    print("🔍 " * 40)

    try:
        # Section 1: Overall availability
        overall = check_overall_availability()

        # Section 2 & 3: Distribution for each document type
        for table_name, display_name in [
            ('paystubs', 'PAYSTUBS'),
            ('checks', 'CHECKS'),
            ('money_orders', 'MONEY ORDERS'),
            ('bank_statements', 'BANK STATEMENTS')
        ]:
            print_section(f"SECTION 2: {display_name} - Recommendation Distribution")
            rec_dist = check_recommendation_distribution(table_name)
            if rec_dist:
                print(tabulate(rec_dist, headers='keys', tablefmt='grid'))
            else:
                print(f"No data found in {table_name} table")

            print_section(f"SECTION 3: {display_name} - Confidence Score Distribution")
            conf_dist = check_confidence_distribution(table_name)
            if conf_dist:
                print(tabulate(conf_dist, headers='keys', tablefmt='grid'))
            else:
                print(f"No confidence data found in {table_name} table")

        # Section 4: High-confidence readiness (THE KEY SECTION)
        readiness = check_high_confidence_readiness()

        # Section 5: Schema check
        schema = check_schema()

        # Final summary
        print_section("FINAL SUMMARY & RECOMMENDATIONS")

        ready_count = sum(1 for r in readiness if '✅' in r['Status'])
        warning_count = sum(1 for r in readiness if '⚠️' in r['Status'])
        not_ready_count = sum(1 for r in readiness if '❌' in r['Status'])

        print(f"Document Types Ready for Retraining: {ready_count}/4")
        print(f"Document Types with Warnings: {warning_count}/4")
        print(f"Document Types Not Ready: {not_ready_count}/4\n")

        if ready_count > 0:
            print("✅ You can proceed with implementing automated retraining!")
            ready_types = [r['Document Type'] for r in readiness if '✅' in r['Status']]
            print(f"   Ready types: {', '.join(ready_types)}")

        if warning_count > 0:
            print("\n⚠️  Some document types have warnings - check fraud ratio")
            warning_types = [r['Document Type'] for r in readiness if '⚠️' in r['Status']]
            print(f"   Warning types: {', '.join(warning_types)}")

        if not_ready_count > 0:
            print("\n❌ Some document types need more data:")
            not_ready_types = [r['Document Type'] for r in readiness if '❌' in r['Status']]
            for doc_type in not_ready_types:
                doc_data = next(r for r in readiness if r['Document Type'] == doc_type)
                print(f"   • {doc_type}: {doc_data['High-Conf (≥0.80)']} high-confidence samples")
                print(f"     (Need: 50 total, 20 APPROVE, 20 REJECT)")

        print("\n" + "="*80)
        print("\n💡 NEXT STEPS:")
        if ready_count >= 1:
            print("   1. Proceed with implementing document-specific retrainer subclasses")
            print("   2. Start with ready document types first")
            print("   3. Enable automated retraining for tested types")
        else:
            print("   1. Continue analyzing more documents to build up training data")
            print("   2. Focus on getting high-confidence predictions (≥0.80)")
            print("   3. Ensure both APPROVE and REJECT labels are present")
            print("   4. Re-run this check after processing 100+ more documents")

        print("\n   Report saved to: Backend/scripts/retraining_readiness_report.txt")

    except Exception as e:
        print(f"\n❌ Error running checks: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
