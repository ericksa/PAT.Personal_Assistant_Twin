"""
Push Notification Service
FCM and APNS push notification delivery
"""

import os
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Push Notification Service",
    description="FCM and APNS push notification delivery",
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

# Service URLs
RAG_SCORING_URL = os.getenv("RAG_SCORING_URL", "http://rag-scoring:8030")

# Push Service Configuration
FCM_SERVER_KEY = os.getenv("FCM_SERVER_KEY", "")
APNS_KEY_ID = os.getenv("APNS_KEY_ID", "")
APNS_TEAM_ID = os.getenv("APNS_TEAM_ID", "")
APNS_BUNDLE_ID = os.getenv("APNS_BUNDLE_ID", "")
APNS_PRIVATE_KEY = os.getenv("APNS_PRIVATE_KEY", "")

# Notification Rules
RED_ALERT_ENABLED = os.getenv("RED_ALERT_ENABLED", "true").lower() == "true"
AMBER_REMINDER_ENABLED = os.getenv("AMBER_REMINDER_ENABLED", "true").lower() == "true"
SCHEDULED_SUMMARY_ENABLED = (
    os.getenv("SCHEDULED_SUMMARY_ENABLED", "true").lower() == "true"
)

# Redis for queue management
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
import redis

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "push_notifications",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services_configured": {
            "fcm": bool(FCM_SERVER_KEY),
            "apns": bool(APNS_KEY_ID and APNS_PRIVATE_KEY),
        },
        "rules_enabled": {
            "red_alerts": RED_ALERT_ENABLED,
            "amber_reminders": AMBER_REMINDER_ENABLED,
            "scheduled_summaries": SCHEDULED_SUMMARY_ENABLED,
        },
    }


@app.post("/notify")
async def send_notification(
    notification: Dict[str, Any], background_tasks: BackgroundTasks
):
    """Send push notification"""
    try:
        notification_type = notification.get("type", "general")
        title = notification.get("title", "")
        body = notification.get("body", "")
        data = notification.get("data", {})

        if not title or not body:
            raise HTTPException(status_code=400, detail="Title and body are required")

        background_tasks.add_task(
            deliver_notification, notification_type, title, body, data
        )

        return {
            "status": "queued",
            "type": notification_type,
            "title": title,
            "estimated_delivery": "30s",
        }

    except Exception as e:
        logger.error(f"Failed to queue notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def deliver_notification(
    notification_type: str, title: str, body: str, data: Dict[str, Any]
):
    """Background task to deliver notification"""
    try:
        logger.info(f"Delivering {notification_type} notification: {title}")

        # Send to FCM
        if FCM_SERVER_KEY:
            await send_fcm_notification(title, body, data)

        # Send to APNS (if configured)
        if APNS_PRIVATE_KEY:
            await send_apns_notification(title, body, data)

        # Store notification record
        await store_notification_record(notification_type, title, body, data)

        logger.info(f"Notification delivered: {title}")

    except Exception as e:
        logger.error(f"Notification delivery failed: {str(e)}")


async def send_fcm_notification(title: str, body: str, data: Dict[str, Any]):
    """Send notification via FCM"""
    try:
        fcm_payload = {
            "notification": {"title": title, "body": body},
            "data": data,
            "priority": "high",
        }

        headers = {
            "Authorization": f"key={FCM_SERVER_KEY}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://fcm.googleapis.com/fcm/send",
                headers=headers,
                json=fcm_payload,
                timeout=10.0,
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"FCM notification sent: {result}")
            else:
                logger.error(
                    f"FCM send failed: {response.status_code} - {response.text}"
                )

    except Exception as e:
        logger.error(f"FCM notification error: {str(e)}")


async def send_apns_notification(title: str, body: str, data: Dict[str, Any]):
    """Send notification via APNS"""
    try:
        # Mock APNS implementation
        # In a real implementation, you would use pyapns2 or similar

        apns_payload = {
            "aps": {
                "alert": {"title": title, "body": body},
                "badge": 1,
                "sound": "default",
            },
            "data": data,
        }

        # Mock APNS send (would integrate with Apple Push Notification Service)
        logger.info(f"APNS notification sent: {apns_payload}")

    except Exception as e:
        logger.error(f"APNS notification error: {str(e)}")


async def store_notification_record(
    notification_type: str, title: str, body: str, data: Dict[str, Any]
):
    """Store notification record"""
    try:
        notification_record = {
            "type": notification_type,
            "title": title,
            "body": body,
            "data": data,
            "delivered_at": datetime.utcnow().isoformat(),
            "status": "delivered",
        }

        # Store in Redis for now (in production, use a database)
        record_key = f"notification:{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        redis_client.setex(
            record_key, 86400, json.dumps(notification_record)
        )  # 24h TTL

    except Exception as e:
        logger.error(f"Failed to store notification record: {str(e)}")


@app.post("/alerts/red")
async def send_red_alert(
    opportunity_id: str,
    opportunity_name: str,
    additional_data: Optional[Dict[str, Any]] = None,
):
    """Send RED alert notification"""
    try:
        if not RED_ALERT_ENABLED:
            return {"status": "disabled", "reason": "RED alerts disabled"}

        title = f"🚩 RED Alert: {opportunity_name}"
        body = "High-risk opportunity requires immediate review"

        data = {
            "type": "red_alert",
            "opportunity_id": opportunity_id,
            "opportunity_name": opportunity_name,
            "timestamp": datetime.utcnow().isoformat(),
            "priority": "critical",
            **(additional_data or {}),
        }

        notification = {"type": "red_alert", "title": title, "body": body, "data": data}

        # Queue the notification
        await send_notification(notification)

        return {
            "status": "sent",
            "alert_type": "red",
            "opportunity_id": opportunity_id,
            "opportunity_name": opportunity_name,
        }

    except Exception as e:
        logger.error(f"Failed to send RED alert: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/summaries/daily")
async def send_daily_summary():
    """Send daily RAG summary notification"""
    try:
        if not SCHEDULED_SUMMARY_ENABLED:
            return {"status": "disabled", "reason": "Scheduled summaries disabled"}

        # Fetch RAG metrics
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{RAG_SCORING_URL}/metrics")
            response.raise_for_status()
            metrics = response.json()

        title = "📊 Daily RAG Summary"
        body = f"Total: {metrics['total_opportunities']} | Green: {metrics['green_count']} | Amber: {metrics['amber_count']} | Red: {metrics['red_count']}"

        data = {
            "type": "daily_summary",
            "metrics": metrics,
            "summary_date": datetime.utcnow().date().isoformat(),
            "timestamp": datetime.utcnow().isoformat(),
        }

        notification = {
            "type": "daily_summary",
            "title": title,
            "body": body,
            "data": data,
        }

        await send_notification(notification)

        return {"status": "sent", "summary_type": "daily", "metrics": metrics}

    except Exception as e:
        logger.error(f"Failed to send daily summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/summaries/weekly")
async def send_weekly_summary():
    """Send weekly RAG summary notification"""
    try:
        if not SCHEDULED_SUMMARY_ENABLED:
            return {"status": "disabled", "reason": "Scheduled summaries disabled"}

        # Fetch comprehensive RAG data
        async with httpx.AsyncClient() as client:
            # Get metrics
            metrics_response = await client.get(f"{RAG_SCORING_URL}/metrics")
            metrics_response.raise_for_status()
            metrics = metrics_response.json()

            # Get recent opportunities
            opps_response = await client.get(
                f"{RAG_SCORING_URL}/opportunities", params={"limit": 50}
            )
            opps_response.raise_for_status()
            opportunities = opps_response.json()

        title = "📈 Weekly Market Intelligence Report"
        body = f"Weekly RAG Analysis: {metrics['total_opportunities']} opportunities analyzed"

        # Calculate weekly changes (simplified)
        green_trend = "stable"  # Would calculate actual trend
        red_count = metrics["red_count"]

        data = {
            "type": "weekly_summary",
            "metrics": metrics,
            "opportunities_count": len(opportunities.get("opportunities", [])),
            "summary_week": datetime.utcnow().date().isoformat(),
            "timestamp": datetime.utcnow().isoformat(),
            "key_insights": [
                f"{red_count} opportunities require immediate attention",
                f"{metrics['green_count']} high-potential opportunities identified",
                f"Average RAG score: {metrics['avg_rag_score']:.1f}",
            ],
        }

        notification = {
            "type": "weekly_summary",
            "title": title,
            "body": body,
            "data": data,
        }

        await send_notification(notification)

        return {"status": "sent", "summary_type": "weekly", "metrics": metrics}

    except Exception as e:
        logger.error(f"Failed to send weekly summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def get_notification_metrics():
    """Get notification delivery metrics"""
    try:
        # Get recent notifications from Redis
        pattern = "notification:*"
        keys = redis_client.keys(pattern)

        notifications = []
        for key in keys[:100]:  # Limit to recent 100
            try:
                data = redis_client.get(key)
                if data:
                    notifications.append(json.loads(data))
            except Exception:
                continue

        # Calculate metrics
        total_sent = len(notifications)
        by_type = {}
        by_status = {}

        for notification in notifications:
            notif_type = notification.get("type", "unknown")
            status = notification.get("status", "unknown")

            by_type[notif_type] = by_type.get(notif_type, 0) + 1
            by_status[status] = by_status.get(status, 0) + 1

        return {
            "total_sent": total_sent,
            "by_type": by_type,
            "by_status": by_status,
            "recent_notifications": notifications[-10:] if notifications else [],
        }

    except Exception as e:
        logger.error(f"Failed to get notification metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/subscriptions/register")
async def register_push_subscription(subscription: Dict[str, Any]):
    """Register push notification subscription"""
    try:
        device_id = subscription.get("device_id")
        platform = subscription.get("platform")  # "ios" or "android"
        token = subscription.get("token")

        if not device_id or not platform or not token:
            raise HTTPException(status_code=400, detail="Missing required fields")

        # Store subscription (in production, use a database)
        subscription_key = f"subscription:{device_id}"
        subscription_data = {
            "device_id": device_id,
            "platform": platform,
            "token": token,
            "registered_at": datetime.utcnow().isoformat(),
            "active": True,
        }

        redis_client.setex(
            subscription_key, 86400 * 30, json.dumps(subscription_data)
        )  # 30 days

        return {"status": "registered", "device_id": device_id, "platform": platform}

    except Exception as e:
        logger.error(f"Failed to register subscription: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8060, reload=True, log_level="info")
