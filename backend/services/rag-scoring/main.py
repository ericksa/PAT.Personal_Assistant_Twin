"""
RAG Scoring Engine
Automated RAG (Red-Amber-Green) scoring for market opportunities
"""

import os
import asyncio
import logging
import pickle
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import json
import numpy as np
import pandas as pd
from dataclasses import dataclass
import yaml

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import httpx
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# ML Libraries
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RAG Scoring Service",
    description="Automated RAG scoring engine for market opportunities",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://llm:llm@localhost:5432/llm")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Redis setup for caching
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
import redis

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# External API Keys
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")
CRUNCHBASE_API_KEY = os.getenv("CRUNCHBASE_API_KEY", "")
GOOGLE_TRENDS_API_KEY = os.getenv("GOOGLE_TRENDS_API_KEY", "")

# RAG Scoring Configuration
RED_THRESHOLD = int(os.getenv("RED_THRESHOLD", "30"))
AMBER_THRESHOLD = int(os.getenv("AMBER_THRESHOLD", "60"))
SCORING_BATCH_SIZE = int(os.getenv("SCORING_BATCH_SIZE", "100"))
SCORING_INTERVAL = int(os.getenv("SCORING_INTERVAL", "3600"))  # 1 hour

# Model paths
MODEL_CACHE_PATH = Path("/app/models")
FEATURE_ENGINE_PATH = Path("/app/features")
MODEL_CACHE_PATH.mkdir(parents=True, exist_ok=True)
FEATURE_ENGINE_PATH.mkdir(parents=True, exist_ok=True)


# Scoring rules configuration
@dataclass
class RAGScoringConfig:
    """Configuration for RAG scoring rules"""

    growth_rate_thresholds: Dict[str, Tuple[float, float]] = None
    funding_thresholds: Dict[str, Tuple[float, float]] = None
    market_size_thresholds: Dict[str, Tuple[float, float]] = None
    risk_factors: Dict[str, int] = None
    competitive_density_thresholds: Dict[str, int] = None

    def __post_init__(self):
        if self.growth_rate_thresholds is None:
            self.growth_rate_thresholds = {
                "RED": (0.0, 0.05),  # < 5% growth
                "AMBER": (0.05, 0.15),  # 5-15% growth
                "GREEN": (0.15, 10.0),  # > 15% growth
            }

        if self.funding_thresholds is None:
            self.funding_thresholds = {
                "RED": (0.0, 1e6),  # < $1M
                "AMBER": (1e6, 10e6),  # $1M-$10M
                "GREEN": (10e6, 100e9),  # > $10M
            }

        if self.market_size_thresholds is None:
            self.market_size_thresholds = {
                "RED": (0.0, 1e8),  # < $100M
                "AMBER": (1e8, 1e9),  # $100M-$1B
                "GREEN": (1e9, 100e9),  # > $1B
            }

        if self.risk_factors is None:
            self.risk_factors = {
                "regulatory_risk": -20,
                "technology_risk": -15,
                "market_risk": -10,
                "competitive_risk": -12,
                "execution_risk": -8,
                "funding_gap": -25,
            }

        if self.competitive_density_thresholds is None:
            self.competitive_density_thresholds = {
                "RED": 20,  # > 20 competitors
                "AMBER": 10,  # 10-20 competitors
                "GREEN": 5,  # < 10 competitors
            }


class RAGScoringEngine:
    """Core RAG scoring engine"""

    def __init__(self, config: RAGScoringConfig):
        self.config = config
        self.model = None
        self.scaler = None
        self.feature_names = []

    def load_or_train_model(self):
        """Load existing model or train new one"""
        model_path = MODEL_CACHE_PATH / "rag_model.pkl"
        scaler_path = MODEL_CACHE_PATH / "scaler.pkl"

        if model_path.exists() and scaler_path.exists():
            try:
                with open(model_path, "rb") as f:
                    self.model = pickle.load(f)
                with open(scaler_path, "rb") as f:
                    self.scaler = pickle.load(f)
                logger.info("Loaded existing RAG model")
                return
            except Exception as e:
                logger.warning(f"Failed to load model: {e}")

        # Train new model if none exists
        self.train_model()

    def train_model(self, historical_data: Optional[pd.DataFrame] = None):
        """Train the RAG scoring model"""
        logger.info("Training RAG scoring model...")

        # Generate synthetic training data if none provided
        if historical_data is None:
            historical_data = self.generate_synthetic_data()

        # Prepare features and labels
        feature_columns = [
            "growth_rate",
            "funding_total",
            "market_size",
            "competitor_count",
            "risk_score",
            "market_maturity",
        ]

        X = historical_data[feature_columns]

        # Create RAG labels based on rules
        y = []
        for _, row in historical_data.iterrows():
            rag_score = self.calculate_rule_based_score(row)
            if rag_score >= AMBER_THRESHOLD:
                label = "GREEN"
            elif rag_score >= RED_THRESHOLD:
                label = "AMBER"
            else:
                label = "RED"
            y.append(label)

        # Encode labels
        from sklearn.preprocessing import LabelEncoder

        le = LabelEncoder()
        y_encoded = le.fit_transform(y)

        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
        )

        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Train Random Forest model
        self.model = RandomForestClassifier(
            n_estimators=100, max_depth=10, random_state=42, class_weight="balanced"
        )

        self.model.fit(X_train_scaled, y_train)

        # Evaluate model
        y_pred = self.model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        logger.info(f"Model accuracy: {accuracy:.3f}")

        # Save model
        with open(MODEL_CACHE_PATH / "rag_model.pkl", "wb") as f:
            pickle.dump(self.model, f)
        with open(MODEL_CACHE_PATH / "scaler.pkl", "wb") as f:
            pickle.dump(self.scaler, f)
        with open(MODEL_CACHE_PATH / "label_encoder.pkl", "wb") as f:
            pickle.dump(le, f)

        # Save feature importance
        feature_importance = pd.DataFrame(
            {"feature": feature_columns, "importance": self.model.feature_importances_}
        ).sort_values("importance", ascending=False)

        feature_importance.to_csv(
            MODEL_CACHE_PATH / "feature_importance.csv", index=False
        )

        logger.info("Model training completed")

    def generate_synthetic_data(self, n_samples: int = 1000) -> pd.DataFrame:
        """Generate synthetic training data"""
        np.random.seed(42)

        data = []
        for _ in range(n_samples):
            # Generate realistic synthetic data
            growth_rate = np.random.exponential(
                0.15
            )  # Most opportunities have moderate growth
            funding_total = np.random.lognormal(
                15, 1.5
            )  # Log-normal distribution for funding
            market_size = np.random.lognormal(18, 2)  # Market sizes
            competitor_count = np.random.poisson(
                8
            )  # Poisson distribution for competitors

            # Risk factors
            risk_score = np.random.normal(50, 20)  # Risk scores around 50
            risk_score = max(0, min(100, risk_score))  # Clamp to 0-100

            # Market maturity (0-100 scale)
            market_maturity = np.random.beta(2, 2) * 100

            data.append(
                {
                    "growth_rate": growth_rate,
                    "funding_total": funding_total,
                    "market_size": market_size,
                    "competitor_count": competitor_count,
                    "risk_score": risk_score,
                    "market_maturity": market_maturity,
                }
            )

        return pd.DataFrame(data)

    def calculate_rule_based_score(self, features: Dict[str, Any]) -> float:
        """Calculate RAG score using rule-based approach"""
        score = 50  # Start with neutral score

        # Growth rate scoring
        growth_rate = features.get("growth_rate", 0)
        if growth_rate >= 0.15:  # > 15%
            score += 25
        elif growth_rate >= 0.05:  # 5-15%
            score += 10
        else:  # < 5%
            score -= 20

        # Funding scoring
        funding = features.get("funding_total", 0)
        if funding >= 10e6:  # > $10M
            score += 20
        elif funding >= 1e6:  # $1M-$10M
            score += 5
        else:  # < $1M
            score -= 15

        # Market size scoring
        market_size = features.get("market_size", 0)
        if market_size >= 1e9:  # > $1B
            score += 25
        elif market_size >= 1e8:  # $100M-$1B
            score += 10
        else:  # < $100M
            score -= 10

        # Competitor count scoring (fewer is better)
        competitor_count = features.get("competitor_count", 10)
        if competitor_count <= 5:
            score += 15
        elif competitor_count <= 15:
            score += 5
        else:
            score -= 10

        # Risk factor penalties
        risk_factors = features.get("risk_factors", [])
        for risk in risk_factors:
            penalty = self.config.risk_factors.get(risk, -5)
            score += penalty

        # Market maturity bonus
        market_maturity = features.get("market_maturity", 50)
        if market_maturity >= 70:  # Mature market
            score += 10
        elif market_maturity <= 30:  # Very early market
            score -= 15

        # Ensure score is within 0-100 range
        return max(0, min(100, score))

    def predict_rag(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Predict RAG status and score for opportunity"""
        if self.model is None:
            self.load_or_train_model()

        # Rule-based score as fallback
        rule_score = self.calculate_rule_based_score(features)

        # ML prediction if model is available
        if self.model is not None and self.scaler is not None:
            try:
                # Prepare features for ML model
                feature_vector = np.array(
                    [
                        features.get("growth_rate", 0),
                        features.get("funding_total", 0),
                        features.get("market_size", 0),
                        features.get("competitor_count", 0),
                        features.get("risk_score", 50),
                        features.get("market_maturity", 50),
                    ]
                ).reshape(1, -1)

                # Scale and predict
                scaled_features = self.scaler.transform(feature_vector)
                prediction = self.model.predict(scaled_features)[0]
                probability = self.model.predict_proba(scaled_features)[0]

                # Convert prediction to RAG status
                from sklearn.preprocessing import LabelEncoder

                with open(MODEL_CACHE_PATH / "label_encoder.pkl", "rb") as f:
                    le = pickle.load(f)

                rag_status = le.inverse_transform([prediction])[0]

                # Use rule-based score as primary, ML confidence as secondary
                ml_confidence = max(probability)

            except Exception as e:
                logger.warning(f"ML prediction failed, using rule-based: {e}")
                ml_confidence = 0.5
                rag_status = "AMBER"  # Default to amber if ML fails
        else:
            # Use rule-based classification
            ml_confidence = 0.7
            if rule_score >= AMBER_THRESHOLD:
                rag_status = "GREEN"
            elif rule_score >= RED_THRESHOLD:
                rag_status = "AMBER"
            else:
                rag_status = "RED"

        # Calculate final score (blend rule-based and confidence)
        final_score = int(rule_score * 0.7 + ml_confidence * 30)

        return {
            "rag_status": rag_status,
            "rag_score": final_score,
            "rule_score": int(rule_score),
            "ml_confidence": float(ml_confidence),
            "feature_importance": self.get_feature_importance() if self.model else {},
        }

    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from trained model"""
        if self.model is None:
            return {}

        feature_names = [
            "growth_rate",
            "funding_total",
            "market_size",
            "competitor_count",
            "risk_score",
            "market_maturity",
        ]

        return dict(zip(feature_names, self.model.feature_importances_))


# Global scoring engine
scoring_engine = RAGScoringEngine(RAGScoringConfig())


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "rag_scoring",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "model_loaded": scoring_engine.model is not None,
    }


@app.get("/opportunities")
async def get_opportunities(
    rag_filter: Optional[str] = None, limit: int = 50, offset: int = 0
):
    """Get market opportunities with optional RAG filter"""
    try:
        # Query database for opportunities
        db = SessionLocal()

        query = """
            SELECT id, name, description, tam, growth_rate, competitor_count,
                   rag_status, rag_score, market_trends, risk_factors,
                   source_data, created_at, updated_at
            FROM market_opportunities 
            WHERE (:rag_filter IS NULL OR rag_status = :rag_filter)
            ORDER BY rag_score DESC, updated_at DESC
            LIMIT :limit OFFSET :offset
        """

        result = db.execute(
            text(query), {"rag_filter": rag_filter, "limit": limit, "offset": offset}
        )

        opportunities = []
        for row in result:
            opportunities.append(
                {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "tam": float(row[3]) if row[3] else None,
                    "growth_rate": float(row[4]) if row[4] else None,
                    "competitor_count": row[5],
                    "rag_status": row[6],
                    "rag_score": row[7],
                    "market_trends": json.loads(row[8]) if row[8] else [],
                    "risk_factors": json.loads(row[9]) if row[9] else [],
                    "source_data": json.loads(row[10]) if row[10] else {},
                    "created_at": row[11].isoformat(),
                    "updated_at": row[12].isoformat(),
                }
            )

        db.close()

        return {
            "opportunities": opportunities,
            "total": len(opportunities),
            "rag_filter": rag_filter,
        }

    except Exception as e:
        logger.error(f"Failed to fetch opportunities: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/opportunities/{id}")
async def get_opportunity(id: str):
    """Get single opportunity by ID"""
    try:
        db = SessionLocal()

        query = """
            SELECT id, name, description, tam, growth_rate, competitor_count,
                   rag_status, rag_score, market_trends, risk_factors,
                   source_data, created_at, updated_at
            FROM market_opportunities 
            WHERE id = :id
        """

        result = db.execute(text(query), {"id": id}).fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Opportunity not found")

        opportunity = {
            "id": result[0],
            "name": result[1],
            "description": result[2],
            "tam": float(result[3]) if result[3] else None,
            "growth_rate": float(result[4]) if result[4] else None,
            "competitor_count": result[5],
            "rag_status": result[6],
            "rag_score": result[7],
            "market_trends": json.loads(result[8]) if result[8] else [],
            "risk_factors": json.loads(result[9]) if result[9] else [],
            "source_data": json.loads(result[10]) if result[10] else {},
            "created_at": result[11].isoformat(),
            "updated_at": result[12].isoformat(),
        }

        db.close()

        return opportunity

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch opportunity {id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/opportunities")
async def create_opportunity(opportunity: Dict[str, Any]):
    """Create new market opportunity and calculate RAG score"""
    try:
        # Calculate RAG score
        rag_result = scoring_engine.predict_rag(opportunity)

        # Store in database
        db = SessionLocal()

        query = """
            INSERT INTO market_opportunities 
            (id, name, description, tam, growth_rate, competitor_count,
             rag_status, rag_score, market_trends, risk_factors, source_data)
            VALUES (:id, :name, :description, :tam, :growth_rate, :competitor_count,
                    :rag_status, :rag_score, :market_trends, :risk_factors, :source_data)
            RETURNING created_at
        """

        import uuid

        opportunity_id = str(uuid.uuid4())

        result = db.execute(
            text(query),
            {
                "id": opportunity_id,
                "name": opportunity.get("name"),
                "description": opportunity.get("description"),
                "tam": opportunity.get("tam"),
                "growth_rate": opportunity.get("growth_rate"),
                "competitor_count": opportunity.get("competitor_count"),
                "rag_status": rag_result["rag_status"],
                "rag_score": rag_result["rag_score"],
                "market_trends": json.dumps(opportunity.get("market_trends", [])),
                "risk_factors": json.dumps(opportunity.get("risk_factors", [])),
                "source_data": json.dumps(opportunity.get("source_data", {})),
            },
        )

        db.commit()
        created_at = result.fetchone()[0]
        db.close()

        # Send push notification if RED
        if rag_result["rag_status"] == "RED":
            await send_red_alert(opportunity_id, opportunity.get("name", "Unknown"))

        return {
            "id": opportunity_id,
            "name": opportunity.get("name"),
            "description": opportunity.get("description"),
            "tam": opportunity.get("tam"),
            "growth_rate": opportunity.get("growth_rate"),
            "competitor_count": opportunity.get("competitor_count"),
            "rag_status": rag_result["rag_status"],
            "rag_score": rag_result["rag_score"],
            "market_trends": opportunity.get("market_trends", []),
            "risk_factors": opportunity.get("risk_factors", []),
            "source_data": opportunity.get("source_data", {}),
            "created_at": created_at.isoformat(),
            "updated_at": created_at.isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to create opportunity: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def get_rag_metrics():
    """Get RAG scoring metrics and overview"""
    try:
        db = SessionLocal()

        # Get counts by RAG status
        query = """
            SELECT rag_status, COUNT(*) as count, AVG(rag_score) as avg_score
            FROM market_opportunities 
            GROUP BY rag_status
        """

        result = db.execute(text(query)).fetchall()

        metrics = {
            "total_opportunities": 0,
            "green_count": 0,
            "amber_count": 0,
            "red_count": 0,
            "avg_rag_score": 0.0,
            "top_risks": [],
        }

        total_score = 0
        total_count = 0

        for row in result:
            status = row[0]
            count = row[1]
            avg_score = float(row[2])

            metrics["total_opportunities"] += count

            if status == "GREEN":
                metrics["green_count"] = count
            elif status == "AMBER":
                metrics["amber_count"] = count
            elif status == "RED":
                metrics["red_count"] = count

            total_score += avg_score * count
            total_count += count

        if total_count > 0:
            metrics["avg_rag_score"] = total_score / total_count

        # Get top risks
        risk_query = """
            SELECT risk_factors, COUNT(*) as count
            FROM market_opportunities 
            WHERE rag_status = 'RED'
            GROUP BY risk_factors
            ORDER BY count DESC
            LIMIT 5
        """

        risk_result = db.execute(text(risk_query)).fetchall()
        metrics["top_risks"] = [row[0] for row in risk_result]

        db.close()

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

        db = SessionLocal()

        query = """
            UPDATE market_opportunities 
            SET rag_status = :rag_status, updated_at = :updated_at
            WHERE id = :id
        """

        result = db.execute(
            text(query),
            {"id": id, "rag_status": rag_status, "updated_at": datetime.utcnow()},
        )

        db.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Opportunity not found")

        db.close()

        # Send notification if status changed to RED
        if rag_status == "RED":
            # Fetch opportunity name for notification
            db = SessionLocal()
            name_result = db.execute(
                text("SELECT name FROM market_opportunities WHERE id = :id"), {"id": id}
            ).fetchone()
            db.close()

            if name_result:
                await send_red_alert(id, name_result[0])

        return {"success": True, "id": id, "rag_status": rag_status}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update RAG status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def send_red_alert(opportunity_id: str, opportunity_name: str):
    """Send push notification for RED opportunities"""
    try:
        # This would integrate with push notification service
        notification_data = {
            "type": "red_alert",
            "opportunity_id": opportunity_id,
            "title": f"🚩 RED Alert: {opportunity_name}",
            "body": "High-risk opportunity requires immediate review",
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Send to push notification service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://push-notifications:8060/notify", json=notification_data
            )
            response.raise_for_status()

        logger.info(f"Red alert sent for opportunity: {opportunity_name}")

    except Exception as e:
        logger.error(f"Failed to send red alert: {str(e)}")


@app.post("/model/retrain")
async def retrain_model(background_tasks: BackgroundTasks):
    """Trigger model retraining"""
    background_tasks.add_task(retrain_model_task)
    return {"status": "retraining_started"}


async def retrain_model_task():
    """Background task for model retraining"""
    try:
        # Fetch historical data
        db = SessionLocal()
        query = """
            SELECT tam, growth_rate, competitor_count, risk_factors, rag_status
            FROM market_opportunities 
            WHERE created_at > :cutoff_date
            ORDER BY created_at DESC
            LIMIT 1000
        """

        cutoff_date = datetime.utcnow() - timedelta(days=30)
        result = db.execute(text(query), {"cutoff_date": cutoff_date}).fetchall()

        if len(result) < 50:  # Need minimum data for training
            logger.info("Insufficient data for model retraining")
            return

        # Convert to DataFrame
        historical_data = pd.DataFrame(
            [
                {
                    "market_size": row[0],
                    "growth_rate": row[1],
                    "competitor_count": row[2],
                    "risk_score": len(json.loads(row[3])) * 10 if row[3] else 0,
                    "rag_status": row[4],
                }
                for row in result
            ]
        )

        db.close()

        # Retrain model
        scoring_engine.train_model(historical_data)

        logger.info("Model retraining completed successfully")

    except Exception as e:
        logger.error(f"Model retraining failed: {str(e)}")


if __name__ == "__main__":
    # Initialize model on startup
    scoring_engine.load_or_train_model()

    uvicorn.run("main:app", host="0.0.0.0", port=8030, reload=True, log_level="info")
