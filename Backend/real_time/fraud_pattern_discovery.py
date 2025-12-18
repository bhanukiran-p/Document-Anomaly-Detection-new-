"""
Dynamic Fraud Pattern Discovery using Clustering and ML
Discovers fraud patterns from actual transaction data instead of using hardcoded rules
"""
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Tuple
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import os

logger = logging.getLogger(__name__)

# Check if OpenAI is available
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available for pattern naming")


class FraudPatternDiscovery:
    """
    Discovers fraud patterns from transaction data using unsupervised learning
    """

    def __init__(self, n_clusters: int = None, min_cluster_size: int = 5):
        """
        Initialize fraud pattern discovery

        Args:
            n_clusters: Number of clusters to discover (None = auto-determine)
            min_cluster_size: Minimum transactions per cluster
        """
        self.n_clusters = n_clusters
        self.min_cluster_size = min_cluster_size
        self.scaler = StandardScaler()
        self.model = None
        self.cluster_profiles = {}
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.llm = None

        if OPENAI_AVAILABLE and self.api_key:
            try:
                self.llm = ChatOpenAI(
                    model=os.getenv('AI_MODEL', 'gpt-4o-mini'),
                    openai_api_key=self.api_key,
                    temperature=0.3
                )
                logger.info("OpenAI initialized for pattern naming")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI: {e}")
                self.llm = None

    def _prepare_clustering_features(self, fraud_df: pd.DataFrame, features_df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare feature matrix for clustering from fraud transactions

        Args:
            fraud_df: DataFrame with fraudulent transactions
            features_df: DataFrame with engineered features

        Returns:
            DataFrame with clustering features
        """
        cluster_features = pd.DataFrame()

        # Amount features
        cluster_features['amount'] = fraud_df['amount'] if 'amount' in fraud_df.columns else 0
        cluster_features['amount_log'] = np.log1p(cluster_features['amount'])
        cluster_features['amount_zscore'] = features_df.get('amount_zscore', 0)

        # Location features
        cluster_features['country_mismatch'] = features_df.get('country_mismatch', 0)
        cluster_features['login_transaction_mismatch'] = features_df.get('login_transaction_mismatch', 0)
        cluster_features['is_foreign_currency'] = features_df.get('is_foreign_currency', 0)

        # Time features
        cluster_features['hour'] = features_df.get('hour', 12)
        cluster_features['is_night'] = features_df.get('is_night', 0)
        cluster_features['is_weekend'] = features_df.get('is_weekend', 0)

        # Velocity features
        cluster_features['customer_txn_count'] = features_df.get('customer_txn_count', 1)
        cluster_features['same_day_count'] = features_df.get('same_day_count', 1)
        cluster_features['amount_deviation'] = features_df.get('amount_deviation', 0)

        # Merchant/Category features
        cluster_features['high_risk_category'] = features_df.get('high_risk_category', 0)
        cluster_features['is_transfer'] = features_df.get('is_transfer', 0)

        # Balance features
        cluster_features['amount_to_balance_ratio'] = features_df.get('amount_to_balance_ratio', 0)
        cluster_features['low_balance'] = features_df.get('low_balance', 0)

        # Derived features
        cluster_features['is_round_amount'] = ((cluster_features['amount'] % 100) < 1).astype(int)
        cluster_features['is_high_velocity'] = (cluster_features['customer_txn_count'] >= 3).astype(int)
        cluster_features['is_high_value'] = (cluster_features['amount'] >= 3000).astype(int)

        return cluster_features

    def _determine_optimal_clusters(self, X: np.ndarray, max_clusters: int = 10) -> int:
        """
        Determine optimal number of clusters using elbow method

        Args:
            X: Feature matrix
            max_clusters: Maximum number of clusters to try

        Returns:
            Optimal number of clusters
        """
        n_samples = len(X)
        max_clusters = min(max_clusters, n_samples // self.min_cluster_size)
        max_clusters = max(2, min(max_clusters, 10))  # Between 2 and 10 clusters

        if n_samples < self.min_cluster_size * 2:
            logger.warning(f"Too few samples ({n_samples}) for clustering, using 2 clusters")
            return 2

        # Calculate inertia for different cluster counts
        inertias = []
        K_range = range(2, max_clusters + 1)

        for k in K_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(X)
            inertias.append(kmeans.inertia_)

        # Find elbow using rate of change
        if len(inertias) > 2:
            deltas = np.diff(inertias)
            delta_deltas = np.diff(deltas)
            elbow_idx = np.argmax(delta_deltas) + 2  # +2 because we start at k=2 and lose 2 points in diff
            optimal_k = min(K_range[elbow_idx] if elbow_idx < len(K_range) else K_range[-1], 8)
        else:
            optimal_k = 3  # Default to 3 clusters

        logger.info(f"Determined optimal clusters: {optimal_k} (from {n_samples} fraud samples)")
        return optimal_k

    def discover_patterns(self, fraud_df: pd.DataFrame, features_df: pd.DataFrame) -> Tuple[List[int], Dict[int, Dict]]:
        """
        Discover fraud patterns using clustering

        Args:
            fraud_df: DataFrame with fraudulent transactions
            features_df: DataFrame with engineered features

        Returns:
            Tuple of (cluster_labels, cluster_profiles)
        """
        logger.info(f"Starting fraud pattern discovery on {len(fraud_df)} fraudulent transactions")

        if len(fraud_df) < self.min_cluster_size:
            logger.warning(f"Too few fraud samples ({len(fraud_df)}) for pattern discovery")
            return [0] * len(fraud_df), {0: self._create_default_profile(fraud_df, features_df)}

        # Prepare features
        X = self._prepare_clustering_features(fraud_df, features_df)
        logger.info(f"Prepared {X.shape[1]} features for clustering")

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Determine optimal number of clusters if not specified
        if self.n_clusters is None:
            self.n_clusters = self._determine_optimal_clusters(X_scaled)

        # Perform clustering
        self.model = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
        cluster_labels = self.model.fit_predict(X_scaled)

        logger.info(f"Clustering complete: {self.n_clusters} patterns discovered")

        # Analyze each cluster to create profiles
        self.cluster_profiles = {}
        for cluster_id in range(self.n_clusters):
            cluster_mask = cluster_labels == cluster_id
            cluster_size = np.sum(cluster_mask)

            if cluster_size < self.min_cluster_size:
                logger.warning(f"Cluster {cluster_id} too small ({cluster_size}), merging with largest cluster")
                # Merge small clusters with the largest cluster
                largest_cluster = np.argmax([np.sum(cluster_labels == i) for i in range(self.n_clusters)])
                cluster_labels[cluster_mask] = largest_cluster
                continue

            # Create profile for this cluster
            cluster_fraud_df = fraud_df[cluster_mask]
            cluster_features = features_df[cluster_mask]
            cluster_X = X[cluster_mask]

            profile = self._analyze_cluster(cluster_id, cluster_fraud_df, cluster_features, cluster_X)
            self.cluster_profiles[cluster_id] = profile

            logger.info(f"Cluster {cluster_id}: {cluster_size} transactions - {profile.get('pattern_name', 'Unnamed')}")

        return cluster_labels.tolist(), self.cluster_profiles

    def _analyze_cluster(self, cluster_id: int, cluster_df: pd.DataFrame,
                        cluster_features: pd.DataFrame, cluster_X: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze a cluster to extract its characteristic pattern

        Args:
            cluster_id: Cluster identifier
            cluster_df: Transactions in this cluster
            cluster_features: Features for these transactions
            cluster_X: Clustering features

        Returns:
            Dictionary with cluster profile
        """
        profile = {
            'cluster_id': cluster_id,
            'size': len(cluster_df),
            'percentage': 0,  # Will be set later
        }

        # Amount characteristics
        profile['avg_amount'] = float(cluster_df['amount'].mean()) if 'amount' in cluster_df.columns else 0
        profile['median_amount'] = float(cluster_df['amount'].median()) if 'amount' in cluster_df.columns else 0
        profile['total_amount'] = float(cluster_df['amount'].sum()) if 'amount' in cluster_df.columns else 0
        profile['amount_range'] = (float(cluster_df['amount'].min()), float(cluster_df['amount'].max())) if 'amount' in cluster_df.columns else (0, 0)

        # Location characteristics
        profile['country_mismatch_rate'] = float(cluster_features.get('country_mismatch', pd.Series([0])).mean())
        profile['foreign_currency_rate'] = float(cluster_features.get('is_foreign_currency', pd.Series([0])).mean())

        # Time characteristics
        profile['avg_hour'] = float(cluster_features.get('hour', pd.Series([12])).mean())
        profile['night_rate'] = float(cluster_features.get('is_night', pd.Series([0])).mean())
        profile['weekend_rate'] = float(cluster_features.get('is_weekend', pd.Series([0])).mean())

        # Velocity characteristics
        profile['avg_txn_count'] = float(cluster_features.get('customer_txn_count', pd.Series([1])).mean())
        profile['avg_same_day_count'] = float(cluster_features.get('same_day_count', pd.Series([1])).mean())
        profile['high_velocity_rate'] = float((cluster_features.get('customer_txn_count', pd.Series([0])) >= 3).mean())

        # Merchant/Category characteristics
        profile['high_risk_merchant_rate'] = float(cluster_features.get('high_risk_category', pd.Series([0])).mean())
        profile['transfer_rate'] = float(cluster_features.get('is_transfer', pd.Series([0])).mean())

        # Balance characteristics
        profile['avg_balance_ratio'] = float(cluster_features.get('amount_to_balance_ratio', pd.Series([0])).mean())
        profile['low_balance_rate'] = float(cluster_features.get('low_balance', pd.Series([0])).mean())

        # Pattern characteristics
        profile['round_amount_rate'] = float(cluster_X['is_round_amount'].mean())
        profile['high_value_rate'] = float(cluster_X['is_high_value'].mean())

        # Extract most common categories and merchants (top 3)
        if 'category' in cluster_df.columns:
            top_categories = cluster_df['category'].value_counts().head(3).to_dict()
            profile['top_categories'] = {str(k): int(v) for k, v in top_categories.items()}
        else:
            profile['top_categories'] = {}

        if 'merchant' in cluster_df.columns:
            top_merchants = cluster_df['merchant'].value_counts().head(3).to_dict()
            profile['top_merchants'] = {str(k): int(v) for k, v in top_merchants.items()}
        else:
            profile['top_merchants'] = {}

        # Generate descriptive pattern name using characteristics
        profile['pattern_name'] = self._generate_pattern_name(profile)
        profile['pattern_description'] = self._generate_pattern_description(profile)

        return profile

    def _generate_pattern_name(self, profile: Dict[str, Any]) -> str:
        """
        Generate a descriptive name for the fraud pattern using OpenAI or rule-based approach

        Args:
            profile: Cluster profile dictionary

        Returns:
            Pattern name string
        """
        if self.llm is not None:
            try:
                return self._generate_pattern_name_with_ai(profile)
            except Exception as e:
                logger.warning(f"Failed to generate AI pattern name: {e}, falling back to rule-based")

        return self._generate_pattern_name_rule_based(profile)

    def _generate_pattern_name_with_ai(self, profile: Dict[str, Any]) -> str:
        """
        Use OpenAI to generate a descriptive pattern name

        Args:
            profile: Cluster profile dictionary

        Returns:
            AI-generated pattern name
        """
        # Create a concise summary of the pattern
        characteristics = []

        if profile['high_value_rate'] > 0.5:
            characteristics.append(f"High-value transactions (avg ${profile['avg_amount']:.0f})")
        elif profile['avg_amount'] > 1000:
            characteristics.append(f"Medium-value transactions (avg ${profile['avg_amount']:.0f})")

        if profile['high_velocity_rate'] > 0.5:
            characteristics.append(f"High velocity ({profile['avg_txn_count']:.1f} txns/customer)")

        if profile['night_rate'] > 0.5:
            characteristics.append("Primarily night-time (12am-6am)")
        elif profile['avg_hour'] >= 22 or profile['avg_hour'] <= 6:
            characteristics.append("Unusual hours")

        if profile['country_mismatch_rate'] > 0.5:
            characteristics.append("Cross-border location mismatches")

        if profile['foreign_currency_rate'] > 0.5:
            characteristics.append("Foreign currency")

        if profile['high_risk_merchant_rate'] > 0.5:
            characteristics.append("High-risk merchants")

        if profile['transfer_rate'] > 0.5:
            characteristics.append("Transfer transactions")

        if profile['round_amount_rate'] > 0.5:
            characteristics.append("Round-dollar amounts")

        if profile['top_categories']:
            top_cat = list(profile['top_categories'].keys())[0]
            characteristics.append(f"Category: {top_cat}")

        char_text = "; ".join(characteristics) if characteristics else "Mixed characteristics"

        prompt = f"""Based on the following fraud pattern characteristics, generate a concise, professional fraud pattern name (3-6 words maximum).

Characteristics:
{char_text}

Pattern Statistics:
- {profile['size']} transactions
- Average amount: ${profile['avg_amount']:.2f}
- Total fraudulent amount: ${profile['total_amount']:.2f}

Generate ONLY the pattern name, no explanation. Examples of good names:
- "High-Value Cross-Border Transfers"
- "Night-Time Gambling Transactions"
- "Rapid Small-Amount Velocity Abuse"
- "Round-Dollar Wire Transfer Structuring"

Pattern name:"""

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            pattern_name = response.content.strip().strip('"').strip("'")

            # Validate and clean the name
            if len(pattern_name) > 60:
                pattern_name = pattern_name[:57] + "..."

            logger.info(f"AI generated pattern name: {pattern_name}")
            return pattern_name

        except Exception as e:
            logger.error(f"OpenAI pattern naming failed: {e}")
            raise

    def _generate_pattern_name_rule_based(self, profile: Dict[str, Any]) -> str:
        """
        Generate pattern name using rule-based approach (fallback)

        Args:
            profile: Cluster profile dictionary

        Returns:
            Rule-based pattern name
        """
        components = []

        # Value component
        if profile['high_value_rate'] > 0.5:
            components.append("High-Value")
        elif profile['avg_amount'] > 1000:
            components.append("Medium-Value")

        # Velocity component
        if profile['high_velocity_rate'] > 0.5:
            components.append("Rapid")

        # Time component
        if profile['night_rate'] > 0.5:
            components.append("Night-Time")
        elif profile['weekend_rate'] > 0.5:
            components.append("Weekend")

        # Location component
        if profile['country_mismatch_rate'] > 0.5:
            components.append("Cross-Border")
        elif profile['foreign_currency_rate'] > 0.5:
            components.append("Foreign")

        # Merchant/Type component
        if profile['high_risk_merchant_rate'] > 0.5:
            components.append("High-Risk Merchant")
        elif profile['transfer_rate'] > 0.5:
            components.append("Transfer")

        # Amount pattern component
        if profile['round_amount_rate'] > 0.5:
            components.append("Round-Amount")

        # Category component
        if profile['top_categories']:
            top_cat = list(profile['top_categories'].keys())[0]
            if top_cat and str(top_cat).lower() not in ['nan', 'none', '']:
                components.append(str(top_cat).title())

        # Construct name
        if not components:
            components = ["Unclassified Fraud Pattern"]

        pattern_name = " ".join(components[:4])  # Limit to 4 components

        # Add "Fraud" if not obvious
        if "fraud" not in pattern_name.lower() and len(components) < 3:
            pattern_name += " Fraud"

        return pattern_name

    def _generate_pattern_description(self, profile: Dict[str, Any]) -> str:
        """
        Generate a detailed description of the fraud pattern

        Args:
            profile: Cluster profile dictionary

        Returns:
            Pattern description string
        """
        desc_parts = []

        desc_parts.append(f"{profile['size']} transactions totaling ${profile['total_amount']:,.2f}")
        desc_parts.append(f"with an average of ${profile['avg_amount']:.2f} per transaction")

        if profile['night_rate'] > 0.3:
            desc_parts.append(f"({profile['night_rate']*100:.0f}% occur at night)")

        if profile['high_velocity_rate'] > 0.3:
            desc_parts.append(f"({profile['high_velocity_rate']*100:.0f}% show high velocity)")

        if profile['country_mismatch_rate'] > 0.3:
            desc_parts.append(f"({profile['country_mismatch_rate']*100:.0f}% have location mismatches)")

        return ". ".join(desc_parts) + "."

    def _create_default_profile(self, fraud_df: pd.DataFrame, features_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Create a default profile when clustering is not possible

        Args:
            fraud_df: DataFrame with fraudulent transactions
            features_df: DataFrame with engineered features

        Returns:
            Default profile dictionary
        """
        return {
            'cluster_id': 0,
            'size': len(fraud_df),
            'percentage': 100.0,
            'pattern_name': 'General Fraudulent Activity',
            'pattern_description': f'{len(fraud_df)} fraudulent transactions detected',
            'avg_amount': float(fraud_df['amount'].mean()) if 'amount' in fraud_df.columns else 0,
            'total_amount': float(fraud_df['amount'].sum()) if 'amount' in fraud_df.columns else 0,
        }


def discover_fraud_patterns(fraud_df: pd.DataFrame, features_df: pd.DataFrame,
                           n_clusters: int = None) -> Tuple[List[str], Dict[int, Dict]]:
    """
    Discover fraud patterns from fraudulent transactions

    Args:
        fraud_df: DataFrame with fraudulent transactions
        features_df: DataFrame with engineered features for fraud transactions
        n_clusters: Number of clusters (None = auto-determine)

    Returns:
        Tuple of (pattern_names, cluster_profiles)
    """
    try:
        discoverer = FraudPatternDiscovery(n_clusters=n_clusters)
        cluster_labels, cluster_profiles = discoverer.discover_patterns(fraud_df, features_df)

        # Assign pattern names to each transaction
        pattern_names = []
        for label in cluster_labels:
            if label in cluster_profiles:
                pattern_names.append(cluster_profiles[label]['pattern_name'])
            else:
                pattern_names.append('Unknown Pattern')

        # Calculate percentages for each cluster
        total_fraud = len(fraud_df)
        for cluster_id, profile in cluster_profiles.items():
            profile['percentage'] = (profile['size'] / total_fraud) * 100

        logger.info(f"Pattern discovery complete: {len(cluster_profiles)} unique patterns found")
        for cluster_id, profile in cluster_profiles.items():
            logger.info(f"  Pattern: {profile['pattern_name']} - {profile['size']} cases ({profile['percentage']:.1f}%)")

        return pattern_names, cluster_profiles

    except Exception as e:
        logger.error(f"Pattern discovery failed: {e}", exc_info=True)
        # Return default pattern for all
        default_profile = {
            0: {
                'cluster_id': 0,
                'size': len(fraud_df),
                'percentage': 100.0,
                'pattern_name': 'Fraudulent Activity',
                'pattern_description': f'{len(fraud_df)} fraudulent transactions',
                'avg_amount': float(fraud_df['amount'].mean()) if 'amount' in fraud_df.columns else 0,
                'total_amount': float(fraud_df['amount'].sum()) if 'amount' in fraud_df.columns else 0,
            }
        }
        return ['Fraudulent Activity'] * len(fraud_df), default_profile
