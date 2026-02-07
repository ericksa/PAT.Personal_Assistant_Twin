# services/brain_service/main.py
import os
import uuid
import json
import psycopg2
from fastapi.openapi.utils import get_openapi
from psycopg2.extras import Json
import ollama
import asyncio
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import httpx


app = FastAPI()

# Database configuration matching your setup

DB_CONFIG = os.getenv("DATABASE_URL", "postgresql://llm:llm@postgres:5432/llm")
openapi_schema = get_openapi(
    title="Tool Proxy API",
    version="1.0.0",
    description="Proxy for agent-service tools",
    routes=app.routes,
)


class AudioInput(BaseModel):
    text: str


class ConnectionManager:
    def __init__(self):

        self.active_connections = []

    async def broadcast(self, message):
        # Placeholder for WebSocket broadcasting
        print(f"Broadcasting: {message}")


manager = ConnectionManager()


class ResumeContext:
    def __init__(self):
        pass

    def get_connection(self):
        """Establish database connection"""
        return psycopg2.connect(DB_CONFIG)

    def query_pgvector(self, question: str, limit: int = 3) -> str:
        """Query pgvector database for relevant context"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()

            # Keyword-based search (enhance with actual embeddings if needed)
            query = """
            SELECT content, metadata 
            FROM documents 
            WHERE content ILIKE %s OR metadata::text ILIKE %s
            ORDER BY created_at DESC 
            LIMIT %s
            """

            search_term = f"%{question}%"
            cur.execute(query, (search_term, search_term, limit))
            results = cur.fetchall()

            context_parts = []
            for content, metadata in results:
                context_parts.append(content)

            return "\n".join(context_parts) if context_parts else "No relevant context found"

        except Exception as e:
            print(f"Database query error: {e}")
            return "Error retrieving context"
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()


resume_context = ResumeContext()


@app.get("/")
def read_root():
    return {"message": "Brain service is running"}


@app.post("/api/process_audio")
async def process_audio(input_data: AudioInput, background_tasks: BackgroundTasks):
    """Process audio transcription with RAG enhancement"""
    print(f"Processing: {input_data.text}")

    # Retrieve relevant context from pgvector
    context = resume_context.query_pgvector(input_data.text)

    # Enhanced prompt with context
    prompt = f"""
    You are a senior software engineer in a technical interview.
    Question: {input_data.text}

    Relevant experience from resume: {context}

    Provide a concise, professional response that:
    1. Directly addresses the question
    2. Highlights relevant experience
    3. Includes specific technical details
    4. Shows enthusiasm for problem-solving

    Keep responses under 150 words.
    """

    try:
        response = ollama.generate(
            model="deepseek-coder:6.7b",
            prompt=prompt,
            options={"temperature": 0.3}
        )

        result = {
            "question": input_data.text,
            "answer": response['response'],
            "timestamp": asyncio.get_event_loop().time()
        }

        # Broadcast via WebSocket
        background_tasks.add_task(manager.broadcast, result)

        return {"status": "processed", "response": result}

    except Exception as e:
        error_msg = f"Error generating response: {str(e)}"
        print(error_msg)
        return {"status": "error", "message": error_msg}


# Sample data loading script (run once to populate your database)
def load_resume_data():
    """Load resume sections into your existing documents table"""
    resume_sections = [
        {
            "filename": "technical_skills.txt",
            "content": "Technology Used: SharePoint, SharePoint Designer, Microsoft Office 365, VMware, GoToAssist, IIS, Windows Server 2016, PowerShell, Kickstart, Windows 2007 & 10, Unix, Linux, Mac OS X, iOS, Android, LAN, WAN, SAN, TCP/IP, HTTP, Wireless, AnyConnect VPN, Switches, Active Directory Domain Controllers, Group Policy Objects, Printers, Projectors. Demonstrated strengths in rapidly diagnosing, troubleshooting and resolving client issues.",
            "metadata": {"category": "technical_skills", "source": "resume"}
        },
        {
            "filename": "cloud_infrastructure.txt",
            "content": "Cloud Infrastructure: AWS EC2 S3 Lambda Redshift EKS GovCloud, Docker, VMware ESXi, Kubernetes. DevSecOps: Jenkins, GitLab CI/CD, Maven, Gradle, SonarQube, Fortify, Splunk, Jira, Git. Security Compliance: RMF, NIST 800-171/53, DISA STIGs, HIPAA, IAM, CNSS 4011-4016 Information Assurance.",
            "metadata": {"category": "cloud_infrastructure", "source": "resume"}
        },
        {
            "filename": "development_experience.txt",
            "content": "Frameworks & Libraries: Spring Boot (REST, MVC), Hibernate, Camel, JMS. Web Development: React, HTML, CSS, JSP, Servlets, Thymeleaf. APIs & Web Services: RESTful services, SOAP services. Database Management: Oracle SQL, PL/SQL, PostgreSQL, MySQL; proficient in writing complex queries and stored procedures.",
            "metadata": {"category": "development", "source": "resume"}
        }
    ]

    conn = psycopg2.connect(DB_CONFIG)
    cur = conn.cursor()

    for section in resume_sections:
        doc_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO documents (id, filename, content, metadata) 
            VALUES (%s, %s, %s, %s)
        """, (doc_id, section["filename"], section["content"], json.dumps(section["metadata"])))

    conn.commit()
    cur.close()
    conn.close()
    print("Resume data loaded successfully")


if __name__ == "__main__":

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)