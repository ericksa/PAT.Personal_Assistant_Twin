"""
Data Collection Pipeline
Core data collection and enrichment engine
"""

import logging
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json
import time
from dataclasses import asdict

from sources import MarketDataSources, DataSourceConfig, collection_strategy

logger = logging.getLogger(__name__)


class DataCollector:
    """Main data collection orchestrator"""

    def __init__(self):
        """Initialize the data collector"""
        self.sources = MarketDataSources()
        self.strategy = collection_strategy

    async def collect_opportunity_data(self, company_name: str) -> Dict[str, Any]:
        """
        Collect comprehensive data for a company/opportunity

        Args:
            company_name: Name of the company to research

        Returns:
            Dictionary containing collected and enriched data
        """
        logger.info(f"Starting data collection for: {company_name}")

        start_time = time.time()

        # Initialize result structure
        collected_data = {
            "name": company_name,
            "collection_timestamp": datetime.utcnow().isoformat(),
            "collection_time_seconds": 0,
            "data_sources": [],
            "enriched_data": {},
            "raw_data": {},
            "enrichment_score": 0.0,
            "confidence_score": 0.0,
            "errors": [],
        }

        # Get enabled sources
        enabled_sources = self.sources.get_enabled_sources()

        # Collect data from each source
        for source_config in enabled_sources:
            try:
                logger.debug(f"Collecting from {source_config.name}")

                # Collect data from source
                source_data = await self._collect_from_source(
                    source_config, company_name
                )

                if source_data:
                    collected_data["raw_data"][source_config.source_type.value] = (
                        source_data
                    )
                    collected_data["data_sources"].append(
                        {
                            "source": source_config.name,
                            "type": source_config.source_type.value,
                            "collection_time": time.time() - start_time,
                            "success": True,
                            "record_count": len(source_data)
                            if isinstance(source_data, list)
                            else 1,
                        }
                    )

                    # Enrich collected data
                    enriched_data = self._enrich_from_source(source_config, source_data)
                    self._merge_enriched_data(
                        collected_data["enriched_data"], enriched_data
                    )

                # Rate limiting
                await asyncio.sleep(1.0 / source_config.rate_limit_per_hour * 3600)

            except Exception as e:
                error_msg = f"Error collecting from {source_config.name}: {str(e)}"
                logger.error(error_msg)
                collected_data["errors"].append(error_msg)
                collected_data["data_sources"].append(
                    {
                        "source": source_config.name,
                        "type": source_config.source_type.value,
                        "success": False,
                        "error": str(e),
                    }
                )

                continue

        # Calculate enrichment and confidence scores
        collected_data["enrichment_score"] = self._calculate_enrichment_score(
            collected_data
        )
        collected_data["confidence_score"] = self._calculate_confidence_score(
            collected_data
        )
        collected_data["collection_time_seconds"] = time.time() - start_time

        logger.info(
            f"Data collection completed for {company_name} in {collected_data['collection_time_seconds']:.2f}s"
        )
        logger.info(f"Data sources: {len(collected_data['data_sources'])}")
        logger.info(f"Enrichment score: {collected_data['enrichment_score']:.2f}")

        return collected_data

    async def _collect_from_source(
        self, source_config: DataSourceConfig, company_name: str
    ) -> Optional[Dict[str, Any]]:
        """Collect data from a specific source"""
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30), headers=source_config.headers
            ) as session:
                if source_config.source_type.value == "crunchbase":
                    return await self._collect_crunchbase(
                        session, source_config, company_name
                    )
                elif source_config.source_type.value == "news_api":
                    return await self._collect_news(
                        session, source_config, company_name
                    )
                elif source_config.source_type.value == "sec":
                    return await self._collect_sec_filings(
                        session, source_config, company_name
                    )
                elif source_config.source_type.value == "linkedin":
                    return await self._collect_linkedin(
                        session, source_config, company_name
                    )
                else:
                    # Generic collection for other sources
                    return await self._collect_generic(
                        session, source_config, company_name
                    )

        except Exception as e:
            logger.error(f"Source collection error for {source_config.name}: {e}")
            return None

    async def _collect_crunchbase(
        self,
        session: aiohttp.ClientSession,
        config: DataSourceConfig,
        company_name: str,
    ) -> Optional[Dict[str, Any]]:
        """Collect data from Crunchbase API"""
        try:
            # Mock implementation - in production, use real API
            return {
                "company_name": company_name,
                "description": f"Company description for {company_name}",
                "founded_year": 2019,
                "employee_count": 150,
                "website": f"https://{company_name.lower().replace(' ', '')}.com",
                "linkedin_url": f"https://linkedin.com/company/{company_name.lower().replace(' ', '-')}",
                "funding_stage": "Series B",
                "total_funding": 25000000,
                "last_funding_date": "2023-06-15",
                "industry": "artificial_intelligence",
                "location": "San Francisco, CA",
                "valuation": 150000000,
                "source": "crunchbase",
            }
        except Exception as e:
            logger.error(f"Crunchbase collection error: {e}")
            return None

    async def _collect_news(
        self,
        session: aiohttp.ClientSession,
        config: DataSourceConfig,
        company_name: str,
    ) -> Optional[List[Dict[str, Any]]]:
        """Collect news data"""
        try:
            # Mock implementation
            return [
                {
                    "title": f"{company_name} announces new AI platform",
                    "description": f"{company_name} has launched their latest AI platform for enterprise customers.",
                    "published_at": "2024-01-15T10:30:00Z",
                    "source": "TechCrunch",
                    "url": "https://example.com/news/1",
                    "sentiment_score": 0.8,
                },
                {
                    "title": f"{company_name} receives Series B funding",
                    "description": f"{company_name} closes $25M Series B round led by top VCs.",
                    "published_at": "2024-01-10T14:20:00Z",
                    "source": "VentureBeat",
                    "url": "https://example.com/news/2",
                    "sentiment_score": 0.9,
                },
            ]
        except Exception as e:
            logger.error(f"News collection error: {e}")
            return None

    async def _collect_sec_filings(
        self,
        session: aiohttp.ClientSession,
        config: DataSourceConfig,
        company_name: str,
    ) -> Optional[Dict[str, Any]]:
        """Collect SEC filing data"""
        try:
            # Mock implementation for private companies (most won't have SEC data)
            if any(
                term in company_name.lower()
                for term in ["inc", "corp", "corporation", "public"]
            ):
                return {
                    "company_name": company_name,
                    "cik": "123456789",
                    "sic_code": "7372",
                    "fiscal_year_end": "1231",
                    "form_types": ["10-K", "10-Q"],
                    "recent_filings": [
                        {
                            "form_type": "10-K",
                            "filing_date": "2023-12-31",
                            "document_url": "https://sec.gov/Archives/edgar/data/123456789/000123456789-23-123456.txt",
                        }
                    ],
                    "business_address": "123 Tech Street, San Francisco, CA 94105",
                    "source": "sec_edgar",
                }
            else:
                return None  # Private company, no SEC filings
        except Exception as e:
            logger.error(f"SEC collection error: {e}")
            return None

    async def _collect_linkedin(
        self,
        session: aiohttp.ClientSession,
        config: DataSourceConfig,
        company_name: str,
    ) -> Optional[Dict[str, Any]]:
        """Collect LinkedIn data"""
        try:
            # Mock implementation
            return {
                "company_name": company_name,
                "description": f"LinkedIn company description for {company_name}",
                "employee_count": 120,
                "website": f"https://{company_name.lower().replace(' ', '')}.com",
                "industry": "Artificial Intelligence",
                "location": "San Francisco Bay Area",
                "followers": 5000,
                "company_size": "51-200 employees",
                "founded": 2019,
                "source": "linkedin",
            }
        except Exception as e:
            logger.error(f"LinkedIn collection error: {e}")
            return None

    async def _collect_generic(
        self,
        session: aiohttp.ClientSession,
        config: DataSourceConfig,
        company_name: str,
    ) -> Optional[Dict[str, Any]]:
        """Generic data collection for other sources"""
        # This would implement API calls for other sources
        # For now, return None for unimplemented sources
        return None

    def _enrich_from_source(
        self, source_config: DataSourceConfig, source_data: Any
    ) -> Dict[str, Any]:
        """Enrich data from source using field mappings"""
        if not source_data:
            return {}

        enriched = {}

        # Handle different data structures
        if isinstance(source_data, list):
            # List of articles or records
            for i, item in enumerate(source_data):
                if isinstance(item, dict):
                    enriched_item = self._map_fields(source_config.fields_mapping, item)
                    enriched[f"{source_config.source_type.value}_{i}"] = enriched_item
        elif isinstance(source_data, dict):
            # Single record
            enriched = self._map_fields(source_config.fields_mapping, source_data)
            enriched["source_info"] = {
                "source_name": source_config.name,
                "source_type": source_config.source_type.value,
                "reliability_score": source_config.reliability_score,
                "enrichment_tags": source_config.enrichment_tags,
            }

        return enriched

    def _map_fields(
        self, field_mapping: Dict[str, str], source_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Map source fields to standardized fields"""
        mapped = {}

        for standard_field, source_path in field_mapping.items():
            try:
                # Navigate nested path (e.g., "properties.name")
                value = source_data
                for part in source_path.split("."):
                    if isinstance(value, dict) and part in value:
                        value = value[part]
                    else:
                        value = None
                        break

                if value is not None:
                    mapped[standard_field] = value

            except Exception as e:
                logger.debug(f"Field mapping error for {standard_field}: {e}")
                continue

        return mapped

    def _merge_enriched_data(self, target: Dict[str, Any], source: Dict[str, Any]):
        """Merge enriched data into target dictionary"""
        for key, value in source.items():
            if key in target:
                # Handle conflicts - prefer higher quality data
                if isinstance(target[key], dict) and isinstance(value, dict):
                    self._merge_enriched_data(target[key], value)
                else:
                    # Keep existing value, append source info
                    if "source_info" in source:
                        target[key] = {
                            "value": target[key],
                            "enriched_value": value,
                            "enrichment_source": source["source_info"],
                        }
                    else:
                        target[key] = value
            else:
                target[key] = value

    def _calculate_enrichment_score(self, collected_data: Dict[str, Any]) -> float:
        """Calculate enrichment score based on data completeness"""
        if not collected_data["raw_data"]:
            return 0.0

        priority_fields = self.strategy.get_high_priority_fields()
        enriched_fields = collected_data["enriched_data"]

        # Count populated priority fields
        populated_count = 0
        for field in priority_fields:
            if field in enriched_fields and enriched_fields[field] is not None:
                populated_count += 1

        # Score based on completeness
        base_score = (populated_count / len(priority_fields)) * 70

        # Bonus for data source diversity
        source_count = len(collected_data["data_sources"])
        source_bonus = min(source_count * 5, 20)

        # Bonus for recent data (within last 30 days)
        recent_bonus = 10 if self._has_recent_data(collected_data) else 0

        final_score = min(base_score + source_bonus + recent_bonus, 100)
        return final_score

    def _calculate_confidence_score(self, collected_data: Dict[str, Any]) -> float:
        """Calculate confidence score based on data source reliability"""
        if not collected_data["data_sources"]:
            return 0.0

        # Calculate weighted average reliability
        total_weight = 0
        weighted_score = 0

        for source_info in collected_data["data_sources"]:
            if source_info["success"]:
                # Get reliability from enriched data or use default
                reliability = 0.7  # Default reliability
                weight = 1.0

                weighted_score += reliability * weight
                total_weight += weight

        if total_weight > 0:
            return min(weighted_score / total_weight, 1.0)
        else:
            return 0.0

    def _has_recent_data(self, collected_data: Dict[str, Any]) -> bool:
        """Check if any data source has recent updates"""
        cutoff_date = datetime.utcnow().replace(month=datetime.utcnow().month - 1)

        for source_info in collected_data["data_sources"]:
            # In a real implementation, check timestamps
            # For now, assume data is recent if successful
            if source_info["success"]:
                return True

        return False

    async def batch_collect(self, company_names: List[str]) -> List[Dict[str, Any]]:
        """Collect data for multiple companies in batch"""
        logger.info(f"Starting batch collection for {len(company_names)} companies")

        # Process companies with concurrency limit
        semaphore = asyncio.Semaphore(3)  # Limit concurrent requests

        async def collect_single(company_name: str):
            async with semaphore:
                return await self.collect_opportunity_data(company_name)

        # Execute batch collection
        tasks = [collect_single(name) for name in company_names]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        successful_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch collection error for {company_names[i]}: {result}")
            else:
                successful_results.append(result)

        logger.info(
            f"Batch collection completed: {len(successful_results)}/{len(company_names)} successful"
        )

        return successful_results


# Global data collector instance
data_collector = DataCollector()
