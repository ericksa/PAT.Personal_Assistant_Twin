#!/usr/bin/env python3
"""
Ingest Apple Notes into PAT Ingest Service
"""

import subprocess
import requests
import json
import logging
import os
import re
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ingest-apple-notes")

INGEST_URL = os.getenv("INGEST_URL", "http://localhost:8001/upload")


def clean_html(raw_html: str) -> str:
    """Basic HTML cleanup for Apple Notes body"""
    clean_text = re.sub("<[^<]+?>", "\n", raw_html)
    # Remove multiple newlines
    clean_text = re.sub("\n+", "\n", clean_text).strip()
    return clean_text


def run_applescript(script: str):
    """Execute AppleScript and return result"""
    try:
        result = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            logger.error(f"AppleScript error: {result.stderr}")
            return None
    except Exception as e:
        logger.error(f"Failed to run AppleScript: {e}")
        return None


def get_all_notes() -> List[Dict]:
    """Get all notes from Apple Notes using AppleScript"""
    logger.info("Retrieving Apple Notes...")

    # Get IDs and Names
    ids_raw = run_applescript('tell application "Notes" to get id of every note')
    names_raw = run_applescript('tell application "Notes" to get name of every note')

    if not ids_raw or not names_raw:
        return []

    ids = [i.strip() for i in ids_raw.split(",")]
    names = [n.strip() for n in names_raw.split(",")]

    notes = []
    # Limit to first 50 to avoid timing out or overloading for the initial run
    limit = 50
    for i in range(min(len(ids), limit)):
        note_id = ids[i]
        note_name = names[i]

        logger.info(f"Fetching content for: {note_name}")
        body_raw = run_applescript(
            f'tell application "Notes" to get body of note id "{note_id}"'
        )

        if body_raw:
            notes.append(
                {"id": note_id, "name": note_name, "content": clean_html(body_raw)}
            )

    return notes


def ingest_note(note: Dict):
    """Upload a single note to PAT Ingest Service"""
    try:
        filename = f"AppleNote_{note['name'].replace('/', '_')}.txt"

        # New parameters for v2
        data = {"domain": "personal", "category": "apple_notes"}

        files = {"file": (filename, note["content"], "text/plain")}

        response = requests.post(INGEST_URL, data=data, files=files)

        if response.status_code == 200:
            logger.info(f"✅ Successfully ingested: {note['name']}")
        else:
            logger.error(f"❌ Failed to ingest {note['name']}: {response.text}")

    except Exception as e:
        logger.error(f"Error ingesting note {note['name']}: {e}")


def main():
    notes = get_all_notes()
    logger.info(f"Found {len(notes)} notes to ingest.")

    for note in notes:
        ingest_note(note)

    logger.info("Ingestion complete.")


if __name__ == "__main__":
    main()
