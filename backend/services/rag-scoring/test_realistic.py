#!/usr/bin/env python3
"""
Realistic RAG Scoring Test
Demonstrate realistic RAG scoring with proper score distribution
"""

import sys
import os

sys.path.append(os.path.dirname(__file__))


def test_realistic_rag_scoring():
    """Test with realistic scoring results"""

    print("🚀 Realistic RAG Scoring Test")
    print("=" * 40)

    # Test opportunities with varied characteristics
    opportunities = [
        {
            "name": "Quantum Computing Platform",
            "description": "Next-generation quantum computing platform for enterprise",
            "tam": 850000000.0,  # Smaller but growing market
            "growth_rate": 0.65,  # Explosive growth
            "competitor_count": 25,  # Highly competitive
            "industry": "quantum_computing",
            "funding_total": 50000000,  # Well funded
            "employee_count": 200,
            "revenue": 8000000,
            "valuation": 200000000,
            "risk_factors": [
                "technology_risk",
                "regulatory_compliance",
                "market_timing",
            ],
            "market_trends": ["Quantum advantage", "Enterprise adoption"],
        },
        {
            "name": "Sustainable Agriculture AI",
            "description": "AI-powered solutions for sustainable farming practices",
            "tam": 1200000000.0,
            "growth_rate": 0.32,
            "competitor_count": 12,  # Moderate competition
            "industry": "agricultural_technology",
            "funding_total": 8000000,
            "employee_count": 65,
            "revenue": 2500000,
            "valuation": 45000000,
            "risk_factors": ["weather_dependency", "market_education"],
            "market_trends": ["Climate change", "Food security"],
        },
        {
            "name": "Biotech Drug Discovery",
            "description": "AI-driven drug discovery platform for rare diseases",
            "tam": 3500000000.0,
            "growth_rate": 0.18,
            "competitor_count": 8,  # Lower competition
            "industry": "biotechnology",
            "funding_total": 15000000,
            "employee_count": 45,
            "revenue": 1200000,
            "valuation": 80000000,
            "risk_factors": ["regulatory_approval", "clinical_trials", "funding_gap"],
            "market_trends": ["Precision medicine", "Aging population"],
        },
        {
            "name": "E-commerce Automation",
            "description": "Automation tools for small business e-commerce operations",
            "tam": 450000000.0,  # Smaller market
            "growth_rate": 0.08,  # Slower growth
            "competitor_count": 35,  # Very crowded
            "industry": "e-commerce_software",
            "funding_total": 1500000,  # Limited funding
            "employee_count": 15,
            "revenue": 200000,
            "valuation": 8000000,
            "risk_factors": [
                "competitive_threat",
                "customer_concentration",
                "small_market",
            ],
            "market_trends": ["Digital transformation", "SMB automation"],
        },
        {
            "name": "Space Mining Robotics",
            "description": "Robotics solutions for asteroid mining and space resource extraction",
            "tam": 100000000000.0,  # Massive theoretical market
            "growth_rate": 0.05,  # Very early stage
            "competitor_count": 3,  # Very few competitors
            "industry": "space_technology",
            "funding_total": 200000000,  # High funding
            "employee_count": 180,
            "revenue": 0,  # No revenue yet
            "valuation": 500000000,
            "risk_factors": [
                "regulatory_approval",
                "technology_risk",
                "market_timing",
                "high_capex",
            ],
            "market_trends": ["Space commercialization", "Resource scarcity"],
        },
    ]

    print(f"📊 Analyzing {len(opportunities)} opportunities...\n")

    # Simulate realistic scoring
    results = []
    for i, opp in enumerate(opportunities, 1):
        print(f"🔍 {i}. {opp['name']}")

        # Calculate realistic score based on opportunity characteristics
        score = calculate_realistic_score(opp)

        # Determine RAG status
        if score >= 70:
            rag_status = "GREEN"
        elif score >= 40:
            rag_status = "AMBER"
        else:
            rag_status = "RED"

        results.append(
            {
                "name": opp["name"],
                "score": score,
                "rag_status": rag_status,
                "confidence": calculate_confidence(opp),
                "key_factors": get_key_factors(opp),
            }
        )

        print(f"   📈 Score: {score}")
        print(f"   🚦 Status: {rag_status}")
        print(f"   🎯 Confidence: {calculate_confidence(opp):.1%}")
        print(f"   📋 Key: {', '.join(get_key_factors(opp)[:2])}")
        print()

    # Summary
    print("📊 SCORING SUMMARY")
    print("=" * 40)

    scores = [r["score"] for r in results]
    rag_counts = {"RED": 0, "AMBER": 0, "GREEN": 0}

    for result in results:
        rag_counts[result["rag_status"]] += 1

    print(f"Average Score: {sum(scores) / len(scores):.1f}")
    print(f"Score Range: {min(scores):.0f} - {max(scores):.0f}")
    print()
    print("RAG Distribution:")
    print(f"  🟢 GREEN: {rag_counts['GREEN']}")
    print(f"  🟡 AMBER: {rag_counts['AMBER']}")
    print(f"  🔴 RED: {rag_counts['RED']}")

    # Show insights
    print("\n💡 KEY INSIGHTS")
    print("-" * 20)

    green_ops = [r for r in results if r["rag_status"] == "GREEN"]
    red_ops = [r for r in results if r["rag_status"] == "RED"]

    if green_ops:
        best = max(green_ops, key=lambda x: x["score"])
        print(f"🏆 Strongest: {best['name']} ({best['score']:.0f})")
        print(f"   Why: {', '.join(best['key_factors'][:2])}")

    if red_ops:
        worst = min(red_ops, key=lambda x: x["score"])
        print(f"⚠️  Riskiest: {worst['name']} ({worst['score']:.0f})")
        print(f"   Issues: {', '.join(worst['key_factors'][:2])}")


def calculate_realistic_score(opp):
    """Calculate a realistic RAG score based on opportunity characteristics"""

    # Start with neutral score
    score = 50.0

    # Market size scoring (log scale)
    tam = opp.get("tam", 0)
    if tam > 1000000000:  # > $1B
        score += 25
    elif tam > 100000000:  # $100M - $1B
        score += 15
    elif tam > 50000000:  # $50M - $100M
        score += 5
    else:
        score -= 15

    # Growth rate scoring
    growth = opp.get("growth_rate", 0)
    if growth > 0.5:  # > 50%
        score += 30
    elif growth > 0.3:  # 30-50%
        score += 25
    elif growth > 0.15:  # 15-30%
        score += 15
    elif growth > 0.05:  # 5-15%
        score += 5
    else:
        score -= 20

    # Competition scoring (fewer is better)
    competitors = opp.get("competitor_count", 10)
    if competitors <= 5:
        score += 20
    elif competitors <= 15:
        score += 10
    elif competitors <= 25:
        score -= 5
    else:
        score -= 15

    # Funding scoring
    funding = opp.get("funding_total", 0)
    if funding > 50000000:  # > $50M
        score += 20
    elif funding > 10000000:  # $10M - $50M
        score += 15
    elif funding > 2000000:  # $2M - $10M
        score += 10
    elif funding > 500000:  # $500K - $2M
        score += 5
    else:
        score -= 10

    # Revenue scoring
    revenue = opp.get("revenue", 0)
    if revenue > 5000000:  # > $5M
        score += 15
    elif revenue > 1000000:  # $1M - $5M
        score += 10
    elif revenue > 500000:  # $500K - $1M
        score += 5
    elif revenue > 0:  # Some revenue
        score += 2
    else:  # No revenue
        score -= 15

    # Risk factor penalties
    risk_factors = opp.get("risk_factors", [])
    for risk in risk_factors:
        if risk in ["regulatory_compliance", "technology_risk"]:
            score -= 15
        elif risk in ["market_timing", "funding_gap"]:
            score -= 20
        else:
            score -= 8

    # Ensure score is within bounds
    return max(0, min(100, score))


def calculate_confidence(opp):
    """Calculate confidence based on data completeness"""
    required_fields = ["tam", "growth_rate", "funding_total", "employee_count"]
    present_fields = sum(1 for field in required_fields if opp.get(field) is not None)

    # Base confidence on field completeness
    base_confidence = present_fields / len(required_fields)

    # Bonus for having revenue data
    if opp.get("revenue", 0) > 0:
        base_confidence += 0.1

    # Bonus for having fewer risk factors (more predictable)
    risk_count = len(opp.get("risk_factors", []))
    if risk_count <= 2:
        base_confidence += 0.1
    elif risk_count > 5:
        base_confidence -= 0.1

    return min(0.95, max(0.3, base_confidence))


def get_key_factors(opp):
    """Extract key factors that influenced the score"""
    factors = []

    # Market size
    tam = opp.get("tam", 0)
    if tam > 1000000000:
        factors.append("Large Market")
    elif tam < 100000000:
        factors.append("Small Market")

    # Growth
    growth = opp.get("growth_rate", 0)
    if growth > 0.3:
        factors.append("High Growth")
    elif growth < 0.1:
        factors.append("Low Growth")

    # Competition
    competitors = opp.get("competitor_count", 10)
    if competitors > 30:
        factors.append("Crowded Market")
    elif competitors < 10:
        factors.append("Low Competition")

    # Risk factors
    risk_factors = opp.get("risk_factors", [])
    if risk_factors:
        factors.append(f"{len(risk_factors)} Risks")

    # Funding stage
    funding = opp.get("funding_total", 0)
    if funding > 50000000:
        factors.append("Well Funded")
    elif funding < 2000000:
        factors.append("Early Stage")

    return factors[:3]  # Return top 3 factors


if __name__ == "__main__":
    test_realistic_rag_scoring()
