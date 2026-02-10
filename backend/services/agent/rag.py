# services/agent/rag.py
import httpx
import psycopg2
from config import (
    INGEST_SERVICE_URL,
    TOP_K_INTERVIEW,
    SCORE_THRESHOLD_INTERVIEW,
    TOP_K_GENERAL,
    SCORE_THRESHOLD_GENERAL,
    DATABASE_URL,
    logger
)


async def search_documents(query: str, is_interview: bool = False) -> list[dict]:
    """Search local documents via ingest service"""
    try:
        top_k = TOP_K_INTERVIEW if is_interview else TOP_K_GENERAL
        score_threshold = SCORE_THRESHOLD_INTERVIEW if is_interview else SCORE_THRESHOLD_GENERAL

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{INGEST_SERVICE_URL}/search",
                json={
                    "query": query,
                    "top_k": top_k,
                    "score_threshold": score_threshold,
                },
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        logger.error(f"Document search error: {e}")
    return []


async def search_documents_direct_db(query: str, is_interview: bool = False) -> list[dict]:
    """Search documents directly in database"""
    try:
        # Connect to database
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        # Search for documents containing Gordon Food Service
        search_query = """
            SELECT id, filename, content, metadata, created_at
            FROM documents 
            WHERE content ILIKE %s
            ORDER BY created_at DESC
            LIMIT 5
        """

        search_pattern = f"%{query}%"
        cur.execute(search_query, (search_pattern,))
        results = cur.fetchall()

        search_results = []
        for row in results:
            content = row[2] if row[2] else ""
            truncated_content = content[:1000] + "..." if len(content) > 1000 else content

            search_results.append({
                "document_id": str(row[0]),
                "filename": row[1] if row[1] else "Unknown",
                "text": truncated_content,
                "similarity": 0.8,
                "metadata": row[3] if row[3] else {}
            })

        cur.close()
        conn.close()

        logger.info(f"Direct DB search found {len(search_results)} results for query: {query}")
        return search_results

    except Exception as e:
        logger.error(f"Direct DB search error: {e}")
        return []