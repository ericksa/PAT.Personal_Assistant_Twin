#!/usr/bin/env python3
"""
APAT - Automation Prompt & Analytics Toolkit
Orchestrator + LLM-prompt library + analytics engine
"""

import asyncio
import os
import logging
from typing import Dict, Any, List
from datetime import datetime
import yaml
import json
from pathlib import Path

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
    title="APAT Service",
    description="Automation Prompt & Analytics Toolkit",
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
INGEST_SERVICE_URL = os.getenv("INGEST_SERVICE_URL", "http://ingest-service:8000")
MCP_SERVICE_URL = os.getenv("MCP_SERVICE_URL", "http://mcp-server:8003")

# Template paths
TEMPLATES_PATH = Path("/app/templates")
OUTPUT_PATH = Path("/app/output")
LOG_PATH = Path("/app/logs")

# Ensure directories exist
TEMPLATES_PATH.mkdir(parents=True, exist_ok=True)
OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
LOG_PATH.mkdir(parents=True, exist_ok=True)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "apat",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }


@app.post("/jobs/generate")
async def generate_document(request: Dict[str, Any], background_tasks: BackgroundTasks):
    """Generate business plan, SOW, or other documents"""
    try:
        document_type = request.get("type")
        data = request.get("data", {})
        template_name = request.get("template")

        if not document_type or not template_name:
            raise HTTPException(status_code=400, detail="Missing required fields")

        job_id = f"{document_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        background_tasks.add_task(
            generate_document_task, job_id, document_type, template_name, data
        )

        return {
            "job_id": job_id,
            "status": "queued",
            "document_type": document_type,
            "template": template_name,
        }

    except Exception as e:
        logger.error(f"Failed to queue document generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def generate_document_task(
    job_id: str, document_type: str, template_name: str, data: Dict[str, Any]
):
    """Background task for document generation"""
    try:
        logger.info(f"Starting document generation job: {job_id}")

        # Load template
        template_path = TEMPLATES_PATH / f"{template_name}.yml"
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_name}")

        with open(template_path, "r") as f:
            template_config = yaml.safe_load(f)

        # Render template with data
        rendered_content = await render_template(template_config, data)

        # Generate document sections based on type
        if document_type == "business_plan":
            sections = await generate_business_plan_sections(rendered_content, data)
        elif document_type == "sow":
            sections = await generate_sow_sections(rendered_content, data)
        elif document_type == "rfp":
            sections = await generate_rfp_sections(rendered_content, data)
        else:
            sections = await generate_generic_sections(rendered_content, data)

        # Calculate RAG for each section
        rag_scores = calculate_section_rag(sections)

        # Store in MCP
        await store_document_in_mcp(job_id, sections, rag_scores)

        logger.info(f"Document generation completed: {job_id}")

    except Exception as e:
        logger.error(f"Document generation failed for job {job_id}: {str(e)}")
        # Update job status to failed


async def render_template(template_config: Dict[str, Any], data: Dict[str, Any]) -> str:
    """Render template with data using Jinja2"""
    try:
        from jinja2 import Template

        template = Template(template_config.get("prompt", ""))
        return template.render(**data)

    except Exception as e:
        logger.error(f"Template rendering failed: {str(e)}")
        raise


async def generate_business_plan_sections(
    rendered_content: str, data: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Generate business plan sections"""
    sections = []

    # Executive Summary
    sections.append(
        {
            "name": "executive_summary",
            "content": await generate_executive_summary(data),
            "rag_status": "GREEN",  # Will be recalculated
        }
    )

    # Market Analysis
    sections.append(
        {
            "name": "market_analysis",
            "content": await generate_market_analysis(data),
            "rag_status": "AMBER",
        }
    )

    # Competitive Landscape
    sections.append(
        {
            "name": "competitive_landscape",
            "content": await generate_competitive_landscape(data),
            "rag_status": "GREEN",
        }
    )

    # Financial Projections
    sections.append(
        {
            "name": "financial_projections",
            "content": await generate_financial_projections(data),
            "rag_status": "RED",
        }
    )

    return sections


async def generate_sow_sections(
    rendered_content: str, data: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Generate Statement of Work sections"""
    sections = []

    # Project Overview
    sections.append(
        {
            "name": "project_overview",
            "content": await generate_project_overview(data),
            "rag_status": "GREEN",
        }
    )

    # Scope of Work
    sections.append(
        {
            "name": "scope_of_work",
            "content": await generate_scope_of_work(data),
            "rag_status": "AMBER",
        }
    )

    # Timeline and Deliverables
    sections.append(
        {
            "name": "timeline_deliverables",
            "content": await generate_timeline_deliverables(data),
            "rag_status": "GREEN",
        }
    )

    # Risk and Mitigation
    sections.append(
        {
            "name": "risk_mitigation",
            "content": await generate_risk_mitigation(data),
            "rag_status": "RED",
        }
    )

    return sections


async def generate_rfp_sections(
    rendered_content: str, data: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Generate RFP sections"""
    sections = []

    # RFP Overview
    sections.append(
        {
            "name": "rfp_overview",
            "content": await generate_rfp_overview(data),
            "rag_status": "GREEN",
        }
    )

    # Requirements
    sections.append(
        {
            "name": "requirements",
            "content": await generate_requirements(data),
            "rag_status": "AMBER",
        }
    )

    # Evaluation Criteria
    sections.append(
        {
            "name": "evaluation_criteria",
            "content": await generate_evaluation_criteria(data),
            "rag_status": "GREEN",
        }
    )

    return sections


async def generate_generic_sections(
    rendered_content: str, data: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Generate generic document sections"""
    return [{"name": "content", "content": rendered_content, "rag_status": "AMBER"}]


async def generate_executive_summary(data: Dict[str, Any]) -> str:
    """Generate executive summary section"""
    # Implementation for LLM generation
    template = """
    # Executive Summary
    
    ## Market Opportunity
    Based on our analysis, we have identified {num_green} high-priority opportunities 
    with GREEN RAG status, representing a total addressable market of ${tam:.1f} billion.
    
    ## Key Findings
    {key_findings}
    
    ## Strategic Recommendations
    {recommendations}
    """

    # This would integrate with LLM service
    return template.format(
        num_green=data.get("num_green_opportunities", 0),
        tam=data.get("total_addressable_market", 0),
        key_findings="• High growth potential in emerging markets\n• Strong competitive positioning",
        recommendations="• Focus on top 3 GREEN opportunities\n• Develop risk mitigation strategies",
    )


async def generate_market_analysis(data: Dict[str, Any]) -> str:
    """Generate market analysis section"""
    # Implementation for market analysis
    return """
    # Market Analysis
    
    ## Market Size and Growth
    The target market shows strong fundamentals with growth rates of {growth}% annually.
    
    ## Competitive Landscape
    Analysis of {competitor_count} competitors reveals market positioning opportunities.
    
    ## Market Trends
    Key trends affecting the market include regulatory changes, technological advancement, and consumer behavior shifts.
    """.format(
        growth=data.get("market_growth_rate", 0),
        competitor_count=data.get("competitor_count", 0),
    )


async def generate_competitive_landscape(data: Dict[str, Any]) -> str:
    """Generate competitive landscape section"""
    return """
    # Competitive Landscape
    
    ## Direct Competitors
    {competitors}
    
    ## Competitive Advantages
    {advantages}
    
    ## Market Positioning
    {positioning}
    """.format(
        competitors="• Competitor A - Market leader\n• Competitor B - Niche player",
        advantages="• Superior technology\n• Established relationships",
        positioning="We are positioned as a premium solution provider with focus on enterprise clients.",
    )


async def generate_financial_projections(data: Dict[str, Any]) -> str:
    """Generate financial projections section"""
    return """
    # Financial Projections
    
    ## Revenue Projections
    Year 1: ${revenue_y1:.2f}M
    Year 2: ${revenue_y2:.2f}M
    Year 3: ${revenue_y3:.2f}M
    
    ## Cost Structure
    • Personnel costs: 60%\n• Technology costs: 25%\n• Marketing costs: 15%
    
    ## Profitability Analysis
    Break-even expected in month {breakeven} with projected gross margin of {margin:.1f}%.
    """.format(
        revenue_y1=data.get("revenue_y1", 0),
        revenue_y2=data.get("revenue_y2", 0),
        revenue_y3=data.get("revenue_y3", 0),
        breakeven=data.get("breakeven_month", 12),
        margin=data.get("gross_margin", 40),
    )


async def generate_project_overview(data: Dict[str, Any]) -> str:
    """Generate project overview section"""
    return """
    # Project Overview
    
    ## Project Objectives
    {objectives}
    
    ## Success Criteria
    {success_criteria}
    
    ## Key Stakeholders
    {stakeholders}
    """.format(
        objectives=data.get(
            "project_objectives", "Deliver enterprise software solution"
        ),
        success_criteria=data.get(
            "success_criteria", "On-time delivery, budget adherence, quality standards"
        ),
        stakeholders=data.get(
            "key_stakeholders", "Project sponsors, development team, end users"
        ),
    )


async def generate_scope_of_work(data: Dict[str, Any]) -> str:
    """Generate scope of work section"""
    return """
    # Scope of Work
    
    ## In-Scope Items
    {in_scope}
    
    ## Out-of-Scope Items
    {out_of_scope}
    
    ## Assumptions
    {assumptions}
    """.format(
        in_scope=data.get(
            "in_scope_items", "• Core development\n• Testing\n• Deployment"
        ),
        out_of_scope=data.get(
            "out_of_scope_items", "• Training programs\n• Hardware procurement"
        ),
        assumptions=data.get(
            "assumptions", "• Access to existing systems\n• Timely stakeholder feedback"
        ),
    )


async def generate_timeline_deliverables(data: Dict[str, Any]) -> str:
    """Generate timeline and deliverables section"""
    return """
    # Timeline and Deliverables
    
    ## Project Timeline
    • Phase 1: Discovery (Weeks 1-2)\n• Phase 2: Design (Weeks 3-4)\n• Phase 3: Development (Weeks 5-8)\n• Phase 4: Testing (Weeks 9-10)\n• Phase 5: Deployment (Weeks 11-12)
    
    ## Key Deliverables
    {deliverables}
    
    ## Milestones
    {milestones}
    """.format(
        deliverables=data.get(
            "key_deliverables",
            "• Technical specifications\n• Working software\n• Documentation",
        ),
        milestones=data.get(
            "project_milestones",
            "• Design approval\n• Development milestone\n• Go-live",
        ),
    )


async def generate_risk_mitigation(data: Dict[str, Any]) -> str:
    """Generate risk and mitigation section"""
    return """
    # Risk and Mitigation
    
    ## Identified Risks
    • Technical complexity\n• Resource availability\n• Timeline constraints
    
    ## Mitigation Strategies
    {mitigation_strategies}
    
    ## Contingency Plans
    {contingency_plans}
    """.format(
        mitigation_strategies=data.get(
            "mitigation_strategies",
            "• Regular code reviews\n• Resource planning\n• Buffer time in schedule",
        ),
        contingency_plans=data.get(
            "contingency_plans",
            "• Alternative resource pool\n• Scope adjustment procedures",
        ),
    )


async def generate_rfp_overview(data: Dict[str, Any]) -> str:
    """Generate RFP overview section"""
    return """
    # RFP Overview
    
    ## Purpose
    {purpose}
    
    ## Background
    {background}
    
    ## Project Scope
    {project_scope}
    """.format(
        purpose=data.get(
            "rfp_purpose",
            "Seek qualified vendor to provide enterprise software solution",
        ),
        background=data.get(
            "project_background", "Company seeking to modernize legacy systems"
        ),
        project_scope=data.get("rfp_scope", "Full-stack development and deployment"),
    )


async def generate_requirements(data: Dict[str, Any]) -> str:
    """Generate requirements section"""
    return """
    # Requirements
    
    ## Functional Requirements
    {functional_requirements}
    
    ## Technical Requirements
    {technical_requirements}
    
    ## Performance Requirements
    {performance_requirements}
    """.format(
        functional_requirements=data.get(
            "functional_requirements",
            "• User authentication\n• Data processing\n• Reporting",
        ),
        technical_requirements=data.get(
            "technical_requirements",
            "• REST APIs\n• Database integration\n• Security protocols",
        ),
        performance_requirements=data.get(
            "performance_requirements", "• 99.9% uptime\n• Sub-second response times"
        ),
    )


async def generate_evaluation_criteria(data: Dict[str, Any]) -> str:
    """Generate evaluation criteria section"""
    return """
    # Evaluation Criteria
    
    ## Technical Capabilities
    • Architecture and design approach\n• Technology stack alignment\n• Security and compliance
    
    ## Experience and Expertise
    {experience_factors}
    
    ## Commercial Considerations
    {commercial_factors}
    """.format(
        experience_factors=data.get(
            "experience_factors",
            "• Relevant industry experience\n• Team qualifications\n• Past project success",
        ),
        commercial_factors=data.get(
            "commercial_factors",
            "• Cost competitiveness\n• Payment terms\n• Risk allocation",
        ),
    )


def calculate_section_rag(sections: List[Dict[str, Any]]) -> Dict[str, str]:
    """Calculate RAG status for each section"""
    rag_scores = {}

    for section in sections:
        content = section.get("content", "")

        # Simple rule-based RAG calculation
        if "RED" in content.upper() or "risk" in content.lower():
            rag_status = "RED"
        elif "AMBER" in content.upper() or "concern" in content.lower():
            rag_status = "AMBER"
        else:
            rag_status = "GREEN"

        rag_scores[section["name"]] = rag_status
        section["rag_status"] = rag_status

    return rag_scores


async def store_document_in_mcp(
    job_id: str, sections: List[Dict[str, Any]], rag_scores: Dict[str, str]
):
    """Store generated document in MCP"""
    try:
        # Prepare document data
        document_data = {
            "job_id": job_id,
            "sections": sections,
            "rag_scores": rag_scores,
            "created_at": datetime.utcnow().isoformat(),
            "status": "completed",
        }

        # Store in MCP via API call
        # This would make an HTTP request to MCP service

        logger.info(f"Document stored in MCP: {job_id}")

    except Exception as e:
        logger.error(f"Failed to store document in MCP: {str(e)}")
        raise


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8010, reload=True, log_level="info")
