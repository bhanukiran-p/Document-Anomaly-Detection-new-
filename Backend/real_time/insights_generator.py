"""
Insights Generator for Transaction Analysis
Generates comprehensive analytics and visualizations
"""
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List
from datetime import datetime
import base64
from io import BytesIO

logger = logging.getLogger(__name__)

# Try to import matplotlib, but don't fail if not available
try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except ImportError:
    logger.warning("Matplotlib not available, plots will be skipped")
    PLOTTING_AVAILABLE = False

COLOR_CANVAS = '#0f172a'
COLOR_PANEL = '#111827'
COLOR_TEXT = '#f8fafc'
COLOR_MUTED = '#cbd5f5'
COLOR_GRID = '#1f2937'
COLOR_ACCENT = '#60a5fa'
COLOR_FRAUD = '#f97066'
COLOR_LEGIT = '#34d399'
COLOR_WARNING = '#fbbf24'

if PLOTTING_AVAILABLE:
    sns.set_theme(style="whitegrid")
    plt.rcParams.update({
        'axes.facecolor': COLOR_CANVAS,
        'figure.facecolor': COLOR_PANEL,
        'text.color': COLOR_TEXT,
        'axes.labelcolor': COLOR_MUTED,
        'xtick.color': COLOR_MUTED,
        'ytick.color': COLOR_MUTED,
        'grid.color': COLOR_GRID,
        'axes.edgecolor': COLOR_GRID,
        'font.size': 11,
    })


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

        # Generate plots if available (use filtered dataframe and updated analysis result)
        plots = []
        if PLOTTING_AVAILABLE:
            plots = _generate_plots(df, filtered_analysis_result)

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


def _style_chart(fig, axes):
    """Apply dark theme styling to matplotlib axes."""
    if not PLOTTING_AVAILABLE:
        return

    axes = axes if isinstance(axes, (list, tuple, np.ndarray)) else [axes]
    for ax in axes:
        ax.set_facecolor(COLOR_CANVAS)
        ax.tick_params(colors=COLOR_MUTED, labelcolor=COLOR_MUTED)
        ax.yaxis.label.set_color(COLOR_MUTED)
        ax.xaxis.label.set_color(COLOR_MUTED)
        ax.title.set_color(COLOR_TEXT)
        for spine in ax.spines.values():
            spine.set_color(COLOR_GRID)
    fig.patch.set_facecolor(COLOR_PANEL)


def _format_currency(value: float) -> str:
    try:
        return f"${value:,.2f}"
    except Exception:
        return "$0.00"


def _format_percent(value: float) -> str:
    return f"{value:.1f}%"


def _detail(label: str, value: str) -> Dict[str, str]:
    return {'label': label, 'value': value}


def _build_plot_payload(title: str, fig, plot_type: str, details: List[Dict[str, str]], description: str = None) -> Dict[str, Any]:
    payload = {
        'title': title,
        'image': _fig_to_base64(fig),
        'type': plot_type,
        'details': details or []
    }
    if description:
        payload['description'] = description
    return payload


def _generate_plots(df: pd.DataFrame, analysis_result: Dict) -> List[Dict[str, str]]:
    """Generate visualization plots as base64 encoded images."""
    plots = []

    if not PLOTTING_AVAILABLE:
        logger.warning("Matplotlib not available - cannot generate plots")
        return plots

    sns.set_style("whitegrid")
    logger.info("Starting plot generation with matplotlib")

    try:
        # Plot 1: Fraud vs Legitimate Distribution (Pie Chart)
        fig, ax = plt.subplots(figsize=(8, 6))
        counts = df['is_fraud'].value_counts()

        fraud_count = int(counts.get(1, 0))
        legit_count = int(counts.get(0, 0))
        total_count = fraud_count + legit_count

        plot_values = []
        plot_labels = []
        plot_colors = []

        if legit_count > 0:
            plot_values.append(legit_count)
            plot_labels.append('Legitimate')
            plot_colors.append(COLOR_LEGIT)

        if fraud_count > 0:
            plot_values.append(fraud_count)
            plot_labels.append('Fraud')
            plot_colors.append(COLOR_FRAUD)

        if plot_values:
            def _format_autopct(values):
                def inner(pct):
                    absolute = int(round(pct / 100.0 * sum(values)))
                    return f"{pct:.1f}%\n({absolute})"
                return inner

            wedges, texts, autotexts = ax.pie(
                plot_values,
                labels=plot_labels,
                autopct=_format_autopct(plot_values),
                colors=plot_colors,
                startangle=90,
                wedgeprops={'linewidth': 1, 'edgecolor': COLOR_PANEL}
            )
            for text in texts + autotexts:
                text.set_color(COLOR_TEXT)
            ax.set_title('Transaction Classification Distribution', fontsize=14, fontweight='bold')
            _style_chart(fig, ax)

            fraud_pct = (fraud_count / total_count * 100) if total_count else 0
            legit_pct = (legit_count / total_count * 100) if total_count else 0
            pie_details = [
                _detail('Fraud', f"{fraud_count:,} ({_format_percent(fraud_pct)})"),
                _detail('Legitimate', f"{legit_count:,} ({_format_percent(legit_pct)})"),
                _detail('Total Volume', f"{total_count:,}")
            ]
            plots.append(_build_plot_payload(
                'Fraud vs Legitimate Distribution',
                fig,
                'pie',
                pie_details,
                description="Overall balance between legitimate and fraudulent transactions"
            ))
        plt.close(fig)

        # Plot 2: Amount Distribution by Fraud Status (Box Plot / Histogram)
        fraud_amounts = df[df['is_fraud'] == 1]['amount']
        legit_amounts = df[df['is_fraud'] == 0]['amount']

        if len(fraud_amounts) > 0 and len(legit_amounts) > 0:
            fig, ax = plt.subplots(figsize=(10, 6))
            box_data = [legit_amounts, fraud_amounts]
            bp = ax.boxplot(box_data, labels=['Legitimate', 'Fraud'], patch_artist=True)
            bp['boxes'][0].set_facecolor(COLOR_LEGIT)
            bp['boxes'][1].set_facecolor(COLOR_FRAUD)
            ax.set_ylabel('Amount ($)', fontsize=12)
            ax.set_title('Transaction Amount Distribution by Status', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.25)
            _style_chart(fig, ax)

            details = [
                _detail('Median Legitimate', _format_currency(float(np.median(legit_amounts)))),
                _detail('Median Fraud', _format_currency(float(np.median(fraud_amounts)))),
                _detail('Fraud Max', _format_currency(float(np.max(fraud_amounts))))
            ]
            plots.append(_build_plot_payload(
                'Amount Distribution by Status',
                fig,
                'boxplot',
                details,
                description="Compares the spread and outliers of fraud vs legitimate transaction values"
            ))
            plt.close(fig)
        elif len(legit_amounts) > 0 or len(fraud_amounts) > 0:
            fig, ax = plt.subplots(figsize=(10, 6))
            amounts = legit_amounts if len(legit_amounts) > 0 else fraud_amounts
            label = 'Legitimate' if len(legit_amounts) > 0 else 'Fraud'
            color = COLOR_LEGIT if len(legit_amounts) > 0 else COLOR_FRAUD

            ax.hist(amounts, bins=30, color=color, edgecolor=COLOR_PANEL, alpha=0.85)
            ax.set_xlabel('Amount ($)', fontsize=12)
            ax.set_ylabel('Count', fontsize=12)
            ax.set_title(f'{label} Transaction Amount Distribution', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.25)
            _style_chart(fig, ax)

            median_amount = float(np.median(amounts))
            details = [
                _detail('Median Amount', _format_currency(median_amount)),
                _detail('Transactions', f"{len(amounts):,}"),
                _detail('Label', label)
            ]
            plots.append(_build_plot_payload(
                'Amount Distribution',
                fig,
                'histogram',
                details,
                description=f"Amount spread for {label.lower()} transactions"
            ))
            plt.close(fig)

        # Plot 3: Fraud Probability Distribution (Histogram)
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(df['fraud_probability'], bins=30, color=COLOR_ACCENT, edgecolor=COLOR_PANEL, alpha=0.85)
        ax.set_xlabel('Fraud Probability', fontsize=12)
        ax.set_ylabel('Number of Transactions', fontsize=12)
        ax.set_title('Fraud Probability Distribution', fontsize=14, fontweight='bold')
        ax.axvline(0.5, color=COLOR_WARNING, linestyle='--', linewidth=2, label='Threshold (0.5)')
        ax.legend(facecolor=COLOR_CANVAS, edgecolor=COLOR_GRID)
        ax.grid(True, alpha=0.25)
        _style_chart(fig, ax)

        avg_probability = float(df['fraud_probability'].mean())
        high_confidence = int((df['fraud_probability'] >= 0.8).sum())
        over_threshold = int((df['fraud_probability'] >= 0.5).sum())
        details = [
            _detail('Average Probability', f"{avg_probability:.2f}"),
            _detail('≥ 0.80 Signals', f"{high_confidence:,}"),
            _detail('≥ 0.50 Signals', f"{over_threshold:,}")
        ]
        plots.append(_build_plot_payload(
            'Fraud Probability Distribution',
            fig,
            'histogram',
            details,
            description="How confident the ML model is across all transactions"
        ))
        plt.close(fig)

        # Plot 4: Time-based analysis (if timestamp available)
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            df_with_time = df.dropna(subset=['timestamp'])

            if len(df_with_time) > 0:
                fig, ax = plt.subplots(figsize=(12, 6))

                fraud_by_hour = df_with_time[df_with_time['is_fraud'] == 1].groupby(
                    df_with_time['timestamp'].dt.hour
                ).size()
                legit_by_hour = df_with_time[df_with_time['is_fraud'] == 0].groupby(
                    df_with_time['timestamp'].dt.hour
                ).size()

                hours = range(24)
                fraud_counts = [int(fraud_by_hour.get(h, 0)) for h in hours]
                legit_counts = [int(legit_by_hour.get(h, 0)) for h in hours]

                x = np.arange(24)
                width = 0.35

                ax.bar(x - width/2, legit_counts, width, label='Legitimate', color=COLOR_LEGIT)
                ax.bar(x + width/2, fraud_counts, width, label='Fraud', color=COLOR_FRAUD)

                ax.set_xlabel('Hour of Day', fontsize=12)
                ax.set_ylabel('Number of Transactions', fontsize=12)
                ax.set_title('Transaction Pattern by Hour of Day', fontsize=14, fontweight='bold')
                ax.set_xticks(x)
                ax.legend(facecolor=COLOR_CANVAS, edgecolor=COLOR_GRID)
                ax.grid(True, alpha=0.25)
                _style_chart(fig, ax)

                if sum(fraud_counts) > 0:
                    peak_hour = int(hours[int(np.argmax(fraud_counts))])
                    peak_value = max(fraud_counts)
                else:
                    peak_hour = None
                    peak_value = 0
                weekend_fraud = df_with_time[
                    (df_with_time['timestamp'].dt.dayofweek >= 5) & (df_with_time['is_fraud'] == 1)
                ]
                weekend_pct = 0
                total_fraud_samples = df_with_time[df_with_time['is_fraud'] == 1].shape[0]
                if total_fraud_samples > 0:
                    weekend_pct = len(weekend_fraud) / total_fraud_samples * 100

                time_details = [
                    _detail('Peak Fraud Hour', f"{peak_hour:02d}:00" if peak_hour is not None else 'N/A'),
                    _detail('Peak Volume', f"{peak_value:,} cases"),
                    _detail('Weekend Fraud', _format_percent(weekend_pct))
                ]
                plots.append(_build_plot_payload(
                    'Hourly Transaction Patterns',
                    fig,
                    'bar',
                    time_details,
                    description="Identifies when fraudulent activity is most active throughout the day"
                ))
                plt.close(fig)

        # Plot 5: Category-based fraud analysis (if category available)
        if 'category' in df.columns:
            category_fraud = df.groupby('category')['is_fraud'].agg(['sum', 'count'])
            category_fraud['fraud_rate'] = (category_fraud['sum'] / category_fraud['count'] * 100)
            category_fraud = category_fraud.sort_values(['fraud_rate', 'count'], ascending=False).head(10)

            if len(category_fraud) > 0:
                fig, ax = plt.subplots(figsize=(12, 6))
                categories = category_fraud.index.tolist()
                fraud_rates = category_fraud['fraud_rate'].tolist()

                bars = ax.barh(categories, fraud_rates, color=COLOR_WARNING)
                ax.set_xlabel('Fraud Rate (%)', fontsize=12)
                ax.set_title('Top 10 Categories by Fraud Rate', fontsize=14, fontweight='bold')
                ax.grid(True, alpha=0.25, axis='x')
                _style_chart(fig, ax)

                for bar, rate in zip(bars, fraud_rates):
                    ax.text(
                        rate + 0.3,
                        bar.get_y() + bar.get_height() / 2,
                        f'{rate:.1f}%',
                        va='center',
                        color=COLOR_TEXT,
                        fontsize=10
                    )

                top_category = categories[0]
                top_rate = fraud_rates[0]
                details = [
                    _detail('Highest Risk Category', f"{top_category} ({top_rate:.1f}%)"),
                    _detail('Categories Reviewed', f"{len(categories)}"),
                    _detail('Total Fraud Cases', f"{int(category_fraud['sum'].sum()):,}")
                ]
                plots.append(_build_plot_payload(
                    'Fraud Rate by Category',
                    fig,
                    'horizontal_bar',
                    details,
                    description="Highlights categories with the highest fraud rates by percentage"
                ))
                plt.close(fig)

        # Plot 6: Amount vs Fraud Probability Scatter
        fig, ax = plt.subplots(figsize=(10, 6))
        fraud_mask = df['is_fraud'] == 1
        ax.scatter(
            df[~fraud_mask]['amount'],
            df[~fraud_mask]['fraud_probability'],
            c=COLOR_LEGIT,
            label='Legitimate',
            alpha=0.6,
            s=45,
            edgecolors='none'
        )
        ax.scatter(
            df[fraud_mask]['amount'],
            df[fraud_mask]['fraud_probability'],
            c=COLOR_FRAUD,
            label='Fraud',
            alpha=0.7,
            s=55,
            edgecolors='none'
        )
        ax.set_xlabel('Transaction Amount ($)', fontsize=12)
        ax.set_ylabel('Fraud Probability', fontsize=12)
        ax.set_title('Amount vs Fraud Probability', fontsize=14, fontweight='bold')
        ax.axhline(0.5, color=COLOR_WARNING, linestyle='--', linewidth=1.2, alpha=0.8)
        ax.legend(facecolor=COLOR_CANVAS, edgecolor=COLOR_GRID)
        ax.grid(True, alpha=0.2)
        _style_chart(fig, ax)

        correlation = df[['amount', 'fraud_probability']].corr().iloc[0, 1]
        high_risk_high_value = df[(df['fraud_probability'] > 0.7) & (df['amount'] > df['amount'].median())]
        scatter_details = [
            _detail('Correlation', f"{correlation:.2f}" if not np.isnan(correlation) else 'N/A'),
            _detail('High-Risk High-Value', f"{len(high_risk_high_value):,} cases"),
            _detail('Median Amount', _format_currency(float(df['amount'].median())))
        ]
        plots.append(_build_plot_payload(
            'Amount vs Fraud Probability',
            fig,
            'scatter',
            scatter_details,
            description="Shows how fraud probability shifts with transaction size"
        ))
        plt.close(fig)

        # Plot 7: Fraud type distribution
        if 'fraud_type' in df.columns and df['fraud_type'].nunique() > 0:
            fraud_type_counts = df[df['is_fraud'] == 1]['fraud_type'].value_counts()
            if len(fraud_type_counts) > 0:
                fig, ax = plt.subplots(figsize=(10, 6))
                bars = ax.bar(
                    [ft.replace('_', ' ').title() for ft in fraud_type_counts.index],
                    fraud_type_counts.values,
                    color=COLOR_FRAUD
                )
                ax.set_ylabel('Fraud Cases', fontsize=12)
                ax.set_title('Detected Fraud Types', fontsize=14, fontweight='bold')
                ax.set_xticks(range(len(fraud_type_counts.index)))
                ax.set_xticklabels(
                    [ft.replace('_', ' ').title() for ft in fraud_type_counts.index],
                    rotation=30,
                    ha='right'
                )
                ax.grid(True, alpha=0.2, axis='y')
                _style_chart(fig, ax)

                for bar, count in zip(bars, fraud_type_counts.values):
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 0.1,
                        str(int(count)),
                        ha='center',
                        va='bottom',
                        color=COLOR_TEXT,
                        fontsize=10
                    )

                type_details = [
                    _detail('Top Fraud Type', fraud_type_counts.index[0].replace('_', ' ').title()),
                    _detail('Unique Patterns', str(len(fraud_type_counts.index))),
                    _detail('Total Fraud Cases', f"{int(fraud_type_counts.sum()):,}")
                ]
                plots.append(_build_plot_payload(
                    'Fraud Type Distribution',
                    fig,
                    'bar',
                    type_details,
                    description="Breakdown of the most common fraud archetypes detected in this batch"
                ))
                plt.close(fig)

    except Exception as e:
        logger.error(f"Error generating plots: {e}", exc_info=True)

    logger.info(f"Generated {len(plots)} plots successfully")
    return plots


def _fig_to_base64(fig) -> str:
    """Convert matplotlib figure to base64 encoded string."""
    buffer = BytesIO()
    fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    buffer.close()
    return f"data:image/png;base64,{image_base64}"


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
    recommendations = []

    fraud_percentage = analysis_result.get('fraud_percentage', 0)

    if fraud_percentage > 20:
        recommendations.append("⚠️ HIGH ALERT: Over 20% of transactions are fraudulent. Immediate review of security measures recommended.")
    elif fraud_percentage > 10:
        recommendations.append("⚠️ MEDIUM ALERT: 10-20% fraud rate detected. Enhanced monitoring recommended.")
    elif fraud_percentage > 5:
        recommendations.append("⚠️ LOW ALERT: 5-10% fraud rate. Continue standard monitoring.")
    else:
        recommendations.append("✓ Fraud rate is within acceptable limits (<5%).")

    fraud_df = df[df['is_fraud'] == 1]

    # High-value fraud check
    if len(fraud_df) > 0:
        avg_fraud = fraud_df['amount'].mean()
        avg_legit = df[df['is_fraud'] == 0]['amount'].mean() if len(df[df['is_fraud'] == 0]) > 0 else 0

        if avg_fraud > avg_legit * 2:
            recommendations.append(f"💰 Fraudulent transactions have significantly higher average amounts (${avg_fraud:.2f} vs ${avg_legit:.2f}). Consider additional verification for high-value transactions.")

    # Time-based recommendations
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        fraud_df_time = fraud_df.dropna(subset=['timestamp'])

        if len(fraud_df_time) > 0:
            night_fraud_pct = len(fraud_df_time[
                (fraud_df_time['timestamp'].dt.hour < 6) |
                (fraud_df_time['timestamp'].dt.hour > 22)
            ]) / len(fraud_df_time) * 100

            if night_fraud_pct > 30:
                recommendations.append(f"🌙 {night_fraud_pct:.1f}% of fraud occurs during night hours. Consider enhanced monitoring or additional authentication during these hours.")

    # Category-based recommendations
    if 'category' in df.columns and len(fraud_df) > 0:
        fraud_cat_counts = fraud_df['category'].value_counts()
        if len(fraud_cat_counts) > 0:
            top_fraud_cat = fraud_cat_counts.index[0]
            recommendations.append(f"📊 '{top_fraud_cat}' category has the most fraud cases. Consider stricter controls for this category.")

    # Model performance
    avg_prob = analysis_result.get('average_fraud_probability', 0)
    if avg_prob > 0.7:
        recommendations.append("🤖 ML model shows high confidence in fraud detection. Continue collecting feedback to improve accuracy.")

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
