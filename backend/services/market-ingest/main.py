"""
Market Data Ingestion Service
Automated market data collection from multiple sources
"""

import os
import asyncio
import logging
import aiohttp
import redis
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

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
    title="Market Ingestion Service",
    description="Market data collection and processing",
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

# External API Keys
CRUNCHBASE_API_KEY = os.getenv("CRUNCHBASE_API_KEY", "")
LINKEDIN_API_KEY = os.getenv("LINKEDIN_API_KEY", "")
SEC_API_KEY = os.getenv("SEC_API_KEY", "")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

# Redis for caching
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# Scraping Configuration
CONCURRENT_REQUESTS = int(os.getenv("CONCURRENT_REQUESTS", "5"))
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "1"))
USER_AGENT = os.getenv("USER_AGENT", "MarketIntelBot/1.0")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "market_ingest",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "apis_configured": {
            "crunchbase": bool(CRUNCHBASE_API_KEY),
            "linkedin": bool(LINKEDIN_API_KEY),
            "sec": bool(SEC_API_KEY),
            "news": bool(NEWS_API_KEY),
        },
    }


@app.post("/ingest/companies")
async def ingest_companies_data(
    companies: List[str], background_tasks: BackgroundTasks
):
    """Ingest company data from multiple sources"""
    try:
        job_id = f"ingest_companies_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        background_tasks.add_task(ingest_companies_task, job_id, companies)

        return {
            "job_id": job_id,
            "status": "started",
            "companies_count": len(companies),
            "estimated_duration": f"{len(companies) * 30}s",
        }

    except Exception as e:
        logger.error(f"Failed to start company ingestion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def ingest_companies_task(job_id: str, companies: List[str]):
    """Background task for company data ingestion"""
    try:
        logger.info(f"Starting company ingestion job: {job_id}")

        for company in companies:
            try:
                # Collect data from multiple sources
                company_data = await collect_company_data(company)

                # Normalize and enrich data
                normalized_data = normalize_company_data(company_data)

                # Store in database
                await store_company_data(normalized_data)

                # Cache for quick access
                cache_key = f"company:{company.lower()}"
                redis_client.setex(cache_key, 3600, json.dumps(normalized_data))

                await asyncio.sleep(REQUEST_DELAY)  # Rate limiting

            except Exception as e:
                logger.error(f"Failed to ingest data for {company}: {str(e)}")
                continue

        logger.info(f"Company ingestion completed: {job_id}")

    except Exception as e:
        logger.error(f"Company ingestion failed: {str(e)}")


async def collect_company_data(company_name: str) -> Dict[str, Any]:
    """Collect data for a company from multiple sources"""
    company_data = {
        "name": company_name,
        "collected_at": datetime.utcnow().isoformat(),
        "sources": [],
    }

    # Collect from Crunchbase
    if CRUNCHBASE_API_KEY:
        try:
            crunchbase_data = await fetch_crunchbase_data(company_name)
            if crunchbase_data:
                company_data["crunchbase"] = crunchbase_data
                company_data["sources"].append("crunchbase")
        except Exception as e:
            logger.warning(f"Crunchbase fetch failed for {company_name}: {e}")

    # Collect financial data
    try:
        financial_data = await fetch_financial_data(company_name)
        if financial_data:
            company_data["financial"] = financial_data
            company_data["sources"].append("financial")
    except Exception as e:
        logger.warning(f"Financial data fetch failed for {company_name}: {e}")

    # Collect news sentiment
    if NEWS_API_KEY:
        try:
            news_data = await fetch_news_data(company_name)
            if news_data:
                company_data["news"] = news_data
                company_data["sources"].append("news")
        except Exception as e:
            logger.warning(f"News fetch failed for {company_name}: {e}")

    return company_data


async def fetch_crunchbase_data(company_name: str) -> Optional[Dict[str, Any]]:
    """Fetch company data from Crunchbase API"""
    if not CRUNCHBASE_API_KEY:
        return None

    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.crunchbase.com/v3.1/organizations"
            params = {"name": company_name, "user_key": CRUNCHBASE_API_KEY}

            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    organizations = data.get("data", {}).get("items", [])

                    if organizations:
                        org = organizations[0]  # Take first match
                        return {
                            "id": org.get("identifier", {}).get("value"),
                            "name": org.get("properties", {}).get("name"),
                            "description": org.get("properties", {}).get(
                                "short_description"
                            ),
                            "founded_year": org.get("properties", {}).get(
                                "founded_year"
                            ),
                            "funding_stage": org.get("properties", {}).get(
                                "funding_stage"
                            ),
                            "total_funding": org.get("properties", {}).get(
                                "total_funding_usd"
                            ),
                            "employee_count": org.get("properties", {}).get(
                                "employee_count"
                            ),
                            "website": org.get("properties", {}).get("website"),
                            "linkedin": org.get("properties", {}).get(
                                "linkedin_identifier"
                            ),
                        }
    except Exception as e:
        logger.error(f"Crunchbase API error: {e}")

    return None


async def fetch_financial_data(company_name: str) -> Optional[Dict[str, Any]]:
    """Fetch basic financial data (mock implementation)"""
    # In a real implementation, this would integrate with financial APIs
    # For now, return mock data
    return {
        "revenue": 10000000,  # $10M
        "growth_rate": 0.25,  # 25%
        "profit_margin": 0.15,  # 15%
        "cash_flow": 2000000,  # $2M
        "valuation": 50000000,  # $50M
        "funding_rounds": 3,
    }


async def fetch_news_data(company_name: str) -> Optional[Dict[str, Any]]:
    """Fetch recent news about the company"""
    if not NEWS_API_KEY:
        return None

    try:
        async with aiohttp.ClientSession() as session:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": f'"{company_name}"',
                "apiKey": NEWS_API_KEY,
                "sortBy": "publishedAt",
                "language": "en",
                "pageSize": 10,
            }

            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    articles = data.get("articles", [])

                    # Calculate simple sentiment score
                    sentiment_scores = []
                    for article in articles:
                        # Simple sentiment calculation (in real implementation, use NLP)
                        title = article.get("title", "").lower()
                        if any(
                            word in title
                            for word in ["good", "great", "success", "growth"]
                        ):
                            sentiment_scores.append(0.7)
                        elif any(
                            word in title for word in ["bad", "fail", "loss", "decline"]
                        ):
                            sentiment_scores.append(0.3)
                        else:
                            sentiment_scores.append(0.5)

                    avg_sentiment = (
                        sum(sentiment_scores) / len(sentiment_scores)
                        if sentiment_scores
                        else 0.5
                    )

                    return {
                        "articles_count": len(articles),
                        "sentiment_score": avg_sentiment,
                        "latest_articles": [
                            {
                                "title": article.get("title"),
                                "description": article.get("description"),
                                "url": article.get("url"),
                                "published_at": article.get("publishedAt"),
                            }
                            for article in articles[:3]
                        ],
                    }
    except Exception as e:
        logger.error(f"News API error: {e}")

    return None


def normalize_company_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize and enrich collected company data"""
    normalized = {
        "name": raw_data.get("name"),
        "description": "",
        "tam": None,  # Total Addressable Market
        "growth_rate": None,
        "competitor_count": 0,
        "market_trends": [],
        "risk_factors": [],
        "source_data": raw_data,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    # Extract information from Crunchbase data
    crunchbase = raw_data.get("crunchbase", {})
    if crunchbase:
        normalized["description"] = crunchbase.get("description", "")
        normalized["funding_total"] = crunchbase.get("total_funding", 0)
        normalized["employee_count"] = crunchbase.get("employee_count", 0)

    # Extract information from financial data
    financial = raw_data.get("financial", {})
    if financial:
        normalized["growth_rate"] = financial.get("growth_rate")
        normalized["revenue"] = financial.get("revenue")
        normalized["valuation"] = financial.get("valuation")

    # Extract information from news sentiment
    news = raw_data.get("news", {})
    if news:
        sentiment = news.get("sentiment_score", 0.5)
        if sentiment < 0.4:
            normalized["risk_factors"].append("negative_news_sentiment")
        elif sentiment > 0.7:
            normalized["market_trends"].append("positive_market_sentiment")

    # Calculate TAM based on available data (mock calculation)
    revenue = normalized.get("revenue", 0)
    if revenue > 0:
        normalized["tam"] = revenue * 10  # Assume 10x revenue as TAM

    return normalized


async def store_company_data(company_data: Dict[str, Any]):
    """Store normalized company data in database"""
    try:
        # Store in MCP via API
        async with aiohttp.ClientSession() as session:
            url = "http://mcp-server:8003/api/companies"

            async with session.post(url, json=company_data) as response:
                if response.status == 200:
                    logger.info(f"Stored company data: {company_data['name']}")
                else:
                    logger.error(f"Failed to store company data: {response.status}")
    except Exception as e:
        logger.error(f"Database storage error: {e}")


@app.post("/ingest/market-trends")
async def ingest_market_trends(background_tasks: BackgroundTasks):
    """Ingest market trends and industry data"""
    try:
        job_id = f"ingest_trends_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        background_tasks.add_task(ingest_trends_task, job_id)

        return {"job_id": job_id, "status": "started", "estimated_duration": "300s"}

    except Exception as e:
        logger.error(f"Failed to start trends ingestion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def ingest_trends_task(job_id: str):
    """Background task for market trends ingestion"""
    try:
        logger.info(f"Starting market trends ingestion job: {job_id}")

        # List of industries to track
        industries = [
            "artificial intelligence",
            "fintech",
            "healthcare technology",
            "renewable energy",
            "e-commerce",
            "cybersecurity",
            "blockchain",
            "autonomous vehicles",
        ]

        for industry in industries:
            try:
                # Fetch trends data
                trends_data = await fetch_market_trends(industry)

                if trends_data:
                    # Store trends data
                    await store_trends_data(industry, trends_data)

                await asyncio.sleep(REQUEST_DELAY)

            except Exception as e:
                logger.error(f"Failed to ingest trends for {industry}: {str(e)}")
                continue

        logger.info(f"Market trends ingestion completed: {job_id}")

    except Exception as e:
        logger.error(f"Market trends ingestion failed: {str(e)}")


async def fetch_market_trends(industry: str) -> Optional[Dict[str, Any]]:
    """Fetch market trends for an industry"""
    # Mock implementation - in real world would integrate with Google Trends, industry reports, etc.
    return {
        "industry": industry,
        "growth_rate": 0.20,  # 20% annual growth
        "market_size": 10000000000,  # $10B
        "key_trends": ["AI integration", "Regulatory changes", "Technology disruption"],
        "growth_drivers": [
            "Digital transformation",
            "Consumer demand",
            "Investment funding",
        ],
        "barriers": [
            "Regulatory complexity",
            "Talent shortage",
            "High capital requirements",
        ],
        "competitive_intensity": "high",  # high/medium/low
        "collected_at": datetime.utcnow().isoformat(),
    }


async def store_trends_data(industry: str, trends_data: Dict[str, Any]):
    """Store market trends data"""
    try:
        async with aiohttp.ClientSession() as session:
            url = "http://mcp-server:8003/api/market-trends"

            async with session.post(url, json=trends_data) as response:
                if response.status == 200:
                    logger.info(f"Stored trends data for: {industry}")
                else:
                    logger.error(f"Failed to store trends data: {response.status}")
    except Exception as e:
        logger.error(f"Trends storage error: {e}")


@app.get("/api/companies/{company_name}")
async def get_company_data(company_name: str):
    """Get cached company data"""
    try:
        cache_key = f"company:{company_name.lower()}"
        cached_data = redis_client.get(cache_key)

        if cached_data:
            return json.loads(cached_data)

        # Fetch from database if not in cache
        async with aiohttp.ClientSession() as session:
            url = f"http://mcp-server:8003/api/companies/{company_name}"

            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    # Cache the result
                    redis_client.setex(cache_key, 3600, json.dumps(data))
                    return data
                else:
                    raise HTTPException(status_code=404, detail="Company not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get company data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch company data")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8040, reload=True, log_level="info")
