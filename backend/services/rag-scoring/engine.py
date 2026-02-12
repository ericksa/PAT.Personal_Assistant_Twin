"""
RAG Scoring Engine Core
Advanced market opportunity scoring with business rules
"""

import logging
import math
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import asdict

import numpy as np

from config import RAGScoringConfig, RAGStatus

logger = logging.getLogger(__name__)


class RAGScoringEngine:
    """
    Advanced RAG scoring engine with configurable business rules
    """

    def __init__(self, config: RAGScoringConfig):
        """Initialize the scoring engine"""
        self.config = config
        self.base_score = 50.0  # Starting neutral score

    def score_opportunity(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score a market opportunity using configured rules

        Args:
            opportunity_data: Dictionary containing opportunity information

        Returns:
            Dictionary with score, status, and breakdown
        """
        try:
            logger.info(
                f"Scoring opportunity: {opportunity_data.get('name', 'Unknown')}"
            )

            # Initialize scoring breakdown
            breakdown = {
                "base_score": self.base_score,
                "rule_scores": {},
                "feature_scores": {},
                "penalties": {},
                "bonuses": {},
                "final_score": 0,
                "rag_status": "AMBER",
                "confidence": 0.0,
                "scoring_details": {},
            }

            # Start with base score
            final_score = self.base_score

            # Apply rule-based scoring
            rule_results = self._apply_scoring_rules(opportunity_data)
            breakdown["rule_scores"] = rule_results["rule_scores"]
            final_score += rule_results["total_adjustment"]

            # Apply feature-based scoring
            feature_results = self._apply_feature_scoring(opportunity_data)
            breakdown["feature_scores"] = feature_results["feature_scores"]
            final_score += feature_results["total_adjustment"]

            # Apply industry-specific adjustments
            industry_results = self._apply_industry_adjustments(opportunity_data)
            breakdown["scoring_details"]["industry"] = industry_results
            final_score += industry_results["adjustment"]

            # Apply risk factor penalties
            risk_results = self._apply_risk_penalties(opportunity_data)
            breakdown["penalties"] = risk_results["penalties"]
            final_score += risk_results["total_penalty"]

            # Apply competitive landscape scoring
            competitive_results = self._apply_competitive_scoring(opportunity_data)
            breakdown["scoring_details"]["competitive"] = competitive_results
            final_score += competitive_results["adjustment"]

            # Apply growth rate scoring
            growth_results = self._apply_growth_scoring(opportunity_data)
            breakdown["scoring_details"]["growth"] = growth_results
            final_score += growth_results["adjustment"]

            # Apply funding stage scoring
            funding_results = self._apply_funding_scoring(opportunity_data)
            breakdown["scoring_details"]["funding"] = funding_results
            final_score += funding_results["adjustment"]

            # Ensure score is within bounds
            final_score = max(0, min(100, final_score))

            # Determine RAG status
            rag_status = self._get_rag_status(final_score)

            # Calculate confidence (based on data completeness)
            confidence = self._calculate_confidence(opportunity_data)

            # Update breakdown
            breakdown.update(
                {
                    "final_score": round(final_score, 1),
                    "rag_status": rag_status.value,
                    "confidence": round(confidence, 3),
                    "total_adjustment": round(final_score - self.base_score, 1),
                }
            )

            logger.info(f"Scored opportunity: {final_score:.1f} ({rag_status.value})")

            return {
                "score": round(final_score, 1),
                "rag_status": rag_status.value,
                "confidence": round(confidence, 3),
                "breakdown": breakdown,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error scoring opportunity: {e}")
            # Return safe default
            return {
                "score": 50.0,
                "rag_status": "AMBER",
                "confidence": 0.0,
                "breakdown": {"error": str(e)},
                "timestamp": datetime.utcnow().isoformat(),
            }

    def _apply_scoring_rules(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply configured scoring rules with exclusive matching"""
        rule_scores = {}
        total_adjustment = 0.0
        
        # Group rules by field for exclusive matching
        rules_by_field = {}
        for rule in self.config.rules:
            if not rule.active:
                continue
            if rule.field not in rules_by_field:
                rules_by_field[rule.field] = []
            rules_by_field[rule.field].append(rule)
        
        for field, field_rules in rules_by_field.items():
            try:
                field_value = self._get_field_value(data, field)
                if field_value is None:
                    continue
                
                # Apply only the first matching rule for this field
                for rule in field_rules:
                    adjustment = self._evaluate_rule(rule, field_value)
                    if adjustment != 0:
                        rule_scores[rule.name] = {
                            'field': rule.field,
                            'operator': rule.operator,
                            'value': rule.value,
                            'field_value': field_value,
                            'adjustment': adjustment,
                            'description': rule.description
                        }
                        total_adjustment += adjustment
                        break  # Only apply the first matching rule
                        
            except Exception as e:
                logger.warning(f"Error evaluating rules for field {field}: {e}")
                continue
        
        return {
            'rule_scores': rule_scores,
            'total_adjustment': total_adjustment
        }
                logger.warning(f"Error evaluating rule {rule.name}: {e}")
                continue

        return {"rule_scores": rule_scores, "total_adjustment": total_adjustment}

    def _apply_feature_scoring(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply feature-based scoring using weighted features"""
        feature_scores = {}
        total_adjustment = 0.0

        for feature, weight in self.config.feature_weights.items():
            try:
                field_value = self._get_field_value(data, feature)
                if field_value is None:
                    continue

                # Normalize feature value (0-1 scale)
                normalized_value = self._normalize_feature(feature, field_value)

                # Apply weight and convert to adjustment
                adjustment = (
                    (normalized_value - 0.5) * weight * 20
                )  # Scale to reasonable adjustment

                if adjustment != 0:
                    feature_scores[feature] = {
                        "raw_value": field_value,
                        "normalized_value": normalized_value,
                        "weight": weight,
                        "adjustment": adjustment,
                    }
                    total_adjustment += adjustment

            except Exception as e:
                logger.warning(f"Error scoring feature {feature}: {e}")
                continue

        return {"feature_scores": feature_scores, "total_adjustment": total_adjustment}

    def _apply_industry_adjustments(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply industry-specific adjustments"""
        industry = self._get_field_value(data, "industry") or "general"
        adjustments = {"adjustment": 0.0, "factors": {}}

        # Get industry-specific adjustments
        industry_config = self.config.industry_adjustments.get(industry, {})

        # Apply growth rate multiplier
        if "growth_rate_multiplier" in industry_config:
            growth_rate = self._get_field_value(data, "growth_rate") or 0
            if growth_rate > 0:
                multiplier = industry_config["growth_rate_multiplier"]
                adjustment = (
                    growth_rate * 100 - growth_rate
                ) * multiplier  # Percentage improvement
                adjustments["factors"]["growth_multiplier"] = adjustment
                adjustments["adjustment"] += adjustment

        # Apply TAM multiplier
        if "tam_multiplier" in industry_config:
            tam = self._get_field_value(data, "tam") or 0
            if tam > 0:
                multiplier = industry_config["tam_multiplier"]
                # Log-scale adjustment for TAM
                tam_score = min(math.log10(tam / 1000000 + 1), 2)  # Log scale with cap
                adjustment = tam_score * 5 * multiplier
                adjustments["factors"]["tam_multiplier"] = adjustment
                adjustments["adjustment"] += adjustment

        # Apply risk adjustment
        if "risk_adjustment" in industry_config:
            risk_penalty = -abs(industry_config["risk_adjustment"] * 100)
            adjustments["factors"]["industry_risk"] = risk_penalty
            adjustments["adjustment"] += risk_penalty

        return adjustments

    def _apply_risk_penalties(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply risk factor penalties"""
        risk_factors = self._get_field_value(data, "risk_factors") or []
        penalties = {}
        total_penalty = 0.0

        if isinstance(risk_factors, str):
            try:
                risk_factors = eval(risk_factors)  # Parse JSON string if needed
            except:
                risk_factors = []

        for risk in risk_factors:
            if isinstance(risk, str):
                penalty = self.config.risk_factor_penalties.get(risk.lower(), -5)
                penalties[risk] = penalty
                total_penalty += penalty

        # Add additional calculated risks
        calculated_risks = self._calculate_additional_risks(data)
        for risk, penalty in calculated_risks.items():
            penalties[risk] = penalty
            total_penalty += penalty

        return {"penalties": penalties, "total_penalty": total_penalty}

    def _apply_competitive_scoring(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply competitive landscape scoring"""
        competitor_count = self._get_field_value(data, "competitor_count") or 10
        adjustment = 0.0
        details = {}

        # Evaluate against competitive thresholds
        for category, config in self.config.competitive_thresholds.items():
            if "competitors" in config and competitor_count <= config["competitors"]:
                if "score_bonus" in config:
                    adjustment = config["score_bonus"]
                    details["category"] = category
                    details["reason"] = (
                        f"Competitive landscape: {competitor_count} competitors ({category})"
                    )
                    break
                elif "score_penalty" in config:
                    adjustment = config["score_penalty"]
                    details["category"] = category
                    details["reason"] = (
                        f"Crowded market: {competitor_count} competitors"
                    )
                    break

        return {
            "adjustment": adjustment,
            "competitor_count": competitor_count,
            "details": details,
        }

    def _apply_growth_scoring(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply growth rate scoring"""
        growth_rate = self._get_field_value(data, "growth_rate") or 0
        adjustment = 0.0
        details = {}

        # Evaluate growth rate against scoring tiers
        for category, config in self.config.growth_rate_scoring.items():
            if "min_rate" in config and growth_rate >= config["min_rate"]:
                adjustment = config["score"]
                details["category"] = category
                details["reason"] = (
                    f"Growth rate: {growth_rate * 100:.1f}% ({category})"
                )
                break
            elif "max_rate" in config and growth_rate <= config["max_rate"]:
                adjustment = config["score"]
                details["category"] = category
                details["reason"] = (
                    f"Growth rate: {growth_rate * 100:.1f}% ({category})"
                )
                break

        return {
            "adjustment": adjustment,
            "growth_rate": growth_rate,
            "details": details,
        }

    def _apply_funding_scoring(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply funding stage scoring"""
        funding_stage = self._get_field_value(data, "funding_stage") or "unknown"
        adjustment = 0.0
        details = {}

        # Get funding stage score
        funding_config = self.config.funding_stage_scoring.get(
            funding_stage.lower(), {}
        )
        if "score" in funding_config:
            adjustment = funding_config["score"]
            details["stage"] = funding_stage
            details["reason"] = f"Funding stage: {funding_stage}"

        return {
            "adjustment": adjustment,
            "funding_stage": funding_stage,
            "details": details,
        }

    def _get_field_value(self, data: Dict[str, Any], field: str) -> Any:
        """Get field value from opportunity data with fallback support"""
        # Direct lookup
        if field in data:
            return data[field]

        # Try alternative field names
        alternatives = {
            "tam": ["total_addressable_market", "market_size", "addressable_market"],
            "growth_rate": ["growth", "revenue_growth", "market_growth"],
            "funding_total": ["funding", "total_funding", "funding_amount"],
            "competitor_count": ["competitors", "competition_count", "num_competitors"],
            "employee_count": ["employees", "staff", "team_size"],
            "revenue": ["revenue_current", "annual_revenue", "run_rate"],
            "valuation": ["company_valuation", "estimated_valuation"],
            "industry": ["sector", "market", "vertical"],
        }

        if field in alternatives:
            for alt in alternatives[field]:
                if alt in data:
                    return data[alt]

        return None

    def _evaluate_rule(self, rule, field_value: Any) -> float:
        """Evaluate a single rule against field value"""
        operator = rule.operator
        rule_value = rule.value
        adjustment = 0.0

        try:
            if operator == ">":
                if field_value > rule_value:
                    adjustment = rule.weight
                elif rule.penalty:
                    adjustment = -rule.weight
            elif operator == ">=":
                if field_value >= rule_value:
                    adjustment = rule.weight
                elif rule.penalty:
                    adjustment = -rule.weight
            elif operator == "<":
                if field_value < rule_value:
                    adjustment = rule.weight
                elif rule.penalty:
                    adjustment = -rule.weight
            elif operator == "<=":
                if field_value <= rule_value:
                    adjustment = rule.weight
                elif rule.penalty:
                    adjustment = -rule.weight
            elif operator == "=":
                if field_value == rule_value:
                    adjustment = rule.weight
                elif rule.penalty:
                    adjustment = -rule.weight
            elif operator == "contains":
                if isinstance(field_value, list):
                    if rule_value in field_value:
                        adjustment = rule.weight
                    elif rule.penalty:
                        adjustment = -rule.weight
                elif isinstance(field_value, str):
                    if rule_value in field_value.lower():
                        adjustment = rule.weight
                    elif rule.penalty:
                        adjustment = -rule.weight
            elif operator == "between":
                if isinstance(rule_value, (list, tuple)) and len(rule_value) == 2:
                    if rule_value[0] <= field_value <= rule_value[1]:
                        adjustment = rule.weight
                    elif rule.penalty:
                        adjustment = -rule.weight

        except Exception as e:
            logger.warning(f"Error evaluating rule {rule.name}: {e}")

        return adjustment

    def _normalize_feature(self, feature: str, value: float) -> float:
        """Normalize feature values to 0-1 scale"""
        if value is None or value <= 0:
            return 0.0

        # Feature-specific normalization
        if feature == "growth_rate":
            return min(value * 5, 1.0)  # Cap at 20% growth = max score
        elif feature == "tam":
            # Log scale normalization
            return min(math.log10(value / 1000000 + 1) / 2, 1.0)
        elif feature == "funding_total":
            return min(math.log10(value / 1000000 + 1) / 2, 1.0)
        elif feature == "employee_count":
            return min(value / 500, 1.0)  # 500+ employees = max score
        elif feature == "competitor_count":
            return max(1.0 - (value / 50), 0.0)  # Fewer competitors = higher score
        elif feature == "revenue":
            return min(value / 10000000, 1.0)  # $10M+ = max score
        elif feature == "valuation":
            return min(value / 100000000, 1.0)  # $100M+ = max score
        else:
            # Default normalization
            return min(value / 100, 1.0)

    def _calculate_additional_risks(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate additional risk factors based on data patterns"""
        risks = {}

        # Revenue risk
        revenue = self._get_field_value(data, "revenue") or 0
        if revenue <= 0:
            risks["negative_revenue"] = -25

        # Team size risk
        employees = self._get_field_value(data, "employee_count") or 0
        if employees < 5:
            risks["small_team"] = -10

        # Market maturity risk
        maturity = self._get_field_value(data, "market_maturity") or 50
        if maturity < 20:
            risks["early_market"] = -15

        # Funding gap risk
        funding = self._get_field_value(data, "funding_total") or 0
        revenue_annual = self._get_field_value(data, "revenue") or 0
        if funding > 0 and revenue_annual > 0:
            runway_months = funding / (revenue_annual / 12)
            if runway_months < 6:
                risks["short_runway"] = -20
            elif runway_months < 12:
                risks["moderate_runway"] = -10

        return risks

    def _calculate_confidence(self, data: Dict[str, Any]) -> float:
        """Calculate confidence score based on data completeness"""
        total_fields = 0
        filled_fields = 0

        # Key fields for confidence calculation
        key_fields = [
            "name",
            "description",
            "tam",
            "growth_rate",
            "funding_total",
            "competitor_count",
            "employee_count",
            "revenue",
            "industry",
        ]

        for field in key_fields:
            total_fields += 1
            if self._get_field_value(data, field) is not None:
                filled_fields += 1

        # Additional bonus for rich data
        if len(data) > 20:
            filled_fields += 5
            total_fields += 5

        return filled_fields / total_fields if total_fields > 0 else 0.5

    def _get_rag_status(self, score: float) -> RAGStatus:
        """Determine RAG status from score"""
        # Use default thresholds
        thresholds = self.config.thresholds.get(
            "default", self.config.thresholds.get("default")
        )
        if thresholds:
            return thresholds.get_status(score)
        else:
            # Fallback thresholds
            if score < 30:
                return RAGStatus.RED
            elif score < 60:
                return RAGStatus.AMBER
            else:
                return RAGStatus.GREEN

    def batch_score_opportunities(
        self, opportunities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Score multiple opportunities in batch"""
        logger.info(f"Batch scoring {len(opportunities)} opportunities")

        results = []
        for opportunity in opportunities:
            try:
                result = self.score_opportunity(opportunity)
                results.append(result)
            except Exception as e:
                logger.error(f"Error scoring opportunity in batch: {e}")
                # Add error result
                results.append(
                    {
                        "score": 50.0,
                        "rag_status": "AMBER",
                        "confidence": 0.0,
                        "breakdown": {"error": str(e)},
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

        return results

    def get_scoring_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get summary statistics from scoring results"""
        if not results:
            return {}

        scores = [r["score"] for r in results if "score" in r]
        rag_counts = {"RED": 0, "AMBER": 0, "GREEN": 0}
        confidences = [r["confidence"] for r in results if "confidence" in r]

        for result in results:
            rag_status = result.get("rag_status", "AMBER")
            rag_counts[rag_status] = rag_counts.get(rag_status, 0) + 1

        return {
            "total_count": len(results),
            "score_stats": {
                "mean": np.mean(scores) if scores else 0,
                "median": np.median(scores) if scores else 0,
                "min": min(scores) if scores else 0,
                "max": max(scores) if scores else 0,
                "std": np.std(scores) if scores else 0,
            },
            "rag_distribution": rag_counts,
            "avg_confidence": np.mean(confidences) if confidences else 0,
        }
