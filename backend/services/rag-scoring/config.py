"""
RAG Business Rules Configuration
Customizable scoring rules for market opportunities
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json


class RAGStatus(Enum):
    """RAG status enumeration"""

    RED = "RED"
    AMBER = "AMBER"
    GREEN = "GREEN"


@dataclass
class RAGThreshold:
    """RAG scoring threshold configuration"""

    red_max: float
    amber_max: float
    green_min: float

    def get_status(self, score: float) -> RAGStatus:
        """Get RAG status based on score"""
        if score <= self.red_max:
            return RAGStatus.RED
        elif score <= self.amber_max:
            return RAGStatus.AMBER
        else:
            return RAGStatus.GREEN


@dataclass
class RAGRule:
    """Individual RAG scoring rule"""

    name: str
    field: str
    operator: str  # '>', '>=', '<', '<=', '=', 'between', 'in'
    value: Any
    weight: float  # Impact weight on final score
    penalty: bool = False  # Whether this is a penalty
    description: str = ""
    active: bool = True


@dataclass
class RAGScoringConfig:
    """Complete RAG scoring configuration"""

    # Base thresholds
    thresholds: Dict[str, RAGThreshold] = field(default_factory=dict)

    # Scoring rules
    rules: List[RAGRule] = field(default_factory=list)

    # Feature weights for ML model
    feature_weights: Dict[str, float] = field(default_factory=dict)

    # Industry-specific adjustments
    industry_adjustments: Dict[str, Dict[str, float]] = field(default_factory=dict)

    # Market size multipliers
    market_size_multipliers: Dict[str, float] = field(default_factory=dict)

    # Risk factor penalties
    risk_factor_penalties: Dict[str, float] = field(default_factory=dict)

    # Competitive landscape scoring
    competitive_thresholds: Dict[str, Any] = field(default_factory=dict)

    # Growth rate scoring
    growth_rate_scoring: Dict[str, Any] = field(default_factory=dict)

    # Funding stage scoring
    funding_stage_scoring: Dict[str, Any] = field(default_factory=dict)

    # Team quality indicators
    team_quality_factors: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize default configuration if not provided"""
        if not self.thresholds:
            self.thresholds = {
                "default": RAGThreshold(red_max=30, amber_max=60, green_min=60)
            }

        if not self.rules:
            self.rules = self._get_default_rules()

        if not self.feature_weights:
            self.feature_weights = self._get_default_feature_weights()

        if not self.industry_adjustments:
            self.industry_adjustments = self._get_default_industry_adjustments()

        if not self.market_size_multipliers:
            self.market_size_multipliers = self._get_default_market_multipliers()

        if not self.risk_factor_penalties:
            self.risk_factor_penalties = self._get_default_risk_penalties()

        if not self.competitive_thresholds:
            self.competitive_thresholds = self._get_default_competitive_thresholds()

        if not self.growth_rate_scoring:
            self.growth_rate_scoring = self._get_default_growth_scoring()

        if not self.funding_stage_scoring:
            self.funding_stage_scoring = self._get_default_funding_scoring()

        if not self.team_quality_factors:
            self.team_quality_factors = self._get_default_team_factors()

    def _get_default_rules(self) -> List[RAGRule]:
        """Get default RAG scoring rules"""
        return [
            # Growth Rate Rules
            RAGRule(
                "High Growth",
                "growth_rate",
                ">",
                0.20,
                25,
                False,
                "Growth rate above 20%",
            ),
            RAGRule(
                "Medium Growth",
                "growth_rate",
                ">",
                0.10,
                15,
                False,
                "Growth rate above 10%",
            ),
            RAGRule(
                "Low Growth",
                "growth_rate",
                "<=",
                0.05,
                -20,
                True,
                "Growth rate at or below 5%",
            ),
            # Market Size Rules
            RAGRule("Large Market", "tam", ">", 1000000000, 25, False, "TAM above $1B"),
            RAGRule(
                "Medium Market", "tam", ">", 100000000, 15, False, "TAM above $100M"
            ),
            RAGRule(
                "Small Market", "tam", "<=", 50000000, -15, True, "TAM at or below $50M"
            ),
            # Funding Rules
            RAGRule(
                "High Funding",
                "funding_total",
                ">",
                20000000,
                20,
                False,
                "Funding above $20M",
            ),
            RAGRule(
                "Medium Funding",
                "funding_total",
                ">",
                5000000,
                10,
                False,
                "Funding above $5M",
            ),
            RAGRule(
                "Low Funding",
                "funding_total",
                "<",
                1000000,
                -10,
                True,
                "Funding below $1M",
            ),
            # Competitive Rules
            RAGRule(
                "Low Competition",
                "competitor_count",
                "<",
                8,
                15,
                False,
                "Less than 8 competitors",
            ),
            RAGRule(
                "High Competition",
                "competitor_count",
                ">",
                25,
                -15,
                True,
                "More than 25 competitors",
            ),
            # Team Quality Rules
            RAGRule(
                "Strong Team", "employee_count", ">", 100, 10, False, "100+ employees"
            ),
            RAGRule(
                "Strong Leadership",
                "founded_year",
                ">=",
                2018,
                5,
                False,
                "Founded in 2018 or later",
            ),
            # Industry Risk Rules
            RAGRule(
                "Regulatory Risk",
                "risk_factors",
                "contains",
                "regulatory",
                -20,
                True,
                "Regulatory compliance risk",
            ),
            RAGRule(
                "Technical Risk",
                "risk_factors",
                "contains",
                "technical",
                -15,
                True,
                "Technical complexity risk",
            ),
            RAGRule(
                "Market Risk",
                "risk_factors",
                "contains",
                "market",
                -10,
                True,
                "Market volatility risk",
            ),
            # Financial Health Rules
            RAGRule(
                "Revenue Growth",
                "revenue_growth",
                ">",
                0.15,
                15,
                False,
                "Revenue growth above 15%",
            ),
            RAGRule(
                "Negative Revenue",
                "revenue",
                "<=",
                0,
                -25,
                True,
                "Zero or negative revenue",
            ),
            RAGRule(
                "High Valuation",
                "valuation",
                ">",
                50000000,
                20,
                False,
                "Valuation above $50M",
            ),
        ]

    def _get_default_feature_weights(self) -> Dict[str, float]:
        """Get default feature weights for ML model"""
        return {
            "growth_rate": 0.25,
            "tam": 0.20,
            "funding_total": 0.15,
            "competitor_count": 0.10,
            "employee_count": 0.08,
            "revenue": 0.07,
            "valuation": 0.05,
            "market_maturity": 0.05,
            "team_quality": 0.03,
            "risk_factors": 0.02,
        }

    def _get_default_industry_adjustments(self) -> Dict[str, Dict[str, float]]:
        """Get default industry-specific adjustments"""
        return {
            "artificial_intelligence": {
                "growth_rate_multiplier": 1.2,
                "tam_multiplier": 1.3,
                "risk_adjustment": 0.1,
            },
            "fintech": {
                "growth_rate_multiplier": 1.1,
                "tam_multiplier": 1.2,
                "risk_adjustment": 0.2,  # Higher regulatory risk
            },
            "healthcare": {
                "growth_rate_multiplier": 1.0,
                "tam_multiplier": 1.4,  # Large addressable market
                "risk_adjustment": 0.15,  # Regulatory and privacy risks
            },
            "renewable_energy": {
                "growth_rate_multiplier": 1.3,  # High growth sector
                "tam_multiplier": 1.2,
                "risk_adjustment": 0.05,
            },
            "cybersecurity": {
                "growth_rate_multiplier": 1.2,
                "tam_multiplier": 1.1,
                "risk_adjustment": 0.08,
            },
            "blockchain": {
                "growth_rate_multiplier": 1.1,
                "tam_multiplier": 1.0,
                "risk_adjustment": 0.25,  # High regulatory uncertainty
            },
        }

    def _get_default_market_multipliers(self) -> Dict[str, float]:
        """Get market size multipliers"""
        return {
            "startup": 0.8,  # Lower multiplier for early stage
            "growth": 1.2,  # Higher multiplier for growth stage
            "mature": 1.0,  # Standard multiplier for mature market
            "disrupted": 1.5,  # High multiplier for disrupted markets
        }

    def _get_default_risk_penalties(self) -> Dict[str, float]:
        """Get risk factor penalties"""
        return {
            "regulatory_compliance": -25,
            "technology_risk": -20,
            "market_volatility": -15,
            "competitive_threat": -12,
            "execution_risk": -10,
            "funding_gap": -30,
            "team_execution": -8,
            "customer_concentration": -5,
            "intellectual_property": -15,
            "market_timing": -10,
        }

    def _get_default_competitive_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Get competitive landscape thresholds"""
        return {
            "fragmented": {"competitors": 5.0, "score_bonus": 20.0},
            "moderate": {"competitors": 15.0, "score_bonus": 10.0},
            "concentrated": {"competitors": 3.0, "score_bonus": 25.0},
            "crowded": {"competitors": 25.0, "score_penalty": -15.0},
        }

    def _get_default_growth_scoring(self) -> Dict[str, Dict[str, float]]:
        """Get growth rate scoring"""
        return {
            "explosive": {"min_rate": 0.50, "score": 30.0},
            "high": {"min_rate": 0.20, "score": 25.0},
            "medium": {"min_rate": 0.10, "score": 15.0},
            "low": {"min_rate": 0.05, "score": 5.0},
            "negative": {"max_rate": 0.00, "score": -20.0},
        }

    def _get_default_funding_scoring(self) -> Dict[str, Dict[str, float]]:
        """Get funding stage scoring"""
        return {
            "series_d_plus": {"score": 25.0},
            "series_c": {"score": 20.0},
            "series_b": {"score": 15.0},
            "series_a": {"score": 10.0},
            "seed": {"score": 5.0},
            "angel": {"score": 0.0},
            "bootstrap": {"score": -5.0},
        }

    def _get_default_team_factors(self) -> Dict[str, Dict[str, float]]:
        """Get team quality factors"""
        return {
            "employee_count_range": {
                "startup": 5.0,  # < 10 employees
                "small": 10.0,  # 10-50 employees
                "medium": 15.0,  # 50-200 employees
                "large": 20.0,  # > 200 employees
            },
            "leadership_quality": {"experienced": 15, "proven": 20, "first_time": 5},
            "founder_background": {
                "serial_entrepreneur": 15,
                "industry_expert": 10,
                "technical_founder": 8,
                "first_time": 3,
            },
            "advisory_board": {"strong": 10, "moderate": 5, "weak": 0},
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "thresholds": {
                name: {
                    "red_max": th.red_max,
                    "amber_max": th.amber_max,
                    "green_min": th.green_min,
                }
                for name, th in self.thresholds.items()
            },
            "rules": [
                {
                    "name": rule.name,
                    "field": rule.field,
                    "operator": rule.operator,
                    "value": rule.value,
                    "weight": rule.weight,
                    "penalty": rule.penalty,
                    "description": rule.description,
                    "active": rule.active,
                }
                for rule in self.rules
            ],
            "feature_weights": self.feature_weights,
            "industry_adjustments": self.industry_adjustments,
            "market_size_multipliers": self.market_size_multipliers,
            "risk_factor_penalties": self.risk_factor_penalties,
            "competitive_thresholds": self.competitive_thresholds,
            "growth_rate_scoring": self.growth_rate_scoring,
            "funding_stage_scoring": self.funding_stage_scoring,
            "team_quality_factors": self.team_quality_factors,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RAGScoringConfig":
        """Create configuration from dictionary"""
        config = cls()

        # Thresholds
        if "thresholds" in data:
            config.thresholds = {}
            for name, th_data in data["thresholds"].items():
                config.thresholds[name] = RAGThreshold(**th_data)

        # Rules
        if "rules" in data:
            config.rules = [RAGRule(**rule_data) for rule_data in data["rules"]]

        # Other fields
        for field_name in [
            "feature_weights",
            "industry_adjustments",
            "market_size_multipliers",
            "risk_factor_penalties",
            "competitive_thresholds",
            "growth_rate_scoring",
            "funding_stage_scoring",
            "team_quality_factors",
        ]:
            if field_name in data:
                setattr(config, field_name, data[field_name])

        return config


# Global configuration instance
rag_config = RAGScoringConfig()
