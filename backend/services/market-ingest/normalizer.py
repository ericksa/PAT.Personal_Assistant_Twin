"""
Data Normalization and Enrichment Pipeline
Transform raw market data into RAG-ready opportunity records
"""

import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class DataNormalizer:
    """Normalize and clean collected market data"""

    def __init__(self):
        """Initialize the normalizer"""
        self.currency_patterns = {"$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY"}

        self.industry_mappings = {
            "ai": "artificial_intelligence",
            "artificial intelligence": "artificial_intelligence",
            "machine learning": "artificial_intelligence",
            "fintech": "fintech",
            "financial technology": "fintech",
            "healthcare": "healthcare",
            "health tech": "healthcare_technology",
            "health technology": "healthcare_technology",
            "renewable energy": "renewable_energy",
            "clean tech": "clean_technology",
            "clean technology": "clean_technology",
            "cybersecurity": "cybersecurity",
            "cyber security": "cybersecurity",
            "blockchain": "blockchain",
            "e-commerce": "e-commerce",
            "ecommerce": "e-commerce",
            "agtech": "agricultural_technology",
            "agricultural technology": "agricultural_technology",
            "biotech": "biotechnology",
            "space tech": "space_technology",
            "quantum": "quantum_computing",
        }

    def normalize_opportunity_data(
        self, collected_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Normalize collected data into standard opportunity format

        Args:
            collected_data: Raw data from collection pipeline

        Returns:
            Normalized opportunity data ready for RAG scoring
        """
        try:
            logger.info(
                f"Normalizing data for: {collected_data.get('name', 'Unknown')}"
            )

            normalized = {
                # Core identity fields
                "name": self._normalize_company_name(collected_data.get("name")),
                "description": self._normalize_description(collected_data),
                # Market metrics
                "tam": self._normalize_market_size(collected_data),
                "growth_rate": self._normalize_growth_rate(collected_data),
                "competitor_count": self._normalize_competitor_count(collected_data),
                # Company metrics
                "funding_total": self._normalize_funding_amount(collected_data),
                "employee_count": self._normalize_employee_count(collected_data),
                "revenue": self._normalize_revenue(collected_data),
                "valuation": self._normalize_valuation(collected_data),
                # Industry and categorization
                "industry": self._normalize_industry(collected_data),
                "funding_stage": self._normalize_funding_stage(collected_data),
                # Risk and trends
                "risk_factors": self._extract_risk_factors(collected_data),
                "market_trends": self._extract_market_trends(collected_data),
                # Metadata
                "source_data": collected_data.get("raw_data", {}),
                "enrichment_score": collected_data.get("enrichment_score", 0),
                "confidence_score": collected_data.get("confidence_score", 0),
                "collection_timestamp": collected_data.get("collection_timestamp"),
                # Computed fields
                "market_maturity": self._calculate_market_maturity(collected_data),
                "funding_runway": self._calculate_funding_runway(collected_data),
                "competitive_position": self._assess_competitive_position(
                    collected_data
                ),
            }

            # Clean and validate data
            normalized = self._clean_and_validate(normalized)

            logger.info(f"Normalization complete: {normalized['name']}")

            return normalized

        except Exception as e:
            logger.error(f"Normalization error: {e}")
            return self._create_fallback_record(collected_data)

    def _normalize_company_name(self, name: str) -> str:
        """Normalize company name"""
        if not name:
            return "Unknown Company"

        # Remove extra whitespace and standardize
        name = re.sub(r"\s+", " ", name.strip())

        # Capitalize properly
        words = name.split()
        capitalized_words = []
        for word in words:
            if word.upper() in [
                "AI",
                "API",
                "SaaS",
                "B2B",
                "B2C",
                "IoT",
                "ML",
                "VR",
                "AR",
            ]:
                capitalized_words.append(word.upper())
            else:
                capitalized_words.append(word.capitalize())

        return " ".join(capitalized_words)

    def _normalize_description(self, data: Dict[str, Any]) -> str:
        """Normalize company description"""
        enriched_data = data.get("enriched_data", {})

        # Try different sources for description
        descriptions = []

        if "description" in enriched_data:
            descriptions.append(enriched_data["description"])

        # Check raw data sources
        for source_type, source_data in data.get("raw_data", {}).items():
            if isinstance(source_data, dict):
                desc_fields = ["description", "summary", "short_description"]
                for field in desc_fields:
                    if field in source_data and source_data[field]:
                        descriptions.append(source_data[field])

        # Return first non-empty description or generate fallback
        for desc in descriptions:
            if desc and len(desc.strip()) > 10:
                return desc.strip()

        # Fallback description
        name = data.get("name", "Company")
        return f"Company focused on innovative solutions in the technology sector"

    def _normalize_market_size(self, data: Dict[str, Any]) -> Optional[float]:
        """Normalize Total Addressable Market (TAM)"""
        enriched_data = data.get("enriched_data", {})

        # Try direct TAM field
        if "tam" in enriched_data and enriched_data["tam"]:
            return float(enriched_data["tam"])

        # Extract from description or other fields
        description = self._normalize_description(data).lower()

        # Look for market size mentions
        market_size_patterns = [
            r"(\d+(?:\.\d+)?)\s*(billion|b|bn)\s*(?:market|opportunity)",
            r"(\d+(?:\.\d+)?)\s*(million|m|mn)\s*(?:market|opportunity)",
            r"(?:market size|tam|addressable market).*?(\d+(?:\.\d+)?)\s*(billion|million)",
        ]

        for pattern in market_size_patterns:
            match = re.search(pattern, description)
            if match:
                value = float(match.group(1))
                unit = match.group(2).lower()

                if unit.startswith("b"):
                    return value * 1_000_000_000
                else:
                    return value * 1_000_000

        # Calculate from revenue if available
        revenue = self._normalize_revenue(data)
        if revenue:
            return revenue * 10  # Assume 10x revenue as TAM

        return None

    def _normalize_growth_rate(self, data: Dict[str, Any]) -> Optional[float]:
        """Normalize growth rate"""
        enriched_data = data.get("enriched_data", {})

        # Try direct growth rate field
        if "growth_rate" in enriched_data and enriched_data["growth_rate"]:
            growth = float(enriched_data["growth_rate"])
            # Ensure it's a rate (0-1 range), not percentage
            return growth if growth <= 1 else growth / 100

        # Extract from description
        description = self._normalize_description(data).lower()

        # Look for growth mentions
        growth_patterns = [
            r"(\d+(?:\.\d+)?)\s*%?\s*(?:growth|expanding|expansion)",
            r"(?:growing|growth rate).*?(\d+(?:\.\d+)?)\s*%",
            r"(\d+(?:\.\d+)?)\s*percent(?:.*)?growth",
        ]

        for pattern in growth_patterns:
            match = re.search(pattern, description)
            if match:
                value = float(match.group(1))
                # Convert percentage to decimal if needed
                return value / 100 if value > 1 else value

        # Default growth rates by industry
        industry = self._normalize_industry(data)
        industry_defaults = {
            "artificial_intelligence": 0.35,
            "blockchain": 0.25,
            "renewable_energy": 0.20,
            "healthcare_technology": 0.18,
            "biotechnology": 0.15,
            "cybersecurity": 0.22,
            "agricultural_technology": 0.12,
        }

        return industry_defaults.get(industry, 0.10)  # Default 10% growth

    def _normalize_competitor_count(self, data: Dict[str, Any]) -> int:
        """Normalize competitor count"""
        enriched_data = data.get("enriched_data", {})

        # Try direct competitor field
        if "competitor_count" in enriched_data:
            return int(enriched_data["competitor_count"])

        # Estimate based on market characteristics
        industry = self._normalize_industry(data)
        tam = self._normalize_market_size(data)

        # Industry-based estimates
        industry_estimates = {
            "artificial_intelligence": 25,
            "fintech": 30,
            "healthcare_technology": 20,
            "renewable_energy": 15,
            "cybersecurity": 18,
            "blockchain": 12,
            "e-commerce": 35,
            "agricultural_technology": 8,
            "biotechnology": 6,
        }

        base_count = industry_estimates.get(industry, 15)

        # Adjust based on TAM
        if tam and tam > 5_000_000_000:  # > $5B market
            base_count = int(base_count * 1.5)
        elif tam and tam < 100_000_000:  # < $100M market
            base_count = int(base_count * 0.7)

        return max(1, base_count)

    def _normalize_funding_amount(self, data: Dict[str, Any]) -> Optional[float]:
        """Normalize total funding amount"""
        enriched_data = data.get("enriched_data", {})

        # Try direct funding field
        funding_fields = ["funding_total", "total_funding", "funding"]
        for field in funding_fields:
            if field in enriched_data and enriched_data[field]:
                return float(enriched_data[field])

        return None

    def _normalize_employee_count(self, data: Dict[str, Any]) -> Optional[int]:
        """Normalize employee count"""
        enriched_data = data.get("enriched_data", {})

        # Try direct employee field
        if "employee_count" in enriched_data:
            return int(enriched_data["employee_count"])

        # Estimate from funding stage and industry
        funding_stage = self._normalize_funding_stage(data)

        stage_estimates = {
            "seed": 5,
            "series_a": 15,
            "series_b": 40,
            "series_c": 100,
            "series_d_plus": 200,
            "bootstrap": 3,
            "angel": 8,
        }

        return stage_estimates.get(funding_stage, 20)

    def _normalize_revenue(self, data: Dict[str, Any]) -> Optional[float]:
        """Normalize revenue"""
        enriched_data = data.get("enriched_data", {})

        # Try direct revenue field
        if "revenue" in enriched_data and enriched_data["revenue"]:
            return float(enriched_data["revenue"])

        # Estimate from funding and employee count
        funding = self._normalize_funding_amount(data)
        employees = self._normalize_employee_count(data)

        if funding and employees:
            # Revenue = Funding / (Employee Count * Average CAC)
            avg_cac = 150000  # Average customer acquisition cost
            return funding / (employees * avg_cac) if employees > 0 else None

        return None

    def _normalize_valuation(self, data: Dict[str, Any]) -> Optional[float]:
        """Normalize company valuation"""
        enriched_data = data.get("enriched_data", {})

        # Try direct valuation field
        if "valuation" in enriched_data and enriched_data["valuation"]:
            return float(enriched_data["valuation"])

        # Estimate from funding (typically 2-5x funding amount)
        funding = self._normalize_funding_amount(data)
        if funding:
            return funding * 3  # Conservative 3x multiple

        return None

    def _normalize_industry(self, data: Dict[str, Any]) -> str:
        """Normalize industry classification"""
        enriched_data = data.get("enriched_data", {})

        # Try direct industry field
        if "industry" in enriched_data:
            industry_raw = enriched_data["industry"].lower()

            # Map to standardized industry
            for key, value in self.industry_mappings.items():
                if key in industry_raw:
                    return value

        # Analyze description for industry clues
        description = self._normalize_description(data).lower()

        for key, value in self.industry_mappings.items():
            if key in description:
                return value

        # Default industry
        return "technology"

    def _normalize_funding_stage(self, data: Dict[str, Any]) -> str:
        """Normalize funding stage"""
        enriched_data = data.get("enriched_data", {})

        # Try direct funding stage field
        if "funding_stage" in enriched_data:
            stage_raw = enriched_data["funding_stage"].lower()

            stage_mappings = {
                "seed": ["seed", "pre-seed"],
                "series a": ["series a", "seriesa"],
                "series b": ["series b", "seriesb"],
                "series c": ["series c", "seriesc"],
                "series d plus": ["series d", "series e", "growth"],
                "bootstrap": ["bootstrapped", "profitable"],
                "angel": ["angel", "pre-seed"],
            }

            for standard_stage, variations in stage_mappings.items():
                if any(var in stage_raw for var in variations):
                    return standard_stage

        # Estimate from funding amount
        funding = self._normalize_funding_amount(data)
        if funding:
            if funding < 1000000:  # < $1M
                return "seed"
            elif funding < 5000000:  # $1M - $5M
                return "series a"
            elif funding < 15000000:  # $5M - $15M
                return "series b"
            elif funding < 50000000:  # $15M - $50M
                return "series c"
            else:  # > $50M
                return "series d plus"

        return "unknown"

    def _extract_risk_factors(self, data: Dict[str, Any]) -> List[str]:
        """Extract and normalize risk factors"""
        risk_factors = []

        # Check for explicit risk factors
        enriched_data = data.get("enriched_data", {})
        if "risk_factors" in enriched_data:
            risk_factors.extend(enriched_data["risk_factors"])

        # Analyze description for risk indicators
        description = self._normalize_description(data).lower()

        risk_keywords = {
            "regulatory_compliance": [
                "regulation",
                "regulatory",
                "compliance",
                "fda",
                "sec",
            ],
            "technology_risk": ["experimental", "unproven", "complex", "cutting-edge"],
            "market_volatility": ["volatile", "uncertain", "fluctuating", "unstable"],
            "competitive_threat": [
                "competition",
                "competitors",
                "crowded",
                "saturated",
            ],
            "execution_risk": ["execution", "implementation", "deployment"],
            "funding_gap": ["funding", "capital", "investment", "runway"],
            "customer_concentration": ["concentration", "depend", "single customer"],
            "intellectual_property": ["patent", "ip", "intellectual property"],
            "market_timing": ["early", "unproven market", "emerging", "new market"],
        }

        for risk_type, keywords in risk_keywords.items():
            if any(keyword in description for keyword in keywords):
                risk_factors.append(risk_type)

        return list(set(risk_factors))  # Remove duplicates

    def _extract_market_trends(self, data: Dict[str, Any]) -> List[str]:
        """Extract market trends and opportunities"""
        trends = []

        # Check for explicit trends
        enriched_data = data.get("enriched_data", {})
        if "market_trends" in enriched_data:
            trends.extend(enriched_data["market_trends"])

        # Analyze description for trend indicators
        description = self._normalize_description(data).lower()

        trend_keywords = {
            "digital transformation": ["digital", "transformation", "automation"],
            "artificial intelligence": [
                "ai",
                "artificial intelligence",
                "machine learning",
            ],
            "sustainability": ["sustainable", "green", "environment", "climate"],
            "remote work": ["remote", "work from home", "virtual"],
            "cloud adoption": ["cloud", "saas", "software as a service"],
            "cybersecurity": ["security", "cybersecurity", "data protection"],
            "healthcare digitization": ["healthcare", "medical", "telemedicine"],
            "financial inclusion": ["fintech", "financial", "payment"],
            "supply chain optimization": ["supply chain", "logistics", "optimization"],
        }

        for trend, keywords in trend_keywords.items():
            if any(keyword in description for keyword in keywords):
                trends.append(trend)

        return list(set(trends))  # Remove duplicates

    def _calculate_market_maturity(self, data: Dict[str, Any]) -> int:
        """Calculate market maturity score (0-100)"""
        # Factors indicating mature markets
        maturity_factors = 0

        # Large established market
        tam = self._normalize_market_size(data)
        if tam and tam > 1_000_000_000:  # > $1B
            maturity_factors += 30

        # Many competitors indicate established market
        competitors = self._normalize_competitor_count(data)
        if competitors > 20:
            maturity_factors += 25
        elif competitors > 10:
            maturity_factors += 15

        # Stable growth rate indicates maturity
        growth_rate = self._normalize_growth_rate(data)
        if growth_rate and 0.05 <= growth_rate <= 0.25:  # 5-25% growth
            maturity_factors += 20

        # Established companies in space
        funding_stage = self._normalize_funding_stage(data)
        if funding_stage in ["series c", "series d plus"]:
            maturity_factors += 15

        # High revenue companies
        revenue = self._normalize_revenue(data)
        if revenue and revenue > 10_000_000:  # > $10M revenue
            maturity_factors += 10

        return min(100, maturity_factors)

    def _calculate_funding_runway(self, data: Dict[str, Any]) -> Optional[int]:
        """Calculate funding runway in months"""
        funding = self._normalize_funding_amount(data)
        revenue = self._normalize_revenue(data)

        if not funding:
            return None

        # Estimate monthly burn rate
        employees = self._normalize_employee_count(data) or 10
        avg_salary = 80000  # Average tech salary
        monthly_burn = (employees * avg_salary) / 12

        # Subtract revenue if available
        if revenue:
            monthly_burn = max(monthly_burn - (revenue / 12), monthly_burn * 0.3)

        if monthly_burn > 0:
            return int(funding / monthly_burn)

        return None

    def _assess_competitive_position(self, data: Dict[str, Any]) -> str:
        """Assess competitive position"""
        competitors = self._normalize_competitor_count(data)
        funding = self._normalize_funding_amount(data)
        employees = self._normalize_employee_count(data)

        # Strong position indicators
        strong_indicators = 0
        if funding and funding > 10_000_000:
            strong_indicators += 1
        if employees and employees > 50:
            strong_indicators += 1
        if competitors < 10:
            strong_indicators += 1

        if strong_indicators >= 2:
            return "strong"
        elif strong_indicators == 1:
            return "moderate"
        else:
            return "weak"

    def _clean_and_validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and validate normalized data"""
        # Remove None values
        cleaned = {k: v for k, v in data.items() if v is not None}

        # Ensure required fields have defaults
        required_fields = {
            "name": "Unknown Company",
            "industry": "technology",
            "funding_stage": "unknown",
        }

        for field, default_value in required_fields.items():
            if field not in cleaned or not cleaned[field]:
                cleaned[field] = default_value

        return cleaned

    def _create_fallback_record(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a fallback normalized record when normalization fails"""
        return {
            "name": self._normalize_company_name(
                raw_data.get("name", "Unknown Company")
            ),
            "description": "Company data collected but normalization incomplete",
            "industry": "technology",
            "funding_stage": "unknown",
            "risk_factors": ["data_incomplete"],
            "market_trends": [],
            "confidence_score": 0.3,  # Low confidence for fallback
            "source_data": {"fallback": True},
            "collection_timestamp": datetime.utcnow().isoformat(),
        }


# Global normalizer instance
data_normalizer = DataNormalizer()
