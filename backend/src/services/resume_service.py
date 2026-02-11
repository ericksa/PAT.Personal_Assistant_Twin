# services/jobs/resume_customizer.py - Enhanced Resume Generator for Government Jobs
from typing import Dict, List, Optional
import json
import os
import re
from datetime import datetime, date
from enum import Enum


class ResumeFormat(Enum):
    CHRONOLOGICAL = "chronological"
    FUNCTIONAL = "functional"
    COMBINATION = "combination"
    ATS_FRIENDLY = "ats_friendly"


class GovernmentResumeCustomizer:
    """Enhanced resume generator for government contracting jobs"""

    def __init__(self):
        self.government_keywords = [
            "government",
            "federal",
            "contract",
            "DoD",
            "defense",
            "VA",
            "DHA",
            "clearance",
            "security",
            "compliance",
            "regulatory",
            "veterans affairs",
            "defense health agency",
            "public sector",
            "government acquisition",
        ]

        self.clearance_phrases = [
            "secret clearance",
            "top secret",
            "security clearance",
            "DOD clearance",
            "government clearance",
            "TS/SCI",
        ]

    async def generate_custom_resume(
        self,
        job_description: str,
        document_ids: List[str],
        user_documents: List[Dict],
        format: ResumeFormat = ResumeFormat.ATS_FRIENDLY,
    ) -> str:
        """Generate a customized resume for a specific government job"""

        # Analyze job requirements
        job_analysis = self._analyze_job_description(job_description)

        # Process user documents to extract structured resume data
        resume_data = self._process_user_documents(user_documents)

        # Enhance resume data for government jobs
        enhanced_resume = self._enhance_for_government_jobs(resume_data, job_analysis)

        # Generate ATS-friendly resume
        if format == ResumeFormat.ATS_FRIENDLY:
            return self._generate_ats_resume(enhanced_resume, job_analysis)
        else:
            return self._generate_standard_resume(enhanced_resume, job_analysis)

    def _analyze_job_description(self, job_description: str) -> Dict:
        """Extract key requirements from job description"""
        analysis = {
            "skills": [],
            "technologies": [],
            "clearance_required": False,
            "government_focus": False,
            "agencies": [],
            "experience_years": 0,
        }

        # Check for clearance requirements
        analysis["clearance_required"] = any(
            phrase.lower() in job_description.lower()
            for phrase in self.clearance_phrases
        )

        # Check for government focus
        analysis["government_focus"] = any(
            keyword.lower() in job_description.lower()
            for keyword in self.government_keywords
        )

        # Extract technical skills
        tech_keywords = [
            "Java",
            "Spring Boot",
            "AWS",
            "API",
            "microservices",
            "DevOps",
            "Python",
            "Docker",
            "Kubernetes",
            "SQL",
            "PostgreSQL",
            "MongoDB",
            "React",
            "Node.js",
            "TypeScript",
            "REST",
            "GraphQL",
            "Git",
        ]

        for tech in tech_keywords:
            if tech.lower() in job_description.lower():
                analysis["skills"].append(tech)
                analysis["technologies"].append(tech)

        # Extract agency mentions
        agencies = {
            "VA": ["veterans affairs", "VA", "veterans administration"],
            "DHA": ["defense health agency", "DHA", "military health"],
            "DOD": ["department of defense", "DOD", "defense department"],
            "DOT": ["department of transportation", "DOT"],
        }

        for agency, patterns in agencies.items():
            for pattern in patterns:
                if re.search(pattern, job_description, re.IGNORECASE):
                    analysis["agencies"].append(agency)
                    break

        # Extract experience requirement
        experience_patterns = [
            r"(\d+)[\+\-]?\s*(?:year|yr)s?",
            r"\s?(5|7|10)\s*(?:year|yr)s?",
        ]

        for pattern in experience_patterns:
            matches = re.findall(pattern, job_description, re.IGNORECASE)
            if matches:
                analysis["experience_years"] = max(
                    analysis["experience_years"],
                    max(int(m) for m in matches if m.isdigit()),
                )

        return analysis

    def _process_user_documents(self, documents: List[Dict]) -> Dict:
        """Process uploaded PAT documents into structured resume data"""
        resume_data = {
            "contact_info": {},
            "summary": "",
            "skills": [],
            "experience": [],
            "education": [],
            "certifications": [],
            "projects": [],
        }

        # Simple extraction from document content
        # In production, this would use advanced NLP or existing PAT processors
        for doc in documents:
            content = doc.get("content", "")

            # Extract skills (basic keyword matching)
            common_skills = [
                "Java",
                "Python",
                "AWS",
                "Docker",
                "Spring Boot",
                "API",
                "REST",
                "SQL",
                "Git",
                "DevOps",
                "Kubernetes",
            ]

            for skill in common_skills:
                if skill.lower() in content.lower():
                    resume_data["skills"].append(skill)

            # Extract experience patterns
            exp_patterns = [
                r"(Senior|Junior|Lead|Software|Backend|DevOps)[\s\w]*Engineer",
                r"(Developer|Architect|Specialist|Consultant)",
            ]

            for pattern in exp_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if match:
                        resume_data["experience"].append(
                            {
                                "position": match[0]
                                if isinstance(match, tuple)
                                else match,
                                "description": f"Extracted from uploaded documents",
                                "technologies": resume_data["skills"][:5],  # Top skills
                            }
                        )

        # Remove duplicates
        resume_data["skills"] = list(set(resume_data["skills"]))

        return resume_data

    def _enhance_for_government_jobs(
        self, resume_data: Dict, job_analysis: Dict
    ) -> Dict:
        """Enhance resume data for government job applications"""
        enhanced = resume_data.copy()

        # Add clearance emphasis if required
        if job_analysis["clearance_required"]:
            enhanced["summary"] = self._add_clearance_emphasis(
                enhanced.get("summary", ""), job_analysis
            )

            # Add clearance section to experience if missing
            if job_analysis["clearance_required"]:
                enhanced["experience"].insert(
                    0,
                    {
                        "position": "Security Cleared Software Engineer",
                        "description": "Experience working on government contracts requiring security clearance",
                        "technologies": [
                            "Government Compliance",
                            "Security Protocols",
                            "Federated Systems",
                        ],
                    },
                )

        # Prioritize government-related skills
        if job_analysis["government_focus"]:
            enhanced["skills"] = self._prioritize_government_skills(enhanced["skills"])

            # Add government-specific summary
            if "government" not in enhanced.get("summary", "").lower():
                enhanced["summary"] = (
                    f"Experienced software engineer with government contract experience. {enhanced.get('summary', '')}"
                )

        return enhanced

    def _add_clearance_emphasis(self, summary: str, job_analysis: Dict) -> str:
        """Add security clearance emphasis to resume summary"""
        clearance_phrases = [
            "security-cleared professional",
            "experienced with government security requirements",
            "background includes security clearance work",
        ]

        if not any(phrase in summary.lower() for phrase in clearance_phrases):
            return f"{clearance_phrases[0]}. {summary}"
        return summary

    def _prioritize_government_skills(self, skills: List[str]) -> List[str]:
        """Prioritize skills relevant to government work"""
        gov_priority_skills = [
            "Java",
            "Spring Boot",
            "AWS",
            "API",
            "Government Compliance",
            "Security",
            "DevOps",
            "Docker",
            "Kubernetes",
            "SQL",
        ]

        # Move government-relevant skills to front
        prioritized = [s for s in skills if s in gov_priority_skills]
        other_skills = [s for s in skills if s not in gov_priority_skills]

        return prioritized + other_skills

    def _generate_ats_resume(self, resume_data: Dict, job_analysis: Dict) -> str:
        """Generate ATS-friendly resume"""
        # ATS-friendly formatting
        sections = []

        # Contact Info
        sections.append("CONTACT INFORMATION")
        sections.append("-" * 20)
        if resume_data.get("contact_info"):
            for key, value in resume_data["contact_info"].items():
                sections.append(f"{key.upper()}: {value}")
        else:
            sections.append(
                "Email: [Your Email] | Phone: [Your Phone] | LinkedIn: [Your LinkedIn]"
            )
        sections.append("")

        # Summary - optimized for ATS
        sections.append("PROFESSIONAL SUMMARY")
        sections.append("-" * 20)
        summary = resume_data.get("summary", "")
        if not summary:
            summary = (
                "Experienced software engineer with government contract experience"
            )
        if job_analysis["clearance_required"]:
            summary = f"Security-cleared {summary.lower()}"
        sections.append(summary)
        sections.append("")

        # Technical Skills - ATS keywords
        sections.append("TECHNICAL SKILLS")
        sections.append("-" * 20)
        skills = resume_data.get("skills", [])
        if skills:
            sections.append(", ".join(skills[:15]))  # Limit for ATS
        sections.append("")

        # Professional Experience - ATS-friendly format
        sections.append("PROFESSIONAL EXPERIENCE")
        sections.append("-" * 20)
        for exp in resume_data.get("experience", [])[:3]:  # Top 3 most relevant
            position = exp.get("position", "Software Engineer")
            desc = exp.get("description", "Extracted from experience")
            sections.append(f"{position}")
            sections.append(f"• {desc}")
            if exp.get("technologies"):
                sections.append(f"Technologies: {', '.join(exp['technologies'][:5])}")
            sections.append("")

        # Government-Relevant Experience Header
        if job_analysis["government_focus"]:
            sections.append("GOVERNMENT CONTRACT EXPERIENCE")
            sections.append("-" * 20)
            sections.append(
                "Demonstrated experience with federal agencies and compliance requirements"
            )
            sections.append("")

        return "\n".join(sections)

    def _generate_standard_resume(self, resume_data: Dict, job_analysis: Dict) -> str:
        """Generate standard formatted resume"""
        # Similar structure but with more detailed formatting
        return self._generate_ats_resume(
            resume_data, job_analysis
        )  # Use ATS format for now

    def generate_word_resume(self, resume_data: Dict, job_analysis: Dict) -> str:
        """Generate Word-friendly resume text"""
        # For now, return ATS format which is Word-friendly
        return self._generate_ats_resume(resume_data, job_analysis)


# Usage example
async def main():
    customizer = GovernmentResumeCustomizer()

    # Mock job description
    job_desc = """
    Senior Software Engineer - Department of Defense
    Secret clearance required
    
    We are seeking a Senior Software Engineer with Java Spring Boot experience 
    for Department of Defense contracts. Must have active secret clearance.
    AWS, API development, and 5+ years experience required.
    """

    # Mock documents (would come from PAT system)
    mock_docs = [
        {
            "content": "Experienced Java developer with Spring Boot and AWS experience. "
            "Worked on government projects requiring compliance."
        }
    ]

    resume = await customizer.generate_custom_resume(
        job_description=job_desc,
        document_ids=["doc1", "doc2"],
        user_documents=mock_docs,
        format=ResumeFormat.ATS_FRIENDLY,
    )

    print(resume)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
