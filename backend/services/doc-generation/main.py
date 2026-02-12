"""
Document Generation Service
Business plan, SOW, and RFP document generation
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
    title="Document Generation Service",
    description="Business plan, SOW, and RFP document generation",
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
APAT_SERVICE_URL = os.getenv("APAT_SERVICE_URL", "http://apat-service:8010")
MCP_SERVICE_URL = os.getenv("MCP_SERVICE_URL", "http://mcp-server:8003")

# PDF Generation
PDF_ENGINE = os.getenv("PDF_ENGINE", "weasyprint")
TEMPLATES_PATH = os.getenv("TEMPLATES_PATH", "/app/templates")
OUTPUT_PATH = os.getenv("OUTPUT_PATH", "/app/output")

# Document Types
SUPPORTED_TYPES = os.getenv("SUPPORTED_TYPES", "business_plan,sow,rfp,proposal").split(
    ","
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "doc_generation",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "pdf_engine": PDF_ENGINE,
        "supported_types": SUPPORTED_TYPES,
    }


@app.post("/generate")
async def generate_document(request: Dict[str, Any], background_tasks: BackgroundTasks):
    """Generate document (business plan, SOW, RFP)"""
    try:
        document_type = request.get("document_type")
        template_name = request.get("template_name")
        data = request.get("data", {})
        output_format = request.get("output_format", "pdf")

        if not document_type or document_type not in SUPPORTED_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid document type. Supported: {SUPPORTED_TYPES}",
            )

        job_id = f"{document_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        background_tasks.add_task(
            generate_document_task,
            job_id,
            document_type,
            template_name,
            data,
            output_format,
        )

        return {
            "job_id": job_id,
            "status": "queued",
            "document_type": document_type,
            "template": template_name,
            "output_format": output_format,
        }

    except Exception as e:
        logger.error(f"Failed to queue document generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def generate_document_task(
    job_id: str,
    document_type: str,
    template_name: str,
    data: Dict[str, Any],
    output_format: str,
):
    """Background task for document generation"""
    try:
        logger.info(f"Starting document generation job: {job_id}")

        # Generate document content via APAT service
        content = await generate_content_via_apat(document_type, template_name, data)

        if not content:
            raise Exception("Failed to generate content")

        # Generate document based on type
        if document_type == "business_plan":
            document = await generate_business_plan(content, data)
        elif document_type == "sow":
            document = await generate_sow(content, data)
        elif document_type == "rfp":
            document = await generate_rfp(content, data)
        elif document_type == "proposal":
            document = await generate_proposal(content, data)
        else:
            document = content

        # Generate final output
        if output_format == "pdf":
            pdf_result = await generate_pdf(document, job_id)
            if pdf_result:
                await store_document(job_id, document_type, document, pdf_result)
            else:
                await store_document(job_id, document_type, document)
        else:
            await store_document(job_id, document_type, document)

        logger.info(f"Document generation completed: {job_id}")

    except Exception as e:
        logger.error(f"Document generation failed for job {job_id}: {str(e)}")


async def generate_content_via_apat(
    document_type: str, template_name: str, data: Dict[str, Any]
) -> Optional[str]:
    """Generate content using APAT service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{APAT_SERVICE_URL}/jobs/generate",
                json={"type": document_type, "template": template_name, "data": data},
            )

            if response.status_code == 200:
                result = response.json()
                job_id = result["job_id"]

                # Poll for completion (simplified)
                for _ in range(10):  # Wait up to 10 attempts
                    await asyncio.sleep(30)  # Wait 30 seconds between polls

                    status_response = await client.get(
                        f"{APAT_SERVICE_URL}/jobs/{job_id}/status"
                    )

                    if status_response.status_code == 200:
                        status = status_response.json()
                        if status["status"] == "completed":
                            return status.get("content")
                        elif status["status"] == "failed":
                            raise Exception(f"APAT job failed: {status.get('error')}")

                logger.warning(f"APAT job {job_id} did not complete in time")

            else:
                logger.error(f"APAT service error: {response.status_code}")

    except Exception as e:
        logger.error(f"APAT content generation failed: {str(e)}")

    # Fallback: generate basic content locally
    return generate_fallback_content(document_type, data)


def generate_fallback_content(document_type: str, data: Dict[str, Any]) -> str:
    """Generate basic content as fallback"""
    if document_type == "business_plan":
        return generate_basic_business_plan(data)
    elif document_type == "sow":
        return generate_basic_sow(data)
    elif document_type == "rfp":
        return generate_basic_rfp(data)
    elif document_type == "proposal":
        return generate_basic_proposal(data)
    else:
        return f"Generated {document_type} content for: {data.get('title', 'Untitled')}"


def generate_basic_business_plan(data: Dict[str, Any]) -> str:
    """Generate basic business plan content"""
    template = """
# Business Plan: {title}

## Executive Summary

This business plan outlines the strategic approach for {title}. Based on our analysis, we have identified {num_opportunities} market opportunities with varying risk profiles.

### Key Highlights
- Total Addressable Market: ${tam:.1f} billion
- Growth Rate: {growth_rate:.1f}% annually
- Competitive Landscape: {competitive_analysis}

## Market Analysis

Our comprehensive market analysis reveals significant opportunities in the {sector} sector. The market is characterized by:

### Market Dynamics
- **Market Size**: ${market_size:.1f}B
- **Growth Drivers**: {growth_drivers}
- **Competitive Intensity**: {competitive_intensity}
- **Regulatory Environment**: {regulatory_status}

### Opportunities Identified
{opportunities_list}

## Financial Projections

### Revenue Projections
- Year 1: ${revenue_y1:.2f}M
- Year 2: ${revenue_y2:.2f}M  
- Year 3: ${revenue_y3:.2f}M

### Key Financial Metrics
- Gross Margin: {gross_margin:.1f}%
- Break-even Month: {breakeven_month}
- ROI: {roi:.1f}%

## Risk Analysis

### Risk Assessment
{risk_assessment}

### Mitigation Strategies
{risk_mitigation}

## Implementation Timeline

### Phase 1: Foundation (Months 1-3)
{phase1_deliverables}

### Phase 2: Growth (Months 4-8)
{phase2_deliverables}

### Phase 3: Scale (Months 9-12)
{phase3_deliverables}

## Conclusion

This business plan provides a comprehensive roadmap for success in the {sector} market. With careful execution of our strategy and continuous monitoring of market conditions, we are positioned to achieve our objectives.

---
*Generated on {generated_date}*
    """

    return template.format(
        title=data.get("title", "Market Opportunity"),
        num_opportunities=data.get("num_opportunities", 0),
        tam=data.get("total_addressable_market", 0),
        growth_rate=data.get("growth_rate", 15.0),
        competitive_analysis=data.get("competitive_analysis", "Competitive"),
        sector=data.get("sector", "Technology"),
        market_size=data.get("market_size", 1.0),
        growth_drivers=data.get("growth_drivers", "Innovation, Digital Transformation"),
        competitive_intensity=data.get("competitive_intensity", "High"),
        regulatory_status=data.get("regulatory_status", "Evolving"),
        opportunities_list=data.get(
            "opportunities_list", "• Opportunity A\n• Opportunity B"
        ),
        revenue_y1=data.get("revenue_y1", 0.5),
        revenue_y2=data.get("revenue_y2", 1.5),
        revenue_y3=data.get("revenue_y3", 3.0),
        gross_margin=data.get("gross_margin", 40.0),
        breakeven_month=data.get("breakeven_month", 18),
        roi=data.get("roi", 25.0),
        risk_assessment=data.get(
            "risk_assessment", "Standard business risks identified"
        ),
        risk_mitigation=data.get(
            "risk_mitigation", "Diversification, contingency planning"
        ),
        phase1_deliverables=data.get(
            "phase1_deliverables", "Market research, team formation"
        ),
        phase2_deliverables=data.get(
            "phase2_deliverables", "Product development, pilot customers"
        ),
        phase3_deliverables=data.get(
            "phase3_deliverables", "Full market launch, scaling operations"
        ),
        generated_date=datetime.now().strftime("%B %d, %Y"),
    )


def generate_basic_sow(data: Dict[str, Any]) -> str:
    """Generate basic Statement of Work content"""
    template = """
# Statement of Work: {project_name}

## Project Overview

This Statement of Work (SOW) defines the scope, deliverables, timeline, and terms for the {project_name} project.

### Project Objectives
{objectives}

### Success Criteria
{success_criteria}

## Scope of Work

### In-Scope Items
{in_scope_items}

### Out-of-Scope Items
{out_of_scope_items}

## Deliverables

### Primary Deliverables
{primary_deliverables}

### Secondary Deliverables
{secondary_deliverables}

## Timeline

### Project Schedule
**Start Date**: {start_date}
**End Date**: {end_date}
**Total Duration**: {duration}

### Key Milestones
{milestones}

## Resources and Responsibilities

### Client Responsibilities
{client_responsibilities}

### Vendor Responsibilities
{vendor_responsibilities}

## Risk Management

### Identified Risks
{identified_risks}

### Mitigation Strategies
{mitigation_strategies}

## Quality Assurance

### Testing Approach
{testing_approach}

### Acceptance Criteria
{acceptance_criteria}

## Commercial Terms

### Pricing Structure
{pricing_structure}

### Payment Terms
{payment_terms}

---
*Generated on {generated_date}*
    """

    return template.format(
        project_name=data.get("project_name", "IT Implementation"),
        objectives=data.get("objectives", "Deliver enterprise software solution"),
        success_criteria=data.get(
            "success_criteria", "On-time, within budget, meets requirements"
        ),
        in_scope_items=data.get(
            "in_scope_items", "• Core development\n• Testing\n• Documentation"
        ),
        out_of_scope_items=data.get(
            "out_of_scope_items", "• Training programs\n• Hardware procurement"
        ),
        primary_deliverables=data.get(
            "primary_deliverables", "• Working software\n• Technical documentation"
        ),
        secondary_deliverables=data.get(
            "secondary_deliverables", "• Training materials\n• Support documentation"
        ),
        start_date=data.get("start_date", "2024-01-01"),
        end_date=data.get("end_date", "2024-06-30"),
        duration=data.get("duration", "6 months"),
        milestones=data.get(
            "milestones",
            "• Design approval (Month 1)\n• Development milestone (Month 3)\n• Go-live (Month 6)",
        ),
        client_responsibilities=data.get(
            "client_responsibilities", "• Provide access to systems\n• Timely feedback"
        ),
        vendor_responsibilities=data.get(
            "vendor_responsibilities",
            "• Deliver all milestones\n• Provide regular updates",
        ),
        identified_risks=data.get(
            "identified_risks", "• Resource availability\n• Technical complexity"
        ),
        mitigation_strategies=data.get(
            "mitigation_strategies", "• Resource planning\n• Regular reviews"
        ),
        testing_approach=data.get(
            "testing_approach", "Unit, integration, and UAT testing"
        ),
        acceptance_criteria=data.get(
            "acceptance_criteria", "All requirements met, no critical bugs"
        ),
        pricing_structure=data.get("pricing_structure", "Fixed price: $X"),
        payment_terms=data.get("payment_terms", "Monthly invoices, Net 30"),
        generated_date=datetime.now().strftime("%B %d, %Y"),
    )


def generate_basic_rfp(data: Dict[str, Any]) -> str:
    """Generate basic RFP content"""
    template = """
# Request for Proposal: {rfp_title}

## Executive Summary

{organization_name} is seeking qualified vendors to provide {service_description}. This RFP outlines the requirements, evaluation criteria, and submission guidelines.

### RFP Purpose
{rfp_purpose}

### Budget Range
{budget_range}

### Timeline
**Release Date**: {release_date}
**Submission Deadline**: {submission_deadline}
**Vendor Presentations**: {presentation_dates}
**Award Date**: {award_date}

## Project Background

{project_background}

### Current State
{current_state}

### Desired Future State
{future_state}

## Requirements

### Functional Requirements
{functional_requirements}

### Technical Requirements
{technical_requirements}

### Performance Requirements
{performance_requirements}

### Security Requirements
{security_requirements}

### Compliance Requirements
{compliance_requirements}

## Evaluation Criteria

### Technical Capabilities (40%)
{technical_evaluation}

### Experience and Expertise (30%)
{experience_evaluation}

### Commercial Considerations (20%)
{commercial_evaluation}

### Implementation Approach (10%)
{implementation_evaluation}

## Submission Guidelines

### Required Documents
{required_documents}

### Proposal Format
{proposal_format}

### Submission Process
{submission_process}

## Terms and Conditions

### Contract Type
{contract_type}

### Insurance Requirements
{insurance_requirements}

### Intellectual Property
{ip_requirements}

---
*Questions regarding this RFP should be directed to: {contact_person}*

*Generated on {generated_date}*
    """

    return template.format(
        rfp_title=data.get("rfp_title", "Enterprise Software Implementation"),
        organization_name=data.get("organization_name", "Company Name"),
        service_description=data.get(
            "service_description", "Enterprise software solution"
        ),
        rfp_purpose=data.get(
            "rfp_purpose", "Seek qualified vendor for software implementation"
        ),
        budget_range=data.get("budget_range", "$500,000 - $1,000,000"),
        release_date=data.get("release_date", "2024-01-01"),
        submission_deadline=data.get("submission_deadline", "2024-02-01"),
        presentation_dates=data.get("presentation_dates", "2024-02-15-2024-02-28"),
        award_date=data.get("award_date", "2024-03-15"),
        project_background=data.get(
            "project_background", "Modernization of legacy systems"
        ),
        current_state=data.get("current_state", "Legacy systems in use"),
        future_state=data.get("future_state", "Modern, integrated solution"),
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
        security_requirements=data.get(
            "security_requirements",
            "• Data encryption\n• Access controls\n• Audit trails",
        ),
        compliance_requirements=data.get(
            "compliance_requirements", "• GDPR compliance\n• SOC 2 Type II"
        ),
        technical_evaluation=data.get(
            "technical_evaluation",
            "• Architecture and design\n• Technology stack\n• Scalability",
        ),
        experience_evaluation=data.get(
            "experience_evaluation",
            "• Relevant experience\n• Team qualifications\n• Reference projects",
        ),
        commercial_evaluation=data.get(
            "commercial_evaluation",
            "• Cost competitiveness\n• Payment terms\n• Risk allocation",
        ),
        implementation_evaluation=data.get(
            "implementation_evaluation",
            "• Project methodology\n• Timeline feasibility\n• Risk management",
        ),
        required_documents=data.get(
            "required_documents",
            "• Technical proposal\n• Commercial proposal\n• Team resumes\n• References",
        ),
        proposal_format=data.get("proposal_format", "PDF format, maximum 50 pages"),
        submission_process=data.get(
            "submission_process", "Submit via email by deadline"
        ),
        contract_type=data.get("contract_type", "Fixed price with milestone payments"),
        insurance_requirements=data.get(
            "insurance_requirements", "$2M professional liability"
        ),
        ip_requirements=data.get("ip_requirements", "Client owns all deliverables"),
        contact_person=data.get("contact_person", "procurement@company.com"),
        generated_date=datetime.now().strftime("%B %d, %Y"),
    )


def generate_basic_proposal(data: Dict[str, Any]) -> str:
    """Generate basic proposal content"""
    template = """
# Proposal: {project_name}

## Executive Summary

{proposal_summary}

## Understanding of Requirements

{requirements_understanding}

## Solution Approach

{solution_approach}

### Technology Stack
{technology_stack}

### Implementation Methodology
{implementation_methodology}

## Project Timeline

{timeline_details}

## Team and Expertise

{team_overview}

### Key Personnel
{key_personnel}

## Risk Management

{risk_analysis}

## Pricing

{pricing_details}

## Why Choose Us

{competitive_advantages}

---
*Generated on {generated_date}*
    """

    return template.format(
        project_name=data.get("project_name", "IT Implementation Project"),
        proposal_summary=data.get(
            "proposal_summary",
            "We propose a comprehensive solution for your requirements",
        ),
        requirements_understanding=data.get(
            "requirements_understanding",
            "We understand the project goals and constraints",
        ),
        solution_approach=data.get(
            "solution_approach", "Our approach focuses on proven methodologies"
        ),
        technology_stack=data.get(
            "technology_stack", "Modern, scalable technology stack"
        ),
        implementation_methodology=data.get(
            "implementation_methodology", "Agile methodology with iterative delivery"
        ),
        timeline_details=data.get(
            "timeline_details", "Detailed timeline with key milestones"
        ),
        team_overview=data.get(
            "team_overview", "Experienced team with relevant expertise"
        ),
        key_personnel=data.get(
            "key_personnel", "Dedicated team with named individuals"
        ),
        risk_analysis=data.get(
            "risk_analysis", "Comprehensive risk assessment and mitigation"
        ),
        pricing_details=data.get(
            "pricing_details", "Transparent pricing with detailed breakdown"
        ),
        competitive_advantages=data.get(
            "competitive_advantages", "Our unique value proposition"
        ),
        generated_date=datetime.now().strftime("%B %d, %Y"),
    )


async def generate_pdf(content: str, job_id: str) -> Optional[str]:
    """Generate PDF from content"""
    try:
        # In a real implementation, this would use weasyprint or similar
        # For now, return a mock PDF URL
        pdf_filename = f"{job_id}.pdf"
        pdf_path = f"/app/output/{pdf_filename}"

        # Mock PDF generation
        # In reality, you would:
        # 1. Convert markdown to HTML
        # 2. Use weasyprint or similar to generate PDF
        # 3. Store PDF in file system or cloud storage

        return pdf_path

    except Exception as e:
        logger.error(f"PDF generation failed: {str(e)}")
        return None


async def store_document(
    job_id: str, document_type: str, content: str, pdf_path: Optional[str] = None
):
    """Store generated document"""
    try:
        document_data = {
            "id": job_id,
            "document_type": document_type,
            "title": f"{document_type.title()} - {datetime.now().strftime('%B %d, %Y')}",
            "content": content,
            "pdf_path": pdf_path,
            "status": "completed",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Store in MCP
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MCP_SERVICE_URL}/api/documents", json=document_data
            )

            if response.status_code == 200:
                logger.info(f"Document stored: {job_id}")
            else:
                logger.error(f"Failed to store document: {response.status_code}")

    except Exception as e:
        logger.error(f"Document storage failed: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8050, reload=True, log_level="info")
