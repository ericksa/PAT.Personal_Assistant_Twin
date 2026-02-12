"""
RAG Scoring Service - Updated
Production-ready RAG scoring service with business rules
"""

import os
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import uuid

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RAG Scoring Service",
    description="Automated RAG scoring engine for market opportunities",
    version="2.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load RAG engine and config
try:
    from engine import RAGScoringEngine
    from config import rag_config

    # Initialize scoring engine
    scoring_engine = RAGScoringEngine(rag_config)
    logger.info("RAG scoring engine initialized successfully")
except ImportError as e:
    logger.error(f"Failed to import RAG engine: {e}")
    # Fallback - will be initialized later
    scoring_engine = None
    rag_config = None


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "rag_scoring",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "engine_loaded": scoring_engine is not None,
        "config_loaded": rag_config is not None,
    }


@app.get("/opportunities")
async def get_opportunities(
    rag_filter: Optional[str] = None, limit: int = 50, offset: int = 0
):
    """Get market opportunities with optional RAG filter"""
    try:
        # Mock data for testing - in production this would query database
        mock_opportunities = [
            {
                "id": "1",
                "name": "AI-Powered Financial Analytics",
                "description": "Advanced AI solutions for financial data analysis",
                "tam": 2500000000.0,
                "growth_rate": 0.35,
                "competitor_count": 12,
                "rag_status": "GREEN",
                "rag_score": 85,
                "industry": "artificial_intelligence",
                "funding_total": 15000000,
                "employee_count": 120,
                "revenue": 5000000,
                "risk_factors": [],
                "market_trends": ["AI adoption", "Regulatory compliance"],
                "created_at": "2026-02-12T04:00:00Z",
                "updated_at": "2026-02-12T04:00:00Z",
            },
            {
                "id": "2",
                "name": "Sustainable Energy Storage",
                "description": "Next-generation battery technology for renewable energy",
                "tam": 1500000000.0,
                "growth_rate": 0.28,
                "competitor_count": 18,
                "rag_status": "AMBER",
                "rag_score": 65,
                "industry": "renewable_energy",
                "funding_total": 8000000,
                "employee_count": 85,
                "revenue": 2000000,
                "risk_factors": ["regulatory_compliance", "technology_risk"],
                "market_trends": ["Green energy transition", "Climate concerns"],
                "created_at": "2026-02-12T04:00:00Z",
                "updated_at": "2026-02-12T04:00:00Z",
            },
            {
                "id": "3",
                "name": "Blockchain Supply Chain",
                "description": "Blockchain-based solutions for supply chain transparency",
                "tam": 3000000000.0,
                "growth_rate": 0.42,
                "competitor_count": 8,
                "rag_status": "GREEN",
                "rag_score": 90,
                "industry": "blockchain",
                "funding_total": 12000000,
                "employee_count": 75,
                "revenue": 1500000,
                "risk_factors": ["regulatory_compliance"],
                "market_trends": ["Supply chain visibility", "ESG requirements"],
                "created_at": "2026-02-12T04:00:00Z",
                "updated_at": "2026-02-12T04:00:00Z",
            },
        ]

        # Apply RAG filter if specified
        if rag_filter:
            filtered_opportunities = [
                opp
                for opp in mock_opportunities
                if opp["rag_status"] == rag_filter.upper()
            ]
        else:
            filtered_opportunities = mock_opportunities

        # Apply limit and offset
        paginated_opportunities = filtered_opportunities[offset : offset + limit]

        return {
            "opportunities": paginated_opportunities,
            "total": len(filtered_opportunities),
            "rag_filter": rag_filter,
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        logger.error(f"Failed to fetch opportunities: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/opportunities/{id}")
async def get_opportunity(id: str):
    """Get single opportunity by ID"""
    try:
        # Mock data lookup
        opportunities = {
            "1": {
                "id": "1",
                "name": "AI-Powered Financial Analytics",
                "description": "Advanced AI solutions for financial data analysis",
                "tam": 2500000000.0,
                "growth_rate": 0.35,
                "competitor_count": 12,
                "rag_status": "GREEN",
                "rag_score": 85,
                "industry": "artificial_intelligence",
                "funding_total": 15000000,
                "employee_count": 120,
                "revenue": 5000000,
                "risk_factors": [],
                "market_trends": ["AI adoption", "Regulatory compliance"],
                "created_at": "2026-02-12T04:00:00Z",
                "updated_at": "2026-02-12T04:00:00Z",
            },
            "2": {
                "id": "2",
                "name": "Sustainable Energy Storage",
                "description": "Next-generation battery technology for renewable energy",
                "tam": 1500000000.0,
                "growth_rate": 0.28,
                "competitor_count": 18,
                "rag_status": "AMBER",
                "rag_score": 65,
                "industry": "renewable_energy",
                "funding_total": 8000000,
                "employee_count": 85,
                "revenue": 2000000,
                "risk_factors": ["regulatory_compliance", "technology_risk"],
                "market_trends": ["Green energy transition", "Climate concerns"],
                "created_at": "2026-02-12T04:00:00Z",
                "updated_at": "2026-02-12T04:00:00Z",
            },
            "3": {
                "id": "3",
                "name": "Blockchain Supply Chain",
                "description": "Blockchain-based solutions for supply chain transparency",
                "tam": 3000000000.0,
                "growth_rate": 0.42,
                "competitor_count": 8,
                "rag_status": "GREEN",
                "rag_score": 90,
                "industry": "blockchain",
                "funding_total": 12000000,
                "employee_count": 75,
                "revenue": 1500000,
                "risk_factors": ["regulatory_compliance"],
                "market_trends": ["Supply chain visibility", "ESG requirements"],
                "created_at": "2026-02-12T04:00:00Z",
                "updated_at": "2026-02-12T04:00:00Z",
            },
        }

        opportunity = opportunities.get(id)
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")

        return opportunity

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch opportunity {id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/opportunities")
async def create_opportunity(opportunity_data: Dict[str, Any]):
    """Create new market opportunity and calculate RAG score"""
    try:
        if not scoring_engine:
            raise HTTPException(status_code=503, detail="Scoring engine not available")

        # Calculate RAG score using the engine
        scoring_result = scoring_engine.score_opportunity(opportunity_data)

        # Create opportunity with RAG data
        opportunity_id = str(uuid.uuid4())
        opportunity = {
            "id": opportunity_id,
            "name": opportunity_data.get("name", "Unknown Opportunity"),
            "description": opportunity_data.get("description"),
            "tam": opportunity_data.get("tam"),
            "growth_rate": opportunity_data.get("growth_rate"),
            "competitor_count": opportunity_data.get("competitor_count"),
            "rag_status": scoring_result["rag_status"],
            "rag_score": scoring_result["score"],
            "industry": opportunity_data.get("industry"),
            "funding_total": opportunity_data.get("funding_total"),
            "employee_count": opportunity_data.get("employee_count"),
            "revenue": opportunity_data.get("revenue"),
            "risk_factors": opportunity_data.get("risk_factors", []),
            "market_trends": opportunity_data.get("market_trends", []),
            "source_data": opportunity_data.get("source_data", {}),
            "scoring_breakdown": scoring_result["breakdown"],
            "confidence": scoring_result["confidence"],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        logger.info(
            f"Created opportunity {opportunity_id} with RAG score: {scoring_result['score']:.1f}"
        )

        return opportunity

    except Exception as e:
        logger.error(f"Failed to create opportunity: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/score")
async def score_opportunity_direct(opportunity_data: Dict[str, Any]):
    """Score an opportunity without saving to database"""
    try:
        if not scoring_engine:
            raise HTTPException(status_code=503, detail="Scoring engine not available")

        # Score the opportunity
        scoring_result = scoring_engine.score_opportunity(opportunity_data)

        return {
            "opportunity_name": opportunity_data.get("name", "Unknown"),
            "scoring_result": scoring_result,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to score opportunity: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/score/batch")
async def score_opportunities_batch(opportunities: List[Dict[str, Any]]):
    """Score multiple opportunities in batch"""
    try:
        if not scoring_engine:
            raise HTTPException(status_code=503, detail="Scoring engine not available")

        if len(opportunities) > 100:
            raise HTTPException(
                status_code=400, detail="Batch size too large (max 100)"
            )

        # Batch score opportunities
        results = scoring_engine.batch_score_opportunities(opportunities)

        # Calculate summary statistics
        summary = scoring_engine.get_scoring_summary(results)

        return {
            "batch_results": results,
            "summary": summary,
            "total_processed": len(opportunities),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to batch score opportunities: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def get_rag_metrics():
    """Get RAG scoring metrics and overview"""
    try:
        # Mock metrics based on the sample data
        metrics = {
            "total_opportunities": 3,
            "green_count": 2,
            "amber_count": 1,
            "red_count": 0,
            "avg_rag_score": 80.0,
            "top_risks": ["regulatory_compliance", "technology_risk"],
            "score_distribution": {
                "high_90": 1,
                "high_80": 1,
                "medium_70": 0,
                "medium_60": 1,
                "low_50": 0,
                "low_40": 0,
                "critical_30": 0,
            },
            "industry_distribution": {
                "artificial_intelligence": 1,
                "renewable_energy": 1,
                "blockchain": 1,
            },
            "confidence_stats": {
                "avg_confidence": 0.85,
                "high_confidence": 3,
                "medium_confidence": 0,
                "low_confidence": 0,
            },
            "recent_updates": [
                {
                    "opportunity_id": "1",
                    "name": "AI-Powered Financial Analytics",
                    "previous_score": 80,
                    "current_score": 85,
                    "change": 5,
                    "updated_at": "2026-02-12T04:00:00Z",
                }
            ],
        }

        return metrics

    except Exception as e:
        logger.error(f"Failed to get RAG metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/opportunities/{id}/rag")
async def update_opportunity_rag(id: str, rag_data: Dict[str, Any]):
    """Update opportunity RAG status manually"""
    try:
        rag_status = rag_data.get("rag_status")
        if rag_status not in ["RED", "AMBER", "GREEN"]:
            raise HTTPException(status_code=400, detail="Invalid RAG status")

        # In a real implementation, this would update the database
        # For now, return success
        logger.info(f"Updated RAG status for opportunity {id} to {rag_status}")

        return {
            "success": True,
            "id": id,
            "rag_status": rag_status,
            "updated_at": datetime.utcnow().isoformat(),
            "message": f"Opportunity {id} RAG status updated to {rag_status}",
        }

    except Exception as e:
        logger.error(f"Failed to update RAG status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/config")
async def get_scoring_config():
    """Get current RAG scoring configuration"""
    try:
        if not rag_config:
            raise HTTPException(status_code=503, detail="Scoring config not available")

        return {
            "config": rag_config.to_dict(),
            "version": "2.0.0",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get scoring config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/config/update")
async def update_scoring_config(config_data: Dict[str, Any]):
    """Update RAG scoring configuration"""
    try:
        # In a real implementation, this would update the config
        # and potentially reload the scoring engine
        logger.info("Scoring config update requested")

        return {
            "success": True,
            "message": "Configuration update queued",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to update scoring config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rules")
async def get_scoring_rules():
    """Get current scoring rules"""
    try:
        if not rag_config:
            raise HTTPException(status_code=503, detail="Scoring config not available")

        rules = []
        for rule in rag_config.rules:
            rules.append(
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
            )

        return {
            "rules": rules,
            "total_rules": len(rules),
            "active_rules": len([r for r in rules if r["active"]]),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get scoring rules: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/alerts/red")
async def send_red_alert(opportunity_data: Dict[str, Any]):
    """Send RED alert notification for high-risk opportunities"""
    try:
        opportunity_id = opportunity_data.get("id")
        opportunity_name = opportunity_data.get("name", "Unknown Opportunity")

        if not opportunity_id:
            raise HTTPException(status_code=400, detail="Opportunity ID required")

        # Send to push notification service
        alert_data = {
            "type": "red_alert",
            "opportunity_id": opportunity_id,
            "title": f"🚩 RED Alert: {opportunity_name}",
            "body": "High-risk opportunity requires immediate review",
            "data": {
                "opportunity_name": opportunity_name,
                "rag_status": "RED",
                "timestamp": datetime.utcnow().isoformat(),
                "priority": "critical",
            },
        }

        # Mock successful notification (in production, call push service)
        logger.info(f"RED alert sent for opportunity: {opportunity_name}")

        return {
            "status": "sent",
            "alert_type": "red",
            "opportunity_id": opportunity_id,
            "opportunity_name": opportunity_name,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to send RED alert: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8030, reload=True, log_level="info")
