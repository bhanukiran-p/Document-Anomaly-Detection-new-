"""
Fraud Pattern Recommendation Engine
Provides targeted prevention strategies for each fraud type detected in real-time analysis
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class FraudRecommendationEngine:
    """
    Generate specific, actionable recommendations based on fraud patterns detected
    """

    # Fraud pattern prevention strategies mapping
    FRAUD_PREVENTION_STRATEGIES = {
        'Suspicious login': {
            'severity': 'HIGH',
            'category': 'Authentication Security',
            'prevention_steps': [
                'Implement multi-factor authentication (MFA) for all user accounts',
                'Enable device fingerprinting to detect login from new/unusual devices',
                'Set up geolocation-based login alerts for access from new countries',
                'Implement CAPTCHA for login attempts after failed password entries',
                'Monitor login velocity - flag multiple login attempts in short time',
                'Use behavioral biometrics to detect unusual typing patterns'
            ],
            'immediate_actions': [
                'Review recent login history for flagged accounts',
                'Force password reset for accounts with suspicious login patterns',
                'Enable session monitoring for active suspicious sessions'
            ],
            'monitoring': 'Track login attempts per user per hour/day, login locations, device changes'
        },

        'Account takeover': {
            'severity': 'CRITICAL',
            'category': 'Account Security',
            'prevention_steps': [
                'Require MFA for all high-value transactions and account changes',
                'Implement account change notifications (email, SMS) in real-time',
                'Monitor for simultaneous sessions from different locations',
                'Flag and review accounts with recent password/email changes',
                'Implement "trust this device" mechanisms with device tokens',
                'Set up anomaly detection for account setting modifications'
            ],
            'immediate_actions': [
                'Immediately freeze accounts with confirmed takeover indicators',
                'Contact account holders through verified channels (phone)',
                'Review and reverse unauthorized transactions',
                'Reset credentials and invalidate all active sessions'
            ],
            'monitoring': 'Account setting changes, login from new IPs, session patterns, email/phone updates'
        },

        'Unusual location': {
            'severity': 'HIGH',
            'category': 'Geographic Security',
            'prevention_steps': [
                'Implement geo-velocity checks (impossible travel detection)',
                'Require step-up authentication for transactions from new countries',
                'Maintain user location history and flag deviations',
                'Set up country/region blocklists for high-risk areas',
                'Implement GPS verification for mobile transactions',
                'Create location-based transaction limits'
            ],
            'immediate_actions': [
                'Send real-time alerts to users for transactions from new locations',
                'Hold transactions for manual review from flagged countries',
                'Verify user identity through alternative channels'
            ],
            'monitoring': 'Transaction locations, user travel patterns, VPN/proxy detection, cross-border activity'
        },

        'Unusual device': {
            'severity': 'MEDIUM',
            'category': 'Device Security',
            'prevention_steps': [
                'Implement device fingerprinting and maintain trusted device registry',
                'Require email/SMS verification for transactions from new devices',
                'Check device reputation scores against fraud databases',
                'Monitor for jailbroken/rooted devices in mobile apps',
                'Implement device-based rate limiting',
                'Track device switching frequency per account'
            ],
            'immediate_actions': [
                'Challenge users with security questions on new device access',
                'Limit transaction amounts from unverified devices',
                'Send device registration notifications to primary email'
            ],
            'monitoring': 'Device fingerprints, OS/browser changes, mobile vs desktop usage, device age'
        },

        'Velocity abuse': {
            'severity': 'HIGH',
            'category': 'Transaction Velocity',
            'prevention_steps': [
                'Set transaction count limits per user per time window (hourly/daily)',
                'Implement progressive rate limiting (stricter after threshold breaches)',
                'Monitor transaction frequency across all payment methods',
                'Create velocity rules based on historical user behavior',
                'Flag rapid succession of similar transactions',
                'Implement cool-down periods after high-velocity activity'
            ],
            'immediate_actions': [
                'Temporarily throttle accounts exceeding velocity thresholds',
                'Review transaction patterns for automation/bot activity',
                'Contact users to verify legitimate bulk transactions'
            ],
            'monitoring': 'Transactions per hour/day, time between transactions, burst patterns, repeat transactions'
        },

        'Transaction burst': {
            'severity': 'HIGH',
            'category': 'Transaction Patterns',
            'prevention_steps': [
                'Detect and flag sudden spikes in transaction volume',
                'Implement burst detection algorithms (3+ transactions within minutes)',
                'Set up alerts for accounts with no history suddenly active',
                'Monitor for automated transaction patterns',
                'Require manual approval for burst transactions above threshold',
                'Track transaction timing patterns'
            ],
            'immediate_actions': [
                'Hold burst transactions for fraud analyst review',
                'Verify user intent through phone/email confirmation',
                'Check if account credentials have been compromised'
            ],
            'monitoring': 'Transaction clustering, time gaps between transactions, volume spikes, automation indicators'
        },

        'High-risk merchant': {
            'severity': 'MEDIUM',
            'category': 'Merchant Risk',
            'prevention_steps': [
                'Maintain merchant risk scoring database with fraud history',
                'Monitor merchant category codes (MCCs) for high-risk categories',
                'Implement transaction limits for risky merchant categories',
                'Cross-reference merchants with fraud blacklists',
                'Track chargebacks and disputes by merchant',
                'Set up merchant reputation monitoring'
            ],
            'immediate_actions': [
                'Require additional verification for high-risk merchant transactions',
                'Apply lower transaction limits for flagged merchants',
                'Review transaction history with identified risky merchants'
            ],
            'monitoring': 'Merchant fraud rates, chargeback ratios, merchant category patterns, geographic risk'
        },

        'Unusual amount': {
            'severity': 'HIGH',
            'category': 'Amount Anomaly',
            'prevention_steps': [
                'Build per-user transaction amount profiles',
                'Flag transactions exceeding 3x standard deviation from mean',
                'Implement progressive amount-based verification',
                'Set dynamic transaction limits based on user history',
                'Monitor for first-time large transactions',
                'Create merchant-specific amount thresholds'
            ],
            'immediate_actions': [
                'Require step-up authentication for unusually high amounts',
                'Hold transactions for manual review above risk threshold',
                'Contact users to confirm large/unusual purchases'
            ],
            'monitoring': 'Amount distributions, z-scores, user spending patterns, amount volatility'
        },

        'New payee spike': {
            'severity': 'MEDIUM',
            'category': 'Payee Patterns',
            'prevention_steps': [
                'Monitor frequency of new payee additions',
                'Implement waiting periods for transactions to newly added payees',
                'Require verification for payee details (account validation)',
                'Flag accounts adding multiple payees in short timeframes',
                'Track payee deletion and re-addition patterns',
                'Verify payee information against fraud databases'
            ],
            'immediate_actions': [
                'Review accounts with sudden new payee additions',
                'Delay first transaction to new payee for 24-48 hours',
                'Verify payee addition through secondary authentication'
            ],
            'monitoring': 'New payee frequency, payee turnover rate, payee verification status'
        },

        'Cross-border anomaly': {
            'severity': 'HIGH',
            'category': 'International Transactions',
            'prevention_steps': [
                'Profile user international transaction history',
                'Require pre-registration for international transactions',
                'Implement country-specific risk scoring',
                'Monitor for first-time cross-border transactions',
                'Set up currency conversion monitoring',
                'Track OFAC and sanctions list compliance'
            ],
            'immediate_actions': [
                'Hold first international transaction for review',
                'Verify user travel plans for cross-border activity',
                'Apply enhanced KYC for frequent international transactions'
            ],
            'monitoring': 'International transaction frequency, destination countries, currency patterns'
        },

        'Card-not-present risk': {
            'severity': 'HIGH',
            'category': 'Card Fraud',
            'prevention_steps': [
                'Implement 3D Secure (3DS) for all online card transactions',
                'Require CVV verification for card-not-present transactions',
                'Monitor for card testing patterns (small amounts)',
                'Track AVS (Address Verification Service) match rates',
                'Flag mismatches between billing and shipping addresses',
                'Monitor for multiple cards used from same IP/device'
            ],
            'immediate_actions': [
                'Decline transactions failing CVV/AVS checks',
                'Flag accounts with multiple card additions in short time',
                'Review shipping addresses for fraud indicators'
            ],
            'monitoring': 'CNP transaction ratio, CVV failures, AVS mismatches, card testing patterns'
        },

        'Money mule pattern': {
            'severity': 'CRITICAL',
            'category': 'Money Laundering',
            'prevention_steps': [
                'Detect rapid in-and-out transaction patterns',
                'Monitor for funds received then immediately transferred',
                'Flag accounts with high transaction volume but low balance',
                'Track network connections between accounts',
                'Monitor for round-number transfers',
                'Implement source-of-funds verification'
            ],
            'immediate_actions': [
                'Freeze accounts with confirmed mule activity',
                'Report to financial intelligence unit (FIU)',
                'Review linked accounts for network analysis',
                'File Suspicious Activity Report (SAR)'
            ],
            'monitoring': 'Fund flow patterns, account velocity, balance-to-volume ratios, network graphs'
        },

        'Structuring / smurfing': {
            'severity': 'CRITICAL',
            'category': 'Money Laundering',
            'prevention_steps': [
                'Detect multiple transactions just below reporting thresholds',
                'Monitor cumulative amounts over rolling time windows',
                'Flag patterns of consistent near-threshold amounts',
                'Track split transactions to same beneficiary',
                'Implement aggregation rules for related transactions',
                'Monitor for coordinated structuring across accounts'
            ],
            'immediate_actions': [
                'Aggregate related transactions for reporting',
                'File Currency Transaction Report (CTR) if threshold exceeded',
                'Review account history for systematic structuring',
                'Consider SAR filing for intentional avoidance'
            ],
            'monitoring': 'Transaction amounts near $9,000-$10,000, time-based aggregation, beneficiary patterns'
        },

        'Round-dollar pattern': {
            'severity': 'MEDIUM',
            'category': 'Transaction Patterns',
            'prevention_steps': [
                'Flag unusually high frequency of round-number transactions',
                'Monitor for consistent round amounts (100, 500, 1000)',
                'Compare round-amount ratio to peer group baseline',
                'Track round-amount patterns combined with other risk factors',
                'Analyze merchant types for legitimate round-amount transactions',
                'Build user-specific round-amount profiles'
            ],
            'immediate_actions': [
                'Review accounts with excessive round-amount transactions',
                'Correlate with other fraud indicators for risk assessment',
                'Verify legitimacy through transaction receipts'
            ],
            'monitoring': 'Round amount frequency, amount distributions, merchant patterns'
        },

        'Night-time activity': {
            'severity': 'MEDIUM',
            'category': 'Temporal Patterns',
            'prevention_steps': [
                'Profile user typical transaction times',
                'Flag transactions outside normal hours (e.g., 11 PM - 5 AM)',
                'Implement time-based risk scoring',
                'Require additional authentication for off-hours transactions',
                'Monitor for timezone inconsistencies with user location',
                'Track sudden changes in transaction timing patterns'
            ],
            'immediate_actions': [
                'Send real-time alerts for unusual time transactions',
                'Apply transaction limits during high-risk hours',
                'Verify user activity through push notifications'
            ],
            'monitoring': 'Transaction hour distribution, timezone analysis, user activity patterns, shift from normal'
        }
    }

    def __init__(self):
        """Initialize recommendation engine"""
        self.strategies = self.FRAUD_PREVENTION_STRATEGIES

    def generate_recommendations(self, fraud_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate comprehensive recommendations based on fraud patterns detected

        Args:
            fraud_analysis: Complete fraud analysis results including fraud_detection and insights

        Returns:
            List of recommendation objects with severity, category, and actionable steps
        """
        try:
            recommendations = []

            # Extract fraud detection results
            fraud_detection = fraud_analysis.get('fraud_detection', {})
            fraud_reason_breakdown = fraud_detection.get('fraud_reason_breakdown', [])
            transactions = fraud_analysis.get('transactions', [])

            # Overall fraud rate assessment
            fraud_percentage = fraud_detection.get('fraud_percentage', 0)
            recommendations.append(self._generate_overall_assessment(fraud_percentage, fraud_detection))

            # Generate pattern-specific recommendations
            for fraud_pattern in fraud_reason_breakdown:
                pattern_type = fraud_pattern.get('type', '')
                count = fraud_pattern.get('count', 0)
                percentage = fraud_pattern.get('percentage', 0)
                total_amount = fraud_pattern.get('total_amount', 0)

                if pattern_type in self.strategies and count > 0:
                    recommendations.append(
                        self._generate_pattern_recommendation(
                            pattern_type, count, percentage, total_amount
                        )
                    )

            # Add time-based recommendations
            time_recommendations = self._analyze_temporal_patterns(transactions)
            if time_recommendations:
                recommendations.extend(time_recommendations)

            # Add amount-based recommendations
            amount_recommendations = self._analyze_amount_patterns(transactions)
            if amount_recommendations:
                recommendations.extend(amount_recommendations)

            # Sort by severity
            severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3, 'INFO': 4}
            recommendations.sort(key=lambda x: severity_order.get(x.get('severity', 'INFO'), 5))

            return recommendations

        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}", exc_info=True)
            return [{
                'severity': 'INFO',
                'category': 'System',
                'title': 'Recommendation Generation Error',
                'description': 'Unable to generate detailed recommendations. Please review fraud patterns manually.',
                'prevention_steps': [],
                'immediate_actions': [],
                'monitoring': ''
            }]

    def _generate_overall_assessment(self, fraud_percentage: float,
                                    fraud_detection: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall fraud risk assessment"""
        fraud_count = fraud_detection.get('fraud_count', 0)
        total_count = fraud_detection.get('total_transactions', 0)
        fraud_amount = fraud_detection.get('total_fraud_amount', 0)

        if fraud_percentage >= 20:
            severity = 'CRITICAL'
            title = 'CRITICAL: Extremely High Fraud Rate Detected'
            description = f'{fraud_percentage:.1f}% fraud rate ({fraud_count}/{total_count} transactions). Immediate action required.'
            actions = [
                'Initiate emergency fraud response protocol',
                'Suspend high-risk transaction processing temporarily',
                'Conduct immediate security audit of authentication systems',
                'Review all recent account changes and access logs',
                'Notify fraud investigation team and management'
            ]
        elif fraud_percentage >= 10:
            severity = 'HIGH'
            title = 'HIGH RISK: Elevated Fraud Activity'
            description = f'{fraud_percentage:.1f}% fraud rate ({fraud_count}/{total_count} transactions). Enhanced monitoring required.'
            actions = [
                'Increase fraud detection sensitivity',
                'Implement manual review for high-value transactions',
                'Review and update fraud detection rules',
                'Conduct targeted analysis of fraud patterns',
                'Consider temporary transaction limits'
            ]
        elif fraud_percentage >= 5:
            severity = 'MEDIUM'
            title = 'MODERATE RISK: Above-Normal Fraud Levels'
            description = f'{fraud_percentage:.1f}% fraud rate ({fraud_count}/{total_count} transactions). Continue monitoring.'
            actions = [
                'Monitor fraud trends closely',
                'Review recent changes to fraud detection rules',
                'Analyze fraud pattern distributions',
                'Verify fraud detection model performance'
            ]
        else:
            severity = 'LOW'
            title = 'LOW RISK: Normal Fraud Levels'
            description = f'{fraud_percentage:.1f}% fraud rate ({fraud_count}/{total_count} transactions). Maintain current protocols.'
            actions = [
                'Continue standard fraud monitoring',
                'Regular review of fraud detection performance',
                'Maintain fraud prevention controls'
            ]

        return {
            'severity': severity,
            'category': 'Overall Risk Assessment',
            'title': title,
            'description': description,
            'fraud_count': fraud_count,
            'fraud_percentage': fraud_percentage,
            'fraud_amount': fraud_amount,
            'immediate_actions': actions
        }

    def _generate_pattern_recommendation(self, pattern_type: str, count: int,
                                        percentage: float, total_amount: float) -> Dict[str, Any]:
        """Generate recommendation for specific fraud pattern"""
        strategy = self.strategies.get(pattern_type, {})

        return {
            'severity': strategy.get('severity', 'MEDIUM'),
            'category': strategy.get('category', 'Fraud Prevention'),
            'pattern_type': pattern_type,
            'title': f"{pattern_type} Detected",
            'description': f"Detected {count} cases of '{pattern_type}' ({percentage:.1f}% of fraud, ${total_amount:,.2f} total)",
            'count': count,
            'percentage': percentage,
            'total_amount': total_amount,
            'prevention_steps': strategy.get('prevention_steps', []),
            'immediate_actions': strategy.get('immediate_actions', []),
            'monitoring': strategy.get('monitoring', '')
        }

    def _analyze_temporal_patterns(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze time-based fraud patterns"""
        recommendations = []

        try:
            fraud_txns = [t for t in transactions if t.get('is_fraud') == 1]

            if not fraud_txns:
                return []

            # Analyze hour distribution
            night_time_fraud = 0
            weekend_fraud = 0

            for txn in fraud_txns:
                timestamp = txn.get('timestamp', '')
                if timestamp:
                    try:
                        # Parse timestamp
                        if isinstance(timestamp, str):
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        else:
                            dt = timestamp

                        hour = dt.hour
                        day_of_week = dt.weekday()

                        # Night time: 11 PM to 5 AM
                        if hour >= 23 or hour < 5:
                            night_time_fraud += 1

                        # Weekend: Saturday (5), Sunday (6)
                        if day_of_week >= 5:
                            weekend_fraud += 1
                    except:
                        pass

            # Night-time fraud recommendation
            if night_time_fraud > 0:
                night_pct = (night_time_fraud / len(fraud_txns)) * 100
                if night_pct > 30:
                    recommendations.append({
                        'severity': 'HIGH',
                        'category': 'Temporal Analysis',
                        'title': 'High Night-Time Fraud Activity',
                        'description': f'{night_pct:.1f}% of fraud occurs during night hours (11 PM - 5 AM)',
                        'immediate_actions': [
                            'Implement enhanced authentication for night-time transactions',
                            'Set lower transaction limits during off-hours',
                            'Enable real-time alerts for night-time activity',
                            'Review accounts with frequent night-time transactions'
                        ],
                        'prevention_steps': [
                            'Require step-up authentication for 11 PM - 5 AM transactions',
                            'Implement time-based velocity limits',
                            'Monitor timezone inconsistencies'
                        ]
                    })

            # Weekend fraud recommendation
            if weekend_fraud > 0:
                weekend_pct = (weekend_fraud / len(fraud_txns)) * 100
                if weekend_pct > 40:
                    recommendations.append({
                        'severity': 'MEDIUM',
                        'category': 'Temporal Analysis',
                        'title': 'Elevated Weekend Fraud Activity',
                        'description': f'{weekend_pct:.1f}% of fraud occurs on weekends',
                        'immediate_actions': [
                            'Increase fraud analyst coverage on weekends',
                            'Enable automated weekend transaction monitoring',
                            'Review weekend transaction approval workflows'
                        ]
                    })

        except Exception as e:
            logger.error(f"Temporal pattern analysis failed: {e}")

        return recommendations

    def _analyze_amount_patterns(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze amount-based fraud patterns"""
        recommendations = []

        try:
            fraud_txns = [t for t in transactions if t.get('is_fraud') == 1]

            if not fraud_txns:
                return []

            # Calculate amount statistics
            fraud_amounts = [float(t.get('amount', 0)) for t in fraud_txns]
            avg_fraud_amount = sum(fraud_amounts) / len(fraud_amounts) if fraud_amounts else 0
            max_fraud_amount = max(fraud_amounts) if fraud_amounts else 0

            # High-value fraud
            high_value_threshold = 5000
            high_value_fraud = [a for a in fraud_amounts if a >= high_value_threshold]

            if high_value_fraud:
                high_value_pct = (len(high_value_fraud) / len(fraud_amounts)) * 100
                total_high_value = sum(high_value_fraud)

                recommendations.append({
                    'severity': 'HIGH',
                    'category': 'Amount Analysis',
                    'title': 'High-Value Fraud Detected',
                    'description': f'{len(high_value_fraud)} high-value fraud transactions (≥${high_value_threshold:,}) totaling ${total_high_value:,.2f}',
                    'immediate_actions': [
                        f'Review all transactions exceeding ${high_value_threshold:,}',
                        'Implement mandatory manual approval for high-value transactions',
                        'Contact affected customers for verification',
                        'Investigate accounts with high-value fraud'
                    ],
                    'prevention_steps': [
                        f'Set transaction limits at ${high_value_threshold:,} for unverified accounts',
                        'Require multi-level approval for amounts > ${high_value_threshold:,}',
                        'Implement progressive authentication based on amount'
                    ],
                    'max_amount': max_fraud_amount,
                    'avg_amount': avg_fraud_amount
                })

        except Exception as e:
            logger.error(f"Amount pattern analysis failed: {e}")

        return recommendations

    def get_prevention_strategy(self, fraud_type: str) -> Optional[Dict[str, Any]]:
        """
        Get prevention strategy for specific fraud type

        Args:
            fraud_type: Type of fraud pattern

        Returns:
            Prevention strategy details or None
        """
        return self.strategies.get(fraud_type)

    def get_all_fraud_types(self) -> List[str]:
        """Get list of all supported fraud types"""
        return list(self.strategies.keys())
