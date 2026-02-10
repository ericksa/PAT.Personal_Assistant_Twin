# services/agent/test_rag.py
import os
import sys
import asyncio

# Add current dir to path
sys.path.insert(0, os.path.dirname(__file__))

# Import modules (now with absolute imports)
from rag import search_documents
from config import logger

async def test():
    logger.info("🔍 Testing RAG with: 'tell me your expereince with gordon food service'")
    try:
        results = await search_documents("tell me your expereince with gordon food service", is_interview=True)
        if results:
            logger.info(f"✅ Found {len(results)} results!")
            for i, r in enumerate(results):
                logger.info(f"Result {i+1}: {r.get('text', 'no text')[:150]}...")
        else:
            logger.warning("⚠️ No results found — is ingest-service running?")
    except Exception as e:
        logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())