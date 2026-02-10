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
            - date_start: Start date (e.g., '2023-01-01')
            - date_end: End date (e.g., '2023-03-31')
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

    # Normalize city and country names BEFORE grouping to combine duplicates
    subset = subset.copy()
    subset['normalized_city'] = subset[city_col].fillna('Unknown City').astype(str).str.strip().str.title()
    if country_col:
        subset['normalized_country'] = subset[country_col].fillna('Unknown').astype(str).str.strip().str.title()
        group_cols = ['normalized_city', 'normalized_country']
    else:
        subset['normalized_country'] = 'Unknown'
        group_cols = ['normalized_city']

    grouped = subset.groupby(group_cols).size().reset_index(name='count').sort_values('count', ascending=False).head(50)
    if grouped.empty:
        return None

    geo_points = []
    for _, row in grouped.iterrows():
        city = str(row.get('normalized_city', 'Unknown City'))
        country = str(row.get('normalized_country', 'Unknown'))
        # Try exact city-country match first
        coords = _pseudo_coordinates(city, country, allow_fallback=False)

        # If no match, try to find coordinates using just the city name with any country
        if not coords:
            coords = _find_city_coordinates_fuzzy(city)

        if not coords:
            # Skip cities without known coordinates to ensure stable map
            logger.debug("Skipping geo hotspot with unknown coordinates", extra={'city': city, 'country': country})
            continue
        lat, lng = coords
        geo_points.append({
            'city': city,
            'country': country,
            'lat': lat,
            'lng': lng,
            'count': int(row['count']),
        })

    if not geo_points:
        logger.warning("No geo hotspots with known coordinates")
        return None

    # Sort geo_points by count in descending order (highest first)
    geo_points.sort(key=lambda x: x['count'], reverse=True)

    details = [
        _detail('Hotspots tracked', str(len(geo_points))),
        _detail('Top hotspot', f"{geo_points[0]['city']} ({geo_points[0]['count']:,})"),
    ]

    return {
        'title': 'Geo Hotspots',
        'type': 'geo_scatter',
        'data': geo_points,
        'details': details,
        'description': 'Real geographic coordinates showing where risky transactions originate.',
    }


def _build_fraud_reason_bar_plot(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    if 'fraud_reason' not in df.columns:
        return None

    fraud_df = df[df['is_fraud'] == 1]
    if fraud_df.empty:
        return None

    # Count all fraud reasons after normalization
    counts = Counter()
    for reason in fraud_df['fraud_reason']:
        normalized = _normalize_fraud_reason(reason)
        counts[normalized] += 1

    # Get all fraud types sorted by count
    all_fraud_types = counts.most_common()

    if not all_fraud_types:
        return None

    # Take top 5 (or all if less than 5)
    top_n = min(5, len(all_fraud_types))
    top_fraud_types = all_fraud_types[:top_n]

    # Build data array
    data = [
        {'label': label, 'value': int(value)}
        for label, value in top_fraud_types
    ]

    # Sort by value descending
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
        'data': data,
        'details': details,
        'description': 'Standardized narratives: login abuse, velocity spikes, mule behavior, etc.',
    }


def _build_sankey_plot(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    type_col = _first_present_column(df, ['transaction_type', 'type'])
    merchant_col = _first_present_column(df, ['merchant'])
    gender_col = _first_present_column(df, ['gender'])

    if not type_col or not merchant_col or not gender_col or 'is_fraud' not in df.columns:
        return None

    sankey_df = df[[gender_col, type_col, merchant_col, 'is_fraud']].copy()
    if sankey_df.empty:
        return None

    sankey_df[gender_col] = sankey_df[gender_col].fillna('Unknown Gender')
    sankey_df[type_col] = sankey_df[type_col].fillna('Unknown Type')
    sankey_df[merchant_col] = sankey_df[merchant_col].fillna('Unknown Merchant')
    sankey_df['status'] = sankey_df['is_fraud'].apply(lambda value: 'Fraud' if value == 1 else 'Legitimate')

    top_types = sankey_df[type_col].value_counts().head(6).index
    top_merchants = sankey_df[merchant_col].value_counts().head(8).index
    sankey_df.loc[~sankey_df[type_col].isin(top_types), type_col] = 'Other Types'
    sankey_df.loc[~sankey_df[merchant_col].isin(top_merchants), merchant_col] = 'Other Merchants'

    nodes: List[str] = []
    node_index: Dict[str, int] = {}

    def add_node(label: Any) -> int:
        """Ensure node exists and return its index."""
        label_str = str(label)
        if label_str not in node_index:
            node_index[label_str] = len(nodes)
            nodes.append(label_str)
        return node_index[label_str]

    def node_name(label: Any) -> str:
        """Return canonical node name after registering it."""
        add_node(label)
        return str(label)

    links: List[Dict[str, Any]] = []

    # Color palette for links - Gender-based colors
    link_colors = {
        'Male': '#3b82f6',      # Blue
        'Female': '#ec4899',    # Pink
        'M': '#3b82f6',         # Blue
        'F': '#ec4899',         # Pink
        'Unknown Gender': '#94a3b8',  # Gray
        'default': '#10b981'    # Green
    }

    # Flow: Gender -> Type -> Merchant -> Status
    for _, row in sankey_df.groupby([gender_col, type_col]).size().reset_index(name='value').iterrows():
        source_label = node_name(row[gender_col])
        target_label = node_name(row[type_col])
        color = link_colors.get(str(row[gender_col]), link_colors['default'])
        links.append({
            'source': source_label,
            'target': target_label,
            'value': int(row['value']),
            'color': color
        })

    for _, row in sankey_df.groupby([type_col, merchant_col]).size().reset_index(name='value').iterrows():
        source_label = node_name(row[type_col])
        target_label = node_name(row[merchant_col])
        links.append({
            'source': source_label,
            'target': target_label,
            'value': int(row['value']),
            'color': '#8b5cf6'  # Purple for middle flows
        })

    for _, row in sankey_df.groupby([merchant_col, 'status']).size().reset_index(name='value').iterrows():
        source_label = node_name(row[merchant_col])
        target_label = node_name(row['status'])
        links.append({
            'source': source_label,
            'target': target_label,
            'value': int(row['value']),
            'color': '#ef4444' if row['status'] == 'Fraud' else '#10b981'  # Red for fraud, green for legitimate
        })

    if not links:
        return None

    details = [
        _detail('Gender nodes', str(len(set(sankey_df[gender_col])))),
        _detail('Type nodes', str(len(set(sankey_df[type_col])))),
        _detail('Merchant nodes', str(len(set(sankey_df[merchant_col])))),
    ]

    return {
        'title': 'Sankey Plot Flow Based on Gender',
        'type': 'sankey',
        'data': {
            'nodes': [{'name': label} for label in nodes],
            'links': links,
        },
        'details': details,
        'description': 'Shows transaction flow from gender through transaction types and merchants to fraud status.',
    }


def _first_present_column(df: pd.DataFrame, candidates: Sequence[str]) -> Optional[str]:
    """
    Return the first column present in the dataframe, matching candidates case-insensitively.
    """
    if df is None or df.empty:
        return None

    normalized = {col.lower(): col for col in df.columns}
    for candidate in candidates:
        actual = normalized.get(candidate.lower())
        if actual:
            return actual
    return None


def _find_city_coordinates_fuzzy(city: str) -> Optional[Tuple[float, float]]:
    """
    Try to find coordinates for a city by searching through known cities,
    ignoring the country. This helps with mismatched city-country pairs.

    Args:
        city: City name to search for

    Returns:
        Tuple of (latitude, longitude) if found, None otherwise
    """
    city_clean = (city or 'Unknown').strip().lower()

    # City aliases for normalization
    city_aliases = {
        'new york city': 'new york',
        'nyc': 'new york',
        'san fran': 'san francisco',
        'st louis': 'st. louis',
        'saint louis': 'st. louis',
        'washington dc': 'washington',
        'washington d.c.': 'washington',
        'la': 'los angeles'
    }
    city_clean = city_aliases.get(city_clean, city_clean)

    # Build the known_cities_map inline to search it
    # (We could also move this to a module-level constant for efficiency)
    known_cities = _get_known_cities_map()

    # Search for the city in any country
    for (known_city, known_country), coords in known_cities.items():
        if known_city == city_clean:
            logger.debug(f"Found fuzzy match for city '{city}' -> '{known_city}, {known_country}'")
            return coords

    return None


def _get_known_cities_map() -> dict:
    """
    Returns the known cities mapping.
    Extracted as a separate function to avoid duplication.
    """
    return {
        # North America - USA
        ('new york', 'usa'): (40.7128, -74.0060),
        ('new york', 'united states'): (40.7128, -74.0060),
        ('los angeles', 'usa'): (34.0522, -118.2437),
        ('los angeles', 'united states'): (34.0522, -118.2437),
        ('chicago', 'usa'): (41.8781, -87.6298),
        ('chicago', 'united states'): (41.8781, -87.6298),
        ('san francisco', 'usa'): (37.7749, -122.4194),
        ('san francisco', 'united states'): (37.7749, -122.4194),
        ('houston', 'usa'): (29.7604, -95.3698),
        ('houston', 'united states'): (29.7604, -95.3698),
        ('miami', 'usa'): (25.7617, -80.1918),
        ('miami', 'united states'): (25.7617, -80.1918),
        ('boston', 'usa'): (42.3601, -71.0589),
        ('boston', 'united states'): (42.3601, -71.0589),
        ('seattle', 'usa'): (47.6062, -122.3321),
        ('seattle', 'united states'): (47.6062, -122.3321),
        ('atlanta', 'usa'): (33.7490, -84.3880),
        ('atlanta', 'united states'): (33.7490, -84.3880),
        ('dallas', 'usa'): (32.7767, -96.7970),
        ('dallas', 'united states'): (32.7767, -96.7970),
        ('phoenix', 'usa'): (33.4484, -112.0740),
        ('phoenix', 'united states'): (33.4484, -112.0740),
        ('philadelphia', 'usa'): (39.9526, -75.1652),
        ('philadelphia', 'united states'): (39.9526, -75.1652),
        ('san diego', 'usa'): (32.7157, -117.1611),
        ('san diego', 'united states'): (32.7157, -117.1611),
        ('san antonio', 'usa'): (29.4241, -98.4936),
        ('san antonio', 'united states'): (29.4241, -98.4936),
        ('austin', 'usa'): (30.2672, -97.7431),
        ('austin', 'united states'): (30.2672, -97.7431),
        ('jacksonville', 'usa'): (30.3322, -81.6557),
        ('jacksonville', 'united states'): (30.3322, -81.6557),
        ('columbus', 'usa'): (39.9612, -82.9988),
        ('columbus', 'united states'): (39.9612, -82.9988),
        ('indianapolis', 'usa'): (39.7684, -86.1581),
        ('indianapolis', 'united states'): (39.7684, -86.1581),
        ('san jose', 'usa'): (37.3382, -121.8863),
        ('san jose', 'united states'): (37.3382, -121.8863),
        ('denver', 'usa'): (39.7392, -104.9903),
        ('denver', 'united states'): (39.7392, -104.9903),
        ('las vegas', 'usa'): (36.1699, -115.1398),
        ('las vegas', 'united states'): (36.1699, -115.1398),
        ('charlotte', 'usa'): (35.2271, -80.8431),
        ('charlotte', 'united states'): (35.2271, -80.8431),
        ('washington', 'usa'): (38.9072, -77.0369),
        ('washington', 'united states'): (38.9072, -77.0369),
        ('st. louis', 'usa'): (38.6270, -90.1994),
        ('st. louis', 'united states'): (38.6270, -90.1994),

        # North America - Canada
        ('toronto', 'canada'): (43.6532, -79.3832),
        ('vancouver', 'canada'): (49.2827, -123.1207),
        ('montreal', 'canada'): (45.5017, -73.5673),

        # North America - Mexico
        ('mexico city', 'mexico'): (19.4326, -99.1332),
        ('guadalajara', 'mexico'): (20.6597, -103.3496),
        ('monterrey', 'mexico'): (25.6866, -100.3161),

        # South America
        ('sao paulo', 'brazil'): (-23.5505, -46.6333),
        ('são paulo', 'brazil'): (-23.5505, -46.6333),
        ('rio de janeiro', 'brazil'): (-22.9068, -43.1729),
        ('brasilia', 'brazil'): (-15.8267, -47.9218),
        ('buenos aires', 'argentina'): (-34.6037, -58.3816),
        ('santiago', 'chile'): (-33.4489, -70.6693),
        ('lima', 'peru'): (-12.0464, -77.0428),
        ('bogota', 'colombia'): (4.7110, -74.0721),
        ('caracas', 'venezuela'): (10.4806, -66.9036),

        # Europe - UK
        ('london', 'uk'): (51.5074, -0.1278),
        ('london', 'united kingdom'): (51.5074, -0.1278),
        ('manchester', 'uk'): (53.4808, -2.2426),
        ('manchester', 'united kingdom'): (53.4808, -2.2426),

        # Europe - Western
        ('paris', 'france'): (48.8566, 2.3522),
        ('berlin', 'germany'): (52.5200, 13.4050),
        ('madrid', 'spain'): (40.4168, -3.7038),
        ('rome', 'italy'): (41.9028, 12.4964),
        ('amsterdam', 'netherlands'): (52.3676, 4.9041),
        ('brussels', 'belgium'): (50.8503, 4.3517),
        ('zurich', 'switzerland'): (47.3769, 8.5417),
        ('vienna', 'austria'): (48.2082, 16.3738),
        ('barcelona', 'spain'): (41.3851, 2.1734),
        ('milan', 'italy'): (45.4642, 9.1900),

        # Europe - Eastern
        ('moscow', 'russia'): (55.7558, 37.6173),
        ('warsaw', 'poland'): (52.2297, 21.0122),
        ('prague', 'czech republic'): (50.0755, 14.4378),
        ('budapest', 'hungary'): (47.4979, 19.0402),

        # Middle East
        ('dubai', 'uae'): (25.2048, 55.2708),
        ('dubai', 'united arab emirates'): (25.2048, 55.2708),
        ('abu dhabi', 'uae'): (24.4539, 54.3773),
        ('abu dhabi', 'united arab emirates'): (24.4539, 54.3773),
        ('riyadh', 'saudi arabia'): (24.7136, 46.6753),
        ('istanbul', 'turkey'): (41.0082, 28.9784),
        ('tel aviv', 'israel'): (32.0853, 34.7818),
        ('doha', 'qatar'): (25.2854, 51.5310),

        # Asia - East
        ('tokyo', 'japan'): (35.6762, 139.6503),
        ('beijing', 'china'): (39.9042, 116.4074),
        ('shanghai', 'china'): (31.2304, 121.4737),
        ('hong kong', 'china'): (22.3193, 114.1694),
        ('hong kong', 'hong kong'): (22.3193, 114.1694),
        ('seoul', 'south korea'): (37.5665, 126.9780),
        ('taipei', 'taiwan'): (25.0330, 121.5654),

        # Asia - South
        ('mumbai', 'india'): (19.0760, 72.8777),
        ('delhi', 'india'): (28.7041, 77.1025),
        ('bangalore', 'india'): (12.9716, 77.5946),
        ('chennai', 'india'): (13.0827, 80.2707),
        ('kolkata', 'india'): (22.5726, 88.3639),
        ('karachi', 'pakistan'): (24.8607, 67.0011),
        ('dhaka', 'bangladesh'): (23.8103, 90.4125),

        # Asia - Southeast
        ('singapore', 'singapore'): (1.3521, 103.8198),
        ('bangkok', 'thailand'): (13.7563, 100.5018),
        ('kuala lumpur', 'malaysia'): (3.1390, 101.6869),
        ('jakarta', 'indonesia'): (-6.2088, 106.8456),
        ('manila', 'philippines'): (14.5995, 120.9842),
        ('ho chi minh city', 'vietnam'): (10.8231, 106.6297),

        # Oceania
        ('sydney', 'australia'): (-33.8688, 151.2093),
        ('melbourne', 'australia'): (-37.8136, 144.9631),
        ('brisbane', 'australia'): (-27.4698, 153.0251),
        ('perth', 'australia'): (-31.9505, 115.8605),
        ('auckland', 'new zealand'): (-36.8485, 174.7633),
        ('wellington', 'new zealand'): (-41.2865, 174.7762),

        # Africa
        ('cairo', 'egypt'): (30.0444, 31.2357),
        ('lagos', 'nigeria'): (6.5244, 3.3792),
        ('johannesburg', 'south africa'): (-26.2041, 28.0473),
        ('cape town', 'south africa'): (-33.9249, 18.4241),
        ('nairobi', 'kenya'): (-1.2921, 36.8219),
        ('casablanca', 'morocco'): (33.5731, -7.5898),
    }


def _pseudo_coordinates(city: str, country: str, allow_fallback: bool = True) -> Optional[Tuple[float, float]]:
    '''
    Derive deterministic pseudo coordinates so the UI can plot cities.
    Uses a hash-based approach to generate consistent coordinates for the same city/country pair.
    '''
    # Get the known cities mapping
    known_cities_map = _get_known_cities_map()

    # Normalize names to handle variations
    country_aliases = {
        'united states': 'usa',
        'united states of america': 'usa',
        'us': 'usa',
        'america': 'usa',
        'united kingdom': 'uk',
        'great britain': 'uk',
        'britain': 'uk',
        'united arab emirates': 'uae',
        'czech republic': 'czechia',
    }
    city_aliases = {
        'new york city': 'new york',
        'nyc': 'new york',
        'san fran': 'san francisco',
        'st louis': 'st. louis',
        'saint louis': 'st. louis',
        'washington dc': 'washington',
        'washington d.c.': 'washington',
        'la': 'los angeles'
    }

    # Check if we have known coordinates (case-insensitive)
    city_clean = (city or 'Unknown').strip().lower()
    country_clean = (country or 'Unknown').strip().lower()

    # Apply country aliases for normalization
    country_clean = country_aliases.get(country_clean, country_clean)
    city_clean = city_aliases.get(city_clean, city_clean)

    key_tuple = (city_clean, country_clean)

    if key_tuple in known_cities_map:
        return known_cities_map[key_tuple]

    if not allow_fallback:
        return None

    # For unknown cities, generate pseudo coordinates with better distribution
    key = f"{city}|{country}".encode('utf-8')
    digest = hashlib.sha256(key).hexdigest()
    lat_seed = int(digest[:8], 16)
    lng_seed = int(digest[8:16], 16)

    # Generate coordinates with better clustering around populated areas
    # Avoid extreme polar regions and spread more realistically
    lat_raw = (lat_seed / 0xFFFFFFFF)
    lng_raw = (lng_seed / 0xFFFFFFFF)

    # Bias towards populated latitudes (-60 to 70) and spread longitude fully
    lat = (lat_raw * 130 - 60)  # Range from -60 to 70
    lng = (lng_raw * 360 - 180)  # Full range -180 to 180

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
        return 'Unusual amount'  # Default for unknown fraud reasons

    text = str(value).strip()

    # First try exact match with standard reasons (case-insensitive)
    for reason in STANDARD_FRAUD_REASONS:
        if reason.lower() == text.lower():
            return reason

    # Then try partial match for standard reasons
    for reason in STANDARD_FRAUD_REASONS:
        if reason.lower() in text.lower():
            return reason

    # Check for legitimate label
    if text == LEGITIMATE_LABEL:
        return LEGITIMATE_LABEL

    # Map common variations to standard reasons (order matters - more specific first)
    text_lower = text.lower()

    # Suspicious login / IP mismatch variations
    if 'ip' in text_lower or 'login' in text_lower or 'session' in text_lower:
        return 'Suspicious login'

    # Account takeover variations
    if 'takeover' in text_lower or 'hijack' in text_lower or 'suspected' in text_lower:
        return 'Account takeover'

    # Location-based variations (check before more general patterns)
    if 'location' in text_lower or 'geographical' in text_lower or 'geo' in text_lower or 'country' in text_lower or 'cross-border' in text_lower:
        return 'Unusual location'

    # Unusual device variations
    if 'device' in text_lower or 'new device' in text_lower:
        return 'Unusual device'

    # Velocity/rapid transaction variations
    if 'velocity' in text_lower or 'rapid' in text_lower or 'multiple' in text_lower or 'burst' in text_lower or 'spike' in text_lower:
        return 'Velocity abuse'

    # High-risk merchant / stolen card variations
    if 'stolen' in text_lower or 'compromised' in text_lower or 'card' in text_lower or 'merchant' in text_lower or 'high-risk' in text_lower or 'fraud merchant' in text_lower or 'known fraud' in text_lower:
        return 'High-risk merchant'

    # Unusual amount variations
    if 'amount' in text_lower or 'value' in text_lower or 'unusual' in text_lower:
        return 'Unusual amount'

    # New payee / wire transfer variations
    if 'payee' in text_lower or 'wire' in text_lower or 'transfer' in text_lower or 'beneficiary' in text_lower:
        return 'New payee spike'

    # Card-not-present variations
    if 'card-not-present' in text_lower or 'cnp' in text_lower or 'online' in text_lower or 'ecommerce' in text_lower or 'e-commerce' in text_lower:
        return 'Card-not-present risk'

    # Money mule variations
    if 'mule' in text_lower or 'layering' in text_lower:
        return 'Money mule pattern'

    # Structuring / smurfing variations
    if 'structuring' in text_lower or 'smurfing' in text_lower or 'structur' in text_lower:
        return 'Structuring / smurfing'

    # Round dollar variations
    if 'round' in text_lower or 'dollar' in text_lower:
        return 'Round-dollar pattern'

    # Night-time activity variations
    if 'night' in text_lower or 'late' in text_lower or 'timing' in text_lower or 'time' in text_lower:
        return 'Night-time activity'

    # If still no match, preserve the original label instead of defaulting
    # This ensures we show actual fraud types from the data
    return text


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
    """
    Generate actionable recommendations - REMOVED: Rule-based logic
    Recommendations should come from LLM/ML models only, not rule-based thresholds.
    This function now returns empty list - recommendations come from agent.generate_recommendations() instead.
    """
    # REMOVED: All rule-based recommendation logic
    # Recommendations are now generated by LLM via RealTimeAnalysisAgent.generate_recommendations()
    # This ensures pure ML/AI-based recommendations without rule-based fallbacks
    return []




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
    
    # Date filter
    if 'timestamp' in filtered_df.columns:
        filtered_df['timestamp'] = pd.to_datetime(filtered_df['timestamp'], errors='coerce')

        date_start = filters.get('date_start')
        date_end = filters.get('date_end')

        if date_start is not None or date_end is not None:
            start_ts = pd.to_datetime(date_start, errors='coerce') if date_start else None
            end_ts = pd.to_datetime(date_end, errors='coerce') if date_end else None

            mask = pd.Series(True, index=filtered_df.index)

            if start_ts is not None and not pd.isna(start_ts):
                start_boundary = start_ts.normalize()
                mask &= filtered_df['timestamp'].isna() | (filtered_df['timestamp'] >= start_boundary)

            if end_ts is not None and not pd.isna(end_ts):
                end_boundary = end_ts.normalize() + pd.Timedelta(days=1)
                mask &= filtered_df['timestamp'].isna() | (filtered_df['timestamp'] < end_boundary)

            filtered_df = filtered_df[mask]
    
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
