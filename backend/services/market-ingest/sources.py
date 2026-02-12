"""
Market Data Sources Configuration
Connectors for major market intelligence sources
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import json


class DataSource(Enum):
    """Market data source types"""

    CRUNCHBASE = "crunchbase"
    LINKEDIN = "linkedin"
    SEC_FILINGS = "sec"
    NEWS_API = "news_api"
    GOOGLE_TRENDS = "google_trends"
    ALPHA_VANTAGE = "alpha_vantage"
    PITCHBOOK = "pitchbook"
    CB_INSIGHTS = "cb_insights"
    Y_COMBINATOR = "ycombinator"
    INDUSTRY_REPORTS = "industry_reports"


@dataclass
class DataSourceConfig:
    """Configuration for a market data source"""

    name: str
    source_type: DataSource
    base_url: str
    api_key_required: bool
    rate_limit_per_hour: int
    authentication_type: str  # 'api_key', 'oauth', 'bearer'
    headers: Dict[str, str]
    data_format: str  # 'json', 'xml', 'csv'
    update_frequency: str  # 'realtime', 'daily', 'weekly'
    reliability_score: float  # 0.0-1.0
    cost_per_request: float
    fields_mapping: Dict[str, str]
    enrichment_tags: List[str]
    enabled: bool = True


class MarketDataSources:
    """Market data sources configuration"""

    @staticmethod
    def get_crunchbase_config() -> DataSourceConfig:
        """Crunchbase API configuration"""
        return DataSourceConfig(
            name="Crunchbase",
            source_type=DataSource.CRUNCHBASE,
            base_url="https://api.crunchbase.com/v3.1",
            api_key_required=True,
            rate_limit_per_hour=1000,
            authentication_type="api_key",
            headers={
                "Content-Type": "application/json",
                "User-Agent": "PAT-MarketIntel/1.0",
            },
            data_format="json",
            update_frequency="daily",
            reliability_score=0.9,
            cost_per_request=0.01,
            fields_mapping={
                "name": "properties.name",
                "description": "properties.short_description",
                "founded_year": "properties.founded_year",
                "employee_count": "properties.employee_count",
                "website": "properties.website_url",
                "linkedin_url": "properties.linkedin_identifier",
                "funding_stage": "properties.funding_stage",
                "total_funding": "properties.total_funding_usd",
                "last_funding_date": "properties.last_funding_date",
                "industry": "properties.industries",
                "location": "properties.location_group_identifiers",
            },
            enrichment_tags=["company_data", "funding_info", "leadership"],
        )

    @staticmethod
    def get_linkedin_config() -> DataSourceConfig:
        """LinkedIn API configuration"""
        return DataSourceConfig(
            name="LinkedIn",
            source_type=DataSource.LINKEDIN,
            base_url="https://api.linkedin.com/v2",
            api_key_required=True,
            rate_limit_per_hour=500,
            authentication_type="oauth",
            headers={
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
            },
            data_format="json",
            update_frequency="daily",
            reliability_score=0.85,
            cost_per_request=0.02,
            fields_mapping={
                "name": "localizedName",
                "description": "localizedDescription",
                "employee_count": "staffCount",
                "website": "website",
                "industry": "industry",
                "location": "headquarters",
            },
            enrichment_tags=["social_data", "employee_insights", "company_profile"],
        )

    @staticmethod
    def get_sec_filings_config() -> DataSourceConfig:
        """SEC EDGAR API configuration"""
        return DataSourceConfig(
            name="SEC EDGAR",
            source_type=DataSource.SEC_FILINGS,
            base_url="https://data.sec.gov",
            api_key_required=False,
            rate_limit_per_hour=100,
            authentication_type="none",
            headers={"User-Agent": "PAT-MarketIntel/1.0 contact@company.com"},
            data_format="json",
            update_frequency="realtime",
            reliability_score=0.95,
            cost_per_request=0.0,
            fields_mapping={
                "name": "name",
                "description": "description",
                "sic_code": "sic",
                "fiscal_year_end": "fye",
                "state_of_incorporation": "state_of_incorporation",
                "business_address": "business_address",
                "cik": "cik",
            },
            enrichment_tags=["financial_data", "regulatory", "public_company"],
        )

    @staticmethod
    def get_news_api_config() -> DataSourceConfig:
        """News API configuration"""
        return DataSourceConfig(
            name="News API",
            source_type=DataSource.NEWS_API,
            base_url="https://newsapi.org/v2",
            api_key_required=True,
            rate_limit_per_hour=1000,
            authentication_type="api_key",
            headers={"Content-Type": "application/json"},
            data_format="json",
            update_frequency="realtime",
            reliability_score=0.7,
            cost_per_request=0.0,
            fields_mapping={
                "title": "title",
                "description": "description",
                "content": "content",
                "published_at": "publishedAt",
                "source": "source.name",
                "url": "url",
            },
            enrichment_tags=["market_sentiment", "company_news", "industry_trends"],
        )

    @staticmethod
    def get_google_trends_config() -> DataSourceConfig:
        """Google Trends API configuration"""
        return DataSourceConfig(
            name="Google Trends",
            source_type=DataSource.GOOGLE_TRENDS,
            base_url="https://trends.google.com/trends/api",
            api_key_required=False,
            rate_limit_per_hour=100,
            authentication_type="none",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
            data_format="json",
            update_frequency="daily",
            reliability_score=0.6,
            cost_per_request=0.0,
            fields_mapping={
                "search_volume": "default.interest_over_time.data",
                "related_queries": "default.related_topics.value",
                "geographic_interest": "default.geo_map.data",
            },
            enrichment_tags=["search_trends", "market_interest", "consumer_behavior"],
        )

    @staticmethod
    def get_alpha_vantage_config() -> DataSourceConfig:
        """Alpha Vantage API configuration"""
        return DataSourceConfig(
            name="Alpha Vantage",
            source_type=DataSource.ALPHA_VANTAGE,
            base_url="https://www.alphavantage.co/query",
            api_key_required=True,
            rate_limit_per_hour=500,
            authentication_type="api_key",
            headers={"Content-Type": "application/json"},
            data_format="json",
            update_frequency="realtime",
            reliability_score=0.8,
            cost_per_request=0.0,
            fields_mapping={
                "symbol": "symbol",
                "price": "price",
                "volume": "volume",
                "market_cap": "market_cap",
                "pe_ratio": "pe_ratio",
                "beta": "beta",
            },
            enrichment_tags=["financial_metrics", "stock_data", "market_performance"],
        )

    @staticmethod
    def get_all_sources() -> List[DataSourceConfig]:
        """Get all configured data sources"""
        return [
            MarketDataSources.get_crunchbase_config(),
            MarketDataSources.get_linkedin_config(),
            MarketDataSources.get_sec_filings_config(),
            MarketDataSources.get_news_api_config(),
            MarketDataSources.get_google_trends_config(),
            MarketDataSources.get_alpha_vantage_config(),
        ]

    @staticmethod
    def get_enabled_sources() -> List[DataSourceConfig]:
        """Get only enabled data sources"""
        return [
            source for source in MarketDataSources.get_all_sources() if source.enabled
        ]

    @staticmethod
    def get_source_by_type(source_type: DataSource) -> Optional[DataSourceConfig]:
        """Get configuration for specific source type"""
        for source in MarketDataSources.get_all_sources():
            if source.source_type == source_type:
                return source
        return None


class DataCollectionStrategy:
    """Strategies for data collection and enrichment"""

    @staticmethod
    def get_high_priority_fields() -> List[str]:
        """Get high-priority fields for basic opportunity assessment"""
        return [
            "name",
            "description",
            "tam",
            "growth_rate",
            "funding_total",
            "competitor_count",
            "employee_count",
            "revenue",
            "valuation",
            "industry",
            "funding_stage",
            "market_trends",
            "risk_factors",
        ]

    @staticmethod
    def get_enrichment_priority() -> Dict[str, int]:
        """Get enrichment priority for different data types"""
        return {
            "financial_data": 1,  # Highest priority
            "funding_info": 2,
            "market_size": 3,
            "competitive_data": 4,
            "social_data": 5,  # Lower priority
            "news_sentiment": 6,
            "search_trends": 7,  # Lowest priority
        }

    @staticmethod
    def get_collection_fallback_order() -> List[DataSource]:
        """Get fallback order for data collection"""
        return [
            DataSource.CRUNCHBASE,  # Primary - comprehensive company data
            DataSource.SEC_FILINGS,  # Secondary - financial data
            DataSource.LINKEDIN,  # Tertiary - social/team data
            DataSource.NEWS_API,  # Sentiment and news
            DataSource.GOOGLE_TRENDS,  # Market interest
            DataSource.ALPHA_VANTAGE,  # Stock performance
        ]


# Global configuration instance
market_sources_config = MarketDataSources()
collection_strategy = DataCollectionStrategy()
