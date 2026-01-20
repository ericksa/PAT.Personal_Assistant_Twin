# services/ingest/resume_processor.py
from typing import Dict, List
import json
from pydantic import BaseModel
import re


class ResumeSection(BaseModel):
    """Structured representation of resume sections"""
    contact_info: Dict[str, str] = {}
    summary: str = ""
    skills: List[str] = []
    experience: List[Dict] = []
    education: List[Dict] = []
    certifications: List[Dict] = []
    projects: List[Dict] = []


class ResumeProcessor:
    """Process and extract structured information from resumes"""

    def __init__(self):
        self.sections_keywords = {
            'contact_info': ['contact', 'phone', 'email', 'address', 'linkedin'],
            'summary': ['summary', 'objective', 'profile'],
            'skills': ['skills', 'technologies', 'tools', 'competencies'],
            'experience': ['experience', 'work', 'employment', 'positions'],
            'education': ['education', 'degree', 'university', 'school'],
            'certifications': ['certification', 'certificates'],
            'projects': ['projects', 'portfolio']
        }

    def extract_contact_info(self, text: str) -> Dict[str, str]:
        """Extract contact information from resume text"""
        contact_info = {}

        # Email extraction
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            contact_info['email'] = emails[0]

        # Phone extraction
        phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phones = re.findall(phone_pattern, text)
        if phones:
            contact_info['phone'] = phones[0]

        # LinkedIn extraction
        linkedin_pattern = r'(linkedin\.com\/in\/[^\s]+)'
        linkedin_matches = re.findall(linkedin_pattern, text, re.IGNORECASE)
        if linkedin_matches:
            contact_info['linkedin'] = f"https://www.{linkedin_matches[0]}"

        return contact_info

    def extract_skills(self, text: str) -> List[str]:
        """Extract technical skills from resume"""
        # Common technical skill categories
        tech_skills = [
            'Python', 'Java', 'JavaScript', 'React', 'Node.js', 'SQL', 'MongoDB',
            'AWS', 'Docker', 'Kubernetes', 'Git', 'Linux', 'TensorFlow', 'PyTorch',
            'Machine Learning', 'Data Science', 'API', 'REST', 'GraphQL',
            'CI/CD', 'Agile', 'Scrum', 'DevOps', 'Cloud', 'Azure', 'GCP'
        ]

        found_skills = []
        text_lower = text.lower()

        for skill in tech_skills:
            if skill.lower() in text_lower:
                found_skills.append(skill)

        # Also extract skills from "Skills" section
        skills_section = self._extract_section(text, 'skills')
        if skills_section:
            # Simple extraction of capitalized words/phrases
            words = re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', skills_section)
            found_skills.extend([word for word in words if len(word) > 2])

        return list(set(found_skills))  # Remove duplicates

    def extract_experience(self, text: str) -> List[Dict]:
        """Extract work experience from resume"""
        experiences = []

        # Look for experience sections
        exp_sections = self._extract_section_blocks(text, 'experience')

        for section in exp_sections:
            # Extract company, position, dates
            exp_dict = {
                'company': self._extract_company(section),
                'position': self._extract_position(section),
                'dates': self._extract_dates(section),
                'description': self._clean_description(section)
            }
            if exp_dict['company'] or exp_dict['position']:
                experiences.append(exp_dict)

        return experiences

    def process_resume(self, resume_text: str) -> ResumeSection:
        """Process complete resume and return structured data"""
        resume = ResumeSection()

        # Extract each section
        resume.contact_info = self.extract_contact_info(resume_text)
        resume.skills = self.extract_skills(resume_text)
        resume.experience = self.extract_experience(resume_text)
        resume.education = self._extract_education(resume_text)
        resume.certifications = self._extract_certifications(resume_text)
        resume.projects = self._extract_projects(resume_text)
        resume.summary = self._extract_summary(resume_text)

        return resume

    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract specific section from text"""
        section_patterns = [
            rf'{section_name}.*?(?=\n[A-Z][a-z]+|$)',
            rf'(?i){section_name}.*?(?=\n\n|\Z)'
        ]

        for pattern in section_patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(0)
        return ""

    def _extract_section_blocks(self, text: str, section_name: str) -> List[str]:
        """Extract multiple blocks from a section"""
        section_text = self._extract_section(text, section_name)
        if not section_text:
            return []

        # Split by experience entries (look for date patterns)
        blocks = re.split(r'\n(?=\d{4}|[A-Z][a-z]+\s+\d{4})', section_text)
        return [block.strip() for block in blocks if block.strip()]

    def _extract_company(self, text: str) -> str:
        """Extract company name from experience block"""
        lines = text.split('\n')
        for line in lines[:3]:  # Check first few lines
            # Look for capitalized company names
            company_match = re.search(r'^[A-Z][A-Za-z\s&.,-]+$', line.strip())
            if company_match and len(company_match.group(0)) > 2:
                return company_match.group(0)
        return ""

    def _extract_position(self, text: str) -> str:
        """Extract job position from experience block"""
        # Look for common job titles
        job_titles = [
            'Software Engineer', 'Developer', 'Analyst', 'Manager', 'Architect',
            'Consultant', 'Specialist', 'Lead', 'Senior', 'Junior'
        ]

        for title in job_titles:
            if title.lower() in text.lower():
                # Extract the full title
                pattern = rf'([A-Z][a-zA-Z\s]*{title}[a-zA-Z\s]*)'
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(1).strip()

        return ""

    def _extract_dates(self, text: str) -> str:
        """Extract employment dates"""
        date_pattern = r'(?:\d{1,2}/\d{4}|\d{4})\s*[-–—]\s*(?:\d{1,2}/\d{4}|\d{4}|present|current)'
        matches = re.findall(date_pattern, text, re.IGNORECASE)
        return matches[0] if matches else ""

    def _clean_description(self, text: str) -> str:
        """Clean and extract job description"""
        # Remove company and position lines
        lines = text.split('\n')
        description_lines = []

        for line in lines:
            line_clean = line.strip()
            # Skip if it looks like a header (company/position)
            if not (line_clean.isupper() and len(line_clean.split()) < 5):
                if line_clean and not re.match(r'^\d{4}', line_clean):
                    description_lines.append(line_clean)

        return '\n'.join(description_lines[-10:]) if description_lines else ""  # Last 10 lines

    def _extract_education(self, text: str) -> List[Dict]:
        """Extract education information"""
        education_section = self._extract_section(text, 'education')
        educations = []

        if education_section:
            # Simple extraction for now
            educations.append({
                'institution': 'Extracted from resume',
                'degree': 'Extracted from resume',
                'field': 'Extracted from resume',
                'dates': 'Extracted from resume'
            })

        return educations

    def _extract_certifications(self, text: str) -> List[Dict]:
        """Extract certifications"""
        cert_section = self._extract_section(text, 'certifications')
        certifications = []

        if cert_section:
            certifications.append({
                'name': 'Extracted Certification',
                'issuer': 'Extracted Issuer',
                'date': 'Extracted Date'
            })

        return certifications

    def _extract_projects(self, text: str) -> List[Dict]:
        """Extract project information"""
        projects_section = self._extract_section(text, 'projects')
        projects = []

        if projects_section:
            projects.append({
                'name': 'Extracted Project',
                'description': 'Extracted description',
                'technologies': ['Extracted tech']
            })

        return projects

    def _extract_summary(self, text: str) -> str:
        """Extract professional summary"""
        summary_section = self._extract_section(text, 'summary')
        return summary_section[:500] if summary_section else "Professional summary extracted from resume"


# Usage example
if __name__ == "__main__":
    processor = ResumeProcessor()

    # Example resume text (you would get this from uploaded file)
    sample_resume = """
    John Doe
    john.doe@email.com | (555) 123-4567 | linkedin.com/in/johndoe

    PROFESSIONAL SUMMARY
    Experienced Software Engineer with 5+ years in AI and machine learning development.

    SKILLS
    Python, Machine Learning, TensorFlow, PyTorch, SQL, Docker, AWS

    EXPERIENCE
    Senior AI Engineer | TechCorp | 2022-Present
    - Developed machine learning models for predictive analytics
    - Led team of 3 engineers on AI projects

    SOFTWARE ENGINEER | StartupXYZ | 2020-2022
    - Built recommendation systems using collaborative filtering
    - Implemented CI/CD pipelines for ML models
    """

    resume_data = processor.process_resume(sample_resume)
    print(json.dumps(resume_data.dict(), indent=2))
