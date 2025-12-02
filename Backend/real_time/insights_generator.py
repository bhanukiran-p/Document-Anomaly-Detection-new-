"""
Insights Generator for Transaction Analysis
Generates comprehensive analytics datasets for the React dashboard
"""
import hashlib
import logging
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from .fraud_detector import (
    LEGITIMATE_LABEL,
    OTHER_FRAUD_LABEL,
    STANDARD_FRAUD_REASONS,
)

logger = logging.getLogger(__name__)

COLOR_FRAUD = '#f97066'
COLOR_LEGIT = '#34d399'
COLOR_ACCENT = '#60a5fa'
COLOR_WARNING = '#fbbf24'


def generate_insights(analysis_result: Dict[str, Any], filters: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Generate comprehensive insights from fraud detection results.

    Args:
        analysis_result: Result from detect_fraud_in_transactions
        filters: Optional dictionary with filter parameters:
            - amount_min: Minimum transaction amount
            - amount_max: Maximum transaction amount
            - fraud_probability_min: Minimum fraud probability
            - fraud_probability_max: Maximum fraud probability
            - category: Category filter (substring match)
            - hour_of_day_start: Start hour (0-23)
            - hour_of_day_end: End hour (0-23)
            - fraud_only: Boolean, show only fraud transactions
            - legitimate_only: Boolean, show only legitimate transactions

    Returns:
        Dictionary containing insights and plots
    """
    try:
        logger.info("Generating insights from analysis results")

        if not analysis_result.get('success'):
            return {
                'success': False,
                'error': 'Cannot generate insights from failed analysis'
            }

        transactions = analysis_result['transactions']
        df = pd.DataFrame(transactions)
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        original_count = len(df)
        
        # Apply filters if provided
        if filters:
            logger.info(f"Applying filters: {filters}")
            df = _apply_filters(df, filters)
            logger.info(f"Applied filters: {original_count} -> {len(df)} transactions remaining")
            
            if len(df) == 0:
                logger.warning("Filters resulted in zero transactions - returning empty results")
                return {
                    'success': True,
                    'statistics': {},
                    'plots': [],
                    'fraud_patterns': {'message': 'No transactions match the applied filters'},
                    'recommendations': ['No data available for the selected filters. Try adjusting your filter criteria.'],
                    'generated_at': datetime.now().isoformat()
                }
        else:
            logger.info(f"No filters provided, using all {len(df)} transactions")

        # Update analysis_result with filtered data for accurate statistics
        filtered_analysis_result = analysis_result.copy()
        if filters and len(df) > 0:
            # Recalculate statistics based on filtered data
            fraud_count = int((df['is_fraud'] == 1).sum())
            legit_count = int((df['is_fraud'] == 0).sum())
            filtered_analysis_result['fraud_count'] = fraud_count
            filtered_analysis_result['legitimate_count'] = legit_count
            filtered_analysis_result['fraud_percentage'] = (fraud_count / len(df) * 100) if len(df) > 0 else 0
            filtered_analysis_result['legitimate_percentage'] = (legit_count / len(df) * 100) if len(df) > 0 else 0
            filtered_analysis_result['total_fraud_amount'] = float(df[df['is_fraud'] == 1]['amount'].sum()) if fraud_count > 0 else 0
            filtered_analysis_result['total_legitimate_amount'] = float(df[df['is_fraud'] == 0]['amount'].sum()) if legit_count > 0 else 0
            filtered_analysis_result['total_amount'] = float(df['amount'].sum())
            filtered_analysis_result['average_fraud_probability'] = float(df['fraud_probability'].mean()) if len(df) > 0 else 0
        else:
            filtered_analysis_result = analysis_result

        # Generate statistics
        statistics = _generate_statistics(df, filtered_analysis_result)

        # Generate datasets for the React dashboard
        plots = _build_react_plots(df)

        # Generate fraud patterns
        fraud_patterns = _analyze_fraud_patterns(df)

        # Generate recommendations
        recommendations = _generate_recommendations(df, filtered_analysis_result)

        # Top fraud cases
        top_fraud_cases = _get_top_fraud_cases(df)

        result = {
            'success': True,
            'statistics': statistics,
            'plots': plots,
            'fraud_patterns': fraud_patterns,
            'recommendations': recommendations,
            'top_fraud_cases': top_fraud_cases,
            'generated_at': datetime.now().isoformat()
        }

        logger.info(f"Successfully generated insights with {len(plots)} plots")
        return result

    except Exception as e:
        logger.error(f"Insight generation failed: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to generate insights'
        }


def _generate_statistics(df: pd.DataFrame, analysis_result: Dict) -> Dict[str, Any]:
    """Generate detailed statistics from transaction data."""
    fraud_df = df[df['is_fraud'] == 1]
    legit_df = df[df['is_fraud'] == 0]

    stats = {
        'overview': {
            'total_transactions': len(df),
            'fraud_count': int(fraud_df.shape[0]),
            'legitimate_count': int(legit_df.shape[0]),
            'fraud_percentage': analysis_result.get('fraud_percentage', 0),
            'total_amount': float(df['amount'].sum()),
            'fraud_amount': float(fraud_df['amount'].sum()) if len(fraud_df) > 0 else 0,
            'legitimate_amount': float(legit_df['amount'].sum()) if len(legit_df) > 0 else 0
        },
        'fraud_stats': {
            'average_fraud_amount': float(fraud_df['amount'].mean()) if len(fraud_df) > 0 else 0,
            'max_fraud_amount': float(fraud_df['amount'].max()) if len(fraud_df) > 0 else 0,
            'min_fraud_amount': float(fraud_df['amount'].min()) if len(fraud_df) > 0 else 0,
            'median_fraud_amount': float(fraud_df['amount'].median()) if len(fraud_df) > 0 else 0
        },
        'legitimate_stats': {
            'average_legitimate_amount': float(legit_df['amount'].mean()) if len(legit_df) > 0 else 0,
            'max_legitimate_amount': float(legit_df['amount'].max()) if len(legit_df) > 0 else 0,
            'min_legitimate_amount': float(legit_df['amount'].min()) if len(legit_df) > 0 else 0,
            'median_legitimate_amount': float(legit_df['amount'].median()) if len(legit_df) > 0 else 0
        }
    }

    # Fraud type distribution if available
    if 'fraud_type' in df.columns:
        type_counts = fraud_df['fraud_type'].value_counts()
        total = type_counts.sum()
        stats['fraud_types'] = [
            {
                'type': fraud_type,
                'count': int(count),
                'percentage': round((count / total) * 100, 2) if total else 0.0
            }
            for fraud_type, count in type_counts.items()
        ]

    # Time-based stats if timestamp available
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        stats['time_analysis'] = {
            'date_range': {
                'start': df['timestamp'].min().isoformat() if pd.notna(df['timestamp'].min()) else None,
                'end': df['timestamp'].max().isoformat() if pd.notna(df['timestamp'].max()) else None
            },
            'fraud_by_hour': fraud_df.groupby(fraud_df['timestamp'].dt.hour)['amount'].count().to_dict() if len(fraud_df) > 0 else {}
        }

    # Category-based stats if available
    if 'category' in df.columns:
        stats['category_analysis'] = {
            'fraud_by_category': fraud_df['category'].value_counts().to_dict() if len(fraud_df) > 0 else {},
            'total_by_category': df['category'].value_counts().to_dict()
        }

    return stats


def _format_currency(value: float) -> str:
    try:
        return f"${value:,.2f}"
    except Exception:
        return "$0.00"


def _format_percent(value: float) -> str:
    return f"{value:.1f}%"


def _detail(label: str, value: str) -> Dict[str, str]:
    return {'label': label, 'value': value}


def _build_react_plots(df: pd.DataFrame) -> List[Dict[str, Any]]:
    '''Generate structured datasets for the React dashboard (no base64 images).'''
    builders = [
        _build_donut_plot,
        _build_monthly_trend_plot,
        _build_correlation_heatmap_plot,
        _build_geo_scatter_plot,
        _build_fraud_reason_bar_plot,
        _build_sankey_plot,
    ]

    plots: List[Dict[str, Any]] = []
    for builder in builders:
        try:
            payload = builder(df)
            if payload:
                plots.append(payload)
        except Exception as exc:
            logger.warning(f"Plot builder {builder.__name__} failed: {exc}", exc_info=True)
    return plots


def _build_donut_plot(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    if 'is_fraud' not in df.columns or len(df) == 0:
        return None

    counts = df['is_fraud'].value_counts()
    fraud_count = int(counts.get(1, 0))
    legit_count = int(counts.get(0, 0))
    total = fraud_count + legit_count
    if total == 0:
        return None

    data = [
        {'label': 'Fraud', 'value': fraud_count, 'percentage': round(fraud_count / total * 100, 2)},
        {'label': 'Legitimate', 'value': legit_count, 'percentage': round(legit_count / total * 100, 2)},
    ]

    details = [
        _detail('Fraud volume', f"{fraud_count:,}"),
        _detail('Legitimate volume', f"{legit_count:,}"),
        _detail('Detection rate', _format_percent(fraud_count / total * 100)),
    ]

    return {
        'title': 'Fraud vs Legitimate Distribution',
        'type': 'donut',
        'data': data,
        'details': details,
        'description': 'Overall split of detected fraud versus legitimate transactions.',
    }


def _build_monthly_trend_plot(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    if 'timestamp' not in df.columns:
        return None

    timestamps = pd.to_datetime(df['timestamp'], errors='coerce')
    tmp = df.copy()
    tmp['timestamp'] = timestamps
    tmp = tmp.dropna(subset=['timestamp'])
    if tmp.empty:
        return None

    tmp['month'] = tmp['timestamp'].dt.to_period('M').astype(str)
    grouped = tmp.groupby(['month', 'is_fraud']).size().unstack(fill_value=0).sort_index()

    data = []
    for month, row in grouped.iterrows():
        data.append({
            'month': month,
            'fraud': int(row.get(1, 0)),
            'legitimate': int(row.get(0, 0)),
        })

    if not data:
        return None

    peak = max(data, key=lambda item: item['fraud'])
    details = [
        _detail('Peak fraud month', f"{peak['month']} ({peak['fraud']:,} cases)"),
        _detail('Monitored months', str(len(data))),
    ]

    return {
        'title': 'Monthly Fraud Trend',
        'type': 'line_trend',
        'data': data,
        'details': details,
        'description': 'Rolling fraud vs legitimate counts grouped by calendar month.',
    }


def _build_correlation_heatmap_plot(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    candidate_columns = [
        'amount',
        'fraud_probability',
        'account_balance',
        'balanceafter',
        'avgdailybalance',
        'amount_deviation',
        'amount_to_balance_ratio',
        'amount_zscore',
    ]
    numeric_columns = [col for col in candidate_columns if col in df.columns]
    if len(numeric_columns) < 2:
        return None

    corr = df[numeric_columns].corr().replace([np.inf, -np.inf], np.nan).fillna(0)
    if corr.empty:
        return None

    data = [
        {'x': x_label, 'y': y_label, 'value': float(corr.loc[y_label, x_label])}
        for y_label in numeric_columns
        for x_label in numeric_columns
    ]

    details = [
        _detail('Strongest positive', _describe_correlation_pair(corr, positive=True)),
        _detail('Strongest negative', _describe_correlation_pair(corr, positive=False)),
    ]

    return {
        'title': 'Feature Correlation Heatmap',
        'type': 'heatmap',
        'xLabels': numeric_columns,
        'yLabels': numeric_columns,
        'data': data,
        'details': details,
        'description': 'Correlation matrix for high-signal numeric features.',
    }


def _build_geo_scatter_plot(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    city_col = _first_present_column(df, [
        'transaction_city',
        'transaction_location_city',
        'transactionlocationcity',
        'transactionlocation_city',
        'transaction_locationcity',
    ])
    country_col = _first_present_column(df, [
        'transaction_country',
        'transaction_location_country',
        'transactionlocationcountry',
        'login_country',
        'home_country',
    ])

    if not city_col:
        return None

    subset = df[df['is_fraud'] == 1]
    if subset.empty:
        subset = df

    group_cols = [city_col]
    if country_col:
        group_cols.append(country_col)

    grouped = subset.groupby(group_cols).size().reset_index(name='count').sort_values('count', ascending=False).head(50)
    if grouped.empty:
        return None

    geo_points = []
    for _, row in grouped.iterrows():
        city = str(row.get(city_col) or 'Unknown City')
        country = str(row.get(country_col) or 'Unknown') if country_col else 'Unknown'
        lat, lng = _pseudo_coordinates(city, country)
        geo_points.append({
            'city': city,
            'country': country,
            'lat': lat,
            'lng': lng,
            'count': int(row['count']),
        })

    details = [
        _detail('Hotspots tracked', str(len(geo_points))),
        _detail('Top hotspot', f"{geo_points[0]['city']} ({geo_points[0]['count']:,})"),
    ]

    return {
        'title': 'Geo Hotspots',
        'type': 'geo_scatter',
        'data': geo_points,
        'details': details,
        'description': 'Synthetic coordinates highlighting where risky transactions originate.',
    }


def _build_fraud_reason_bar_plot(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    if 'fraud_reason' not in df.columns:
        return None

    fraud_df = df[df['is_fraud'] == 1]
    if fraud_df.empty:
        return None

    counts = Counter()
    for reason in fraud_df['fraud_reason']:
        counts[_normalize_fraud_reason(reason)] += 1

    data = [
        {'label': label, 'value': int(counts[label])}
        for label in STANDARD_FRAUD_REASONS
        if counts.get(label)
    ]
    if not data:
        return None

    data.sort(key=lambda item: item['value'], reverse=True)
    total = sum(item['value'] for item in data)
    details = [
        _detail('Top reason', f"{data[0]['label']} ({data[0]['value']:,})"),
        _detail('Distinct reasons', str(len(data))),
        _detail('Fraud cases analyzed', f"{total:,}"),
    ]

    return {
        'title': 'Fraud Reasons Breakdown',
        'type': 'bar_reasons',
        'data': data[:15],
        'details': details,
        'description': 'Standardized narratives: login abuse, velocity spikes, mule behavior, etc.',
    }


def _build_sankey_plot(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    type_col = _first_present_column(df, ['transaction_type', 'type'])
    merchant_col = _first_present_column(df, ['merchant'])
    gender_col = _first_present_column(df, ['gender'])

    if not type_col or not merchant_col or not gender_col or 'is_fraud' not in df.columns:
        return None

    sankey_df = df[[type_col, merchant_col, 'is_fraud', gender_col]].copy()
    if sankey_df.empty:
        return None

    sankey_df[type_col] = sankey_df[type_col].fillna('Unknown Type')
    sankey_df[merchant_col] = sankey_df[merchant_col].fillna('Unknown Merchant')
    sankey_df[gender_col] = sankey_df[gender_col].fillna('Unknown')
    sankey_df['status'] = sankey_df['is_fraud'].apply(lambda value: 'Fraud' if value == 1 else 'Legitimate')

    top_types = sankey_df[type_col].value_counts().head(6).index
    top_merchants = sankey_df[merchant_col].value_counts().head(8).index
    sankey_df.loc[~sankey_df[type_col].isin(top_types), type_col] = 'Other Types'
    sankey_df.loc[~sankey_df[merchant_col].isin(top_merchants), merchant_col] = 'Other Merchants'

    nodes: List[str] = []
    node_index: Dict[str, int] = {}

    def add_node(label: str) -> int:
        if label not in node_index:
            node_index[label] = len(nodes)
            nodes.append(label)
        return node_index[label]

    links: List[Dict[str, Any]] = []

    for _, row in sankey_df.groupby([type_col, merchant_col]).size().reset_index(name='value').iterrows():
        links.append({
            'source': add_node(row[type_col]),
            'target': add_node(row[merchant_col]),
            'value': int(row['value']),
        })

    for _, row in sankey_df.groupby([merchant_col, 'status']).size().reset_index(name='value').iterrows():
        links.append({
            'source': add_node(row[merchant_col]),
            'target': add_node(row['status']),
            'value': int(row['value']),
        })

    for _, row in sankey_df.groupby(['status', gender_col]).size().reset_index(name='value').iterrows():
        links.append({
            'source': add_node(row['status']),
            'target': add_node(row[gender_col]),
            'value': int(row['value']),
        })

    if not links:
        return None

    details = [
        _detail('Type nodes', str(len(set(sankey_df[type_col])))),
        _detail('Merchant nodes', str(len(set(sankey_df[merchant_col])))),
        _detail('Gender nodes', str(len(set(sankey_df[gender_col])))),
    ]

    return {
        'title': 'Flow: Type ? Merchant ? Status ? Gender',
        'type': 'sankey',
        'data': {
            'nodes': [{'name': label} for label in nodes],
            'links': links,
        },
        'details': details,
        'description': 'Shows how risky traffic moves from transaction types through merchants to outcomes and genders.',
    }


def _first_present_column(df: pd.DataFrame, candidates: Sequence[str]) -> Optional[str]:
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    return None


def _pseudo_coordinates(city: str, country: str) -> Tuple[float, float]:
    '''Derive deterministic pseudo coordinates so the UI can plot fictional cities.'''
    key = f"{city}|{country}".encode('utf-8')
    digest = hashlib.sha256(key).hexdigest()
    lat_seed = int(digest[:8], 16)
    lng_seed = int(digest[8:16], 16)
    lat = (lat_seed / 0xFFFFFFFF) * 180 - 90
    lng = (lng_seed / 0xFFFFFFFF) * 360 - 180
    return round(lat, 2), round(lng, 2)


def _describe_correlation_pair(corr: pd.DataFrame, positive: bool) -> str:
    mask = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
    stacked = mask.stack()
    if stacked.empty:
        return 'N/A'

    idx = stacked.idxmax() if positive else stacked.idxmin()
    value = float(corr.loc[idx])
    descriptor = 'Positive' if positive else 'Negative'
    return f"{descriptor}: {idx[0]} & {idx[1]} ({value:.2f})"


def _normalize_fraud_reason(value: Any) -> str:
    if not value:
        return OTHER_FRAUD_LABEL

    text = str(value).strip()
    for reason in STANDARD_FRAUD_REASONS:
        if reason.lower() in text.lower():
            return reason

    if text == LEGITIMATE_LABEL:
        return LEGITIMATE_LABEL

    return OTHER_FRAUD_LABEL

def _analyze_fraud_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze patterns in fraudulent transactions."""
    fraud_df = df[df['is_fraud'] == 1]

    if len(fraud_df) == 0:
        return {
            'message': 'No fraudulent transactions detected',
            'patterns': []
        }

    patterns = []

    # High-value fraud pattern
    high_value_threshold = fraud_df['amount'].quantile(0.75)
    high_value_fraud = fraud_df[fraud_df['amount'] >= high_value_threshold]
    if len(high_value_fraud) > 0:
        patterns.append({
            'type': 'high_value_transactions',
            'count': int(len(high_value_fraud)),
            'total_amount': float(high_value_fraud['amount'].sum()),
            'description': f"{len(high_value_fraud)} high-value fraud transactions detected (>${high_value_threshold:.2f})"
        })

    # Time-based patterns
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        fraud_df_time = fraud_df.dropna(subset=['timestamp'])

        if len(fraud_df_time) > 0:
            # Night-time fraud
            night_fraud = fraud_df_time[
                (fraud_df_time['timestamp'].dt.hour < 6) |
                (fraud_df_time['timestamp'].dt.hour > 22)
            ]
            if len(night_fraud) > 0:
                patterns.append({
                    'type': 'night_time_fraud',
                    'count': int(len(night_fraud)),
                    'description': f"{len(night_fraud)} fraudulent transactions during night hours (10 PM - 6 AM)"
                })

            # Weekend fraud
            weekend_fraud = fraud_df_time[fraud_df_time['timestamp'].dt.dayofweek >= 5]
            if len(weekend_fraud) > 0:
                patterns.append({
                    'type': 'weekend_fraud',
                    'count': int(len(weekend_fraud)),
                    'description': f"{len(weekend_fraud)} fraudulent transactions during weekends"
                })

    # Category patterns
    if 'category' in df.columns:
        fraud_categories = fraud_df['category'].value_counts()
        if len(fraud_categories) > 0:
            top_category = fraud_categories.index[0]
            patterns.append({
                'type': 'category_concentration',
                'category': top_category,
                'count': int(fraud_categories.iloc[0]),
                'description': f"Most fraud in '{top_category}' category ({fraud_categories.iloc[0]} cases)"
            })

    # Fraud type breakdown patterns
    if 'fraud_type' in fraud_df.columns:
        fraud_types = fraud_df['fraud_type'].value_counts()
        if len(fraud_types) > 0:
            leading_type = fraud_types.index[0]
            patterns.append({
                'type': 'fraud_type_distribution',
                'fraud_type': leading_type,
                'count': int(fraud_types.iloc[0]),
                'description': f"'{leading_type.replace('_', ' ').title()}' is the top detected fraud pattern ({fraud_types.iloc[0]} cases)"
            })

    return {
        'total_patterns_detected': len(patterns),
        'patterns': patterns
    }


def _generate_recommendations(df: pd.DataFrame, analysis_result: Dict) -> List[str]:
    """Generate actionable recommendations based on analysis."""
    recommendations: List[str] = []

    fraud_percentage = analysis_result.get('fraud_percentage', 0)

    if fraud_percentage > 20:
        recommendations.append("[High Alert] Over 20% of transactions are fraudulent. Escalate to manual review immediately.")
    elif fraud_percentage > 10:
        recommendations.append("[Medium Alert] 10–20% fraud rate detected. Increase monitoring and tighten controls.")
    elif fraud_percentage > 5:
        recommendations.append("[Low Alert] 5–10% of transactions flagged. Continue monitoring and validate model output.")
    else:
        recommendations.append("[Info] Fraud rate is within acceptable limits (<5%).")

    fraud_df = df[df['is_fraud'] == 1]

    if len(fraud_df) > 0:
        avg_fraud = fraud_df['amount'].mean()
        legit_df = df[df['is_fraud'] == 0]
        avg_legit = legit_df['amount'].mean() if len(legit_df) > 0 else 0

        if avg_legit and avg_fraud > avg_legit * 2:
            recommendations.append(
                f"[Amount Risk] Fraudulent transactions average ${avg_fraud:.2f} vs ${avg_legit:.2f}. Apply additional checks to high-value payouts."
            )

    if 'timestamp' in df.columns and len(fraud_df) > 0:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        fraud_df_time = fraud_df.dropna(subset=['timestamp'])

        if len(fraud_df_time) > 0:
            night_mask = (fraud_df_time['timestamp'].dt.hour < 6) | (fraud_df_time['timestamp'].dt.hour > 22)
            night_fraud_pct = night_mask.mean() * 100
            if night_fraud_pct > 30:
                recommendations.append(
                    f"[Timing Risk] {night_fraud_pct:.1f}% of fraud occurs late night. Require step-up authentication after 10 PM."
                )

    if 'category' in df.columns and len(fraud_df) > 0:
        top_categories = fraud_df['category'].value_counts()
        if not top_categories.empty:
            top_fraud_cat = top_categories.index[0]
            recommendations.append(
                f"[Category Risk] '{top_fraud_cat}' is the most targeted category. Apply stricter limits or approvals there."
            )

    avg_prob = analysis_result.get('average_fraud_probability', 0)
    if avg_prob > 0.7:
        recommendations.append(
            "[Model Insight] ML model shows high confidence (>0.70 average probability). Capture analyst feedback to keep calibration fresh."
        )

    return recommendations




def _apply_filters(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
    """Apply filters to the dataframe."""
    filtered_df = df.copy()
    
    # Amount filters
    if filters.get('amount_min') is not None:
        try:
            amount_min = float(filters['amount_min'])
            filtered_df = filtered_df[filtered_df['amount'] >= amount_min]
        except (ValueError, TypeError):
            pass
    
    if filters.get('amount_max') is not None:
        try:
            amount_max = float(filters['amount_max'])
            filtered_df = filtered_df[filtered_df['amount'] <= amount_max]
        except (ValueError, TypeError):
            pass
    
    # Fraud probability filters
    if filters.get('fraud_probability_min') is not None:
        try:
            prob_min = float(filters['fraud_probability_min'])
            filtered_df = filtered_df[filtered_df['fraud_probability'] >= prob_min]
        except (ValueError, TypeError):
            pass
    
    if filters.get('fraud_probability_max') is not None:
        try:
            prob_max = float(filters['fraud_probability_max'])
            filtered_df = filtered_df[filtered_df['fraud_probability'] <= prob_max]
        except (ValueError, TypeError):
            pass
    
    # Category filter
    if filters.get('category') and filters['category'].strip():
        category_filter = filters['category'].strip().lower()
        if 'category' in filtered_df.columns:
            filtered_df = filtered_df[
                filtered_df['category'].astype(str).str.lower().str.contains(category_filter, na=False)
            ]
    
    # Hour of day filter (handles wrapping around midnight)
    if 'timestamp' in filtered_df.columns:
        filtered_df['timestamp'] = pd.to_datetime(filtered_df['timestamp'], errors='coerce')
        
        hour_start = filters.get('hour_of_day_start')
        hour_end = filters.get('hour_of_day_end')
        
        if hour_start is not None or hour_end is not None:
            filtered_df['hour'] = filtered_df['timestamp'].dt.hour
            start = int(hour_start) if hour_start is not None else 0
            end = int(hour_end) if hour_end is not None else 23
            
            # Handle wrapping around midnight (e.g., 22 to 06)
            if start > end:
                # Range wraps around midnight (e.g., 22 to 06 means 22, 23, 0, 1, 2, 3, 4, 5, 6)
                filtered_df = filtered_df[
                    (filtered_df['hour'] >= start) | (filtered_df['hour'] <= end)
                ]
            else:
                # Normal range (e.g., 9 to 17)
                filtered_df = filtered_df[
                    (filtered_df['hour'] >= start) & (filtered_df['hour'] <= end)
                ]
            filtered_df = filtered_df.drop(columns=['hour'])
    
    # Fraud/Legitimate only filters
    if filters.get('fraud_only'):
        filtered_df = filtered_df[filtered_df['is_fraud'] == 1]
    
    if filters.get('legitimate_only'):
        filtered_df = filtered_df[filtered_df['is_fraud'] == 0]
    
    return filtered_df


def _get_top_fraud_cases(df: pd.DataFrame, top_n: int = 10) -> List[Dict[str, Any]]:
    """Get top fraud cases by probability."""
    fraud_df = df[df['is_fraud'] == 1].copy()

    if len(fraud_df) == 0:
        return []

    fraud_df = fraud_df.sort_values('fraud_probability', ascending=False).head(top_n)

    top_cases = []
    for _, row in fraud_df.iterrows():
        case = {
            'transaction_id': row.get('transaction_id', 'N/A'),
            'amount': float(row['amount']),
            'fraud_probability': float(row['fraud_probability']),
            'reason': row.get('fraud_reason', 'Unknown'),
            'merchant': row.get('merchant', 'N/A'),
            'category': row.get('category', 'N/A')
        }

        if 'timestamp' in row and pd.notna(row['timestamp']):
            case['timestamp'] = pd.to_datetime(row['timestamp']).isoformat()

        top_cases.append(case)

    return top_cases
