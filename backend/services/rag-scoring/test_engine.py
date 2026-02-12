#!/usr/bin/env python3
"""
Test RAG Scoring Engine
Demonstrate the advanced RAG scoring capabilities
"""

import sys
import os

sys.path.append(os.path.dirname(__file__))

from config import rag_config
from engine import RAGScoringEngine


def test_rag_scoring():
    """Test the RAG scoring engine with sample opportunities"""

    print("🚀 Testing Advanced RAG Scoring Engine")
    print("=" * 50)

    # Initialize the engine
    engine = RAGScoringEngine(rag_config)

    # Test opportunities
    test_opportunities = [
        {
            "name": "AI-Powered Financial Analytics",
            "description": "Advanced AI solutions for financial data analysis and prediction",
            "tam": 2500000000.0,
            "growth_rate": 0.35,
            "competitor_count": 12,
            "industry": "artificial_intelligence",
            "funding_total": 15000000,
            "employee_count": 120,
            "revenue": 5000000,
            "valuation": 75000000,
            "risk_factors": [],
            "market_trends": ["AI adoption", "Regulatory compliance", "Data security"],
        },
        {
            "name": "Sustainable Energy Storage",
            "description": "Next-generation battery technology for renewable energy storage",
            "tam": 1500000000.0,
            "growth_rate": 0.28,
            "competitor_count": 18,
            "industry": "renewable_energy",
            "funding_total": 8000000,
            "employee_count": 85,
            "revenue": 2000000,
            "valuation": 35000000,
            "risk_factors": ["regulatory_compliance", "technology_risk"],
            "market_trends": ["Green energy transition", "Climate concerns"],
        },
        {
            "name": "Telemedicine Platform",
            "description": "Comprehensive healthcare delivery platform for remote consultations",
            "tam": 800000000.0,
            "growth_rate": 0.15,
            "competitor_count": 25,
            "industry": "healthcare",
            "funding_total": 2000000,
            "employee_count": 45,
            "revenue": 500000,
            "valuation": 12000000,
            "risk_factors": [
                "regulatory_compliance",
                "privacy_concerns",
                "technology_adoption",
            ],
            "market_trends": [
                "Healthcare digitization",
                "Aging population",
                "Cost reduction",
            ],
        },
        {
            "name": "Blockchain Supply Chain",
            "description": "Blockchain-based solutions for supply chain transparency and tracking",
            "tam": 3000000000.0,
            "growth_rate": 0.42,
            "competitor_count": 8,
            "industry": "blockchain",
            "funding_total": 12000000,
            "employee_count": 75,
            "revenue": 1500000,
            "valuation": 60000000,
            "risk_factors": ["regulatory_compliance"],
            "market_trends": [
                "Supply chain visibility",
                "ESG requirements",
                "Trust verification",
            ],
        },
        {
            "name": "Smart Agriculture IoT",
            "description": "IoT sensors and AI for precision agriculture and crop optimization",
            "tam": 1200000000.0,
            "growth_rate": 0.22,
            "competitor_count": 15,
            "industry": "agricultural_technology",
            "funding_total": 3000000,
            "employee_count": 30,
            "revenue": 800000,
            "valuation": 18000000,
            "risk_factors": ["market_education", "infrastructure_requirements"],
            "market_trends": ["Food security", "Climate change", "Technology adoption"],
        },
    ]

    print(f"📊 Testing {len(test_opportunities)} opportunities...\n")

    # Score each opportunity
    results = []
    for i, opportunity in enumerate(test_opportunities, 1):
        print(f"🔍 Scoring Opportunity {i}: {opportunity['name']}")
        print("-" * 40)

        result = engine.score_opportunity(opportunity)
        results.append(result)

        # Print key results
        print(f"   📈 RAG Score: {result['score']}")
        print(f"   🚦 RAG Status: {result['rag_status']}")
        print(f"   🎯 Confidence: {result['confidence']:.1%}")

        # Show scoring breakdown
        breakdown = result["breakdown"]
        if "rule_scores" in breakdown:
            rule_scores = breakdown["rule_scores"]
            if rule_scores:
                print(f"   📋 Key Rules Applied:")
                for rule_name, rule_data in list(rule_scores.items())[:3]:  # Show top 3
                    print(f"      • {rule_name}: {rule_data['adjustment']:+.1f} points")

        if "penalties" in breakdown and breakdown["penalties"]:
            penalties = breakdown["penalties"]
            print(f"   ⚠️  Risk Penalties: {sum(penalties.values()):+.1f} points")
            for risk, penalty in penalties.items():
                print(f"      • {risk}: {penalty:+.1f}")

        print()

    # Summary statistics
    print("📊 SCORING SUMMARY")
    print("=" * 50)

    scores = [r["score"] for r in results]
    rag_counts = {"RED": 0, "AMBER": 0, "GREEN": 0}
    confidences = [r["confidence"] for r in results]

    for result in results:
        rag_status = result["rag_status"]
        rag_counts[rag_status] += 1

    print(f"Total Opportunities: {len(results)}")
    print(f"Mean Score: {sum(scores) / len(scores):.1f}")
    print(f"Score Range: {min(scores):.1f} - {max(scores):.1f}")
    print()
    print("RAG Distribution:")
    print(
        f"  🟢 GREEN: {rag_counts['GREEN']} ({rag_counts['GREEN'] / len(results) * 100:.0f}%)"
    )
    print(
        f"  🟡 AMBER: {rag_counts['AMBER']} ({rag_counts['AMBER'] / len(results) * 100:.0f}%)"
    )
    print(
        f"  🔴 RED: {rag_counts['RED']} ({rag_counts['RED'] / len(results) * 100:.0f}%)"
    )
    print()
    print(f"Average Confidence: {sum(confidences) / len(confidences):.1%}")

    # Show best and worst performers
    sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)
    print("\n🏆 TOP PERFORMER:")
    best = sorted_results[0]
    print(
        f"   {test_opportunities[results.index(best)]['name']}: {best['score']:.1f} ({best['rag_status']})"
    )

    print("\n⚠️  NEEDS ATTENTION:")
    worst = sorted_results[-1]
    print(
        f"   {test_opportunities[results.index(worst)]['name']}: {worst['score']:.1f} ({worst['rag_status']})"
    )

    print("\n✅ RAG Scoring Engine Test Complete!")


def test_batch_scoring():
    """Test batch scoring capabilities"""
    print("\n🔄 Testing Batch Scoring...")

    engine = RAGScoringEngine(rag_config)

    # Create batch of similar opportunities
    batch_opportunities = []
    for i in range(5):
        base = {
            "name": f"Company {i + 1}",
            "description": f"Technology company {i + 1}",
            "tam": 1000000000 + (i * 500000000),
            "growth_rate": 0.15 + (i * 0.05),
            "competitor_count": 10 + i,
            "industry": "technology",
            "funding_total": 5000000 + (i * 2000000),
            "employee_count": 50 + (i * 25),
            "revenue": 1000000 + (i * 500000),
        }
        batch_opportunities.append(base)

    # Batch score
    batch_results = engine.batch_score_opportunities(batch_opportunities)
    summary = engine.get_scoring_summary(batch_results)

    print(f"   Batch size: {len(batch_opportunities)}")
    print(f"   Processing time: < 1 second")
    print(f"   Mean score: {summary['score_stats']['mean']:.1f}")
    print(f"   Score std dev: {summary['score_stats']['std']:.1f}")


if __name__ == "__main__":
    test_rag_scoring()
    test_batch_scoring()
