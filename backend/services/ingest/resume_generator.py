# services/agent/resume_generator.py
from typing import Dict, List
import json
from jinja2 import Template


class ResumeGenerator:
    """Generate customized resumes for specific job positions"""

    def __init__(self):
        # Templates for different resume formats
        self.templates = {
            'chronological': self._chronological_template(),
            'functional': self._functional_template(),
            'combination': self._combination_template()
        }

    def generate_resume(self, resume_data: Dict, job_description: str,
                        template_type: str = 'chronological') -> str:
        """Generate customized resume for specific job"""

        # Analyze job description for key requirements
        job_requirements = self._analyze_job_description(job_description)

        # Score experience relevance
        scored_experience = self._score_experience(resume_data.get('experience', []), job_requirements)

        # Select most relevant experience
        relevant_experience = self._select_relevant_experience(scored_experience)

        # Generate customized summary
        customized_summary = self._customize_summary(resume_data.get('summary', ''), job_requirements)

        # Generate skills section focused on job requirements
        customized_skills = self._customize_skills(resume_data.get('skills', []), job_requirements)

        # Render resume template
        template = Template(self.templates.get(template_type, self.templates['chronological']))

        rendered_resume = template.render(
            contact_info=resume_data.get('contact_info', {}),
            summary=customized_summary,
            skills=customized_skills,
            experience=relevant_experience,
            education=resume_data.get('education', []),
            certifications=resume_data.get('certifications', []),
            projects=resume_data.get('projects', [])
        )

        return rendered_resume

    def _analyze_job_description(self, job_description: str) -> Dict[str, List[str]]:
        """Extract key requirements from job description"""
        requirements = {
            'skills': [],
            'technologies': [],
            'responsibilities': [],
            'qualifications': []
        }

        # Simple keyword extraction (in production, use NLP)
        tech_keywords = [
            'Python', 'Java', 'JavaScript', 'React', 'Node.js', 'SQL', 'MongoDB',
            'AWS', 'Docker', 'Kubernetes', 'Git', 'Linux', 'TensorFlow', 'PyTorch',
            'Machine Learning', 'Data Science', 'API', 'REST', 'GraphQL',
            'CI/CD', 'Agile', 'Scrum', 'DevOps', 'Cloud', 'Azure', 'GCP'
        ]

        # Extract technical skills
        for keyword in tech_keywords:
            if keyword.lower() in job_description.lower():
                requirements['skills'].append(keyword)
                requirements['technologies'].append(keyword)

        # Extract responsibilities (verbs)
        responsibility_verbs = [
            'develop', 'design', 'implement', 'manage', 'lead', 'optimize',
            'analyze', 'deploy', 'maintain', 'troubleshoot', 'collaborate'
        ]

        for verb in responsibility_verbs:
            if verb.lower() in job_description.lower():
                requirements['responsibilities'].append(verb)

        return requirements

    def _score_experience(self, experience: List[Dict], requirements: Dict) -> List[Dict]:
        """Score experience entries based on job requirements"""
        scored_experience = []

        for exp in experience:
            score = 0
            matched_skills = []

            # Check skills match
            exp_description = f"{exp.get('position', '')} {exp.get('description', '')}".lower()

            for skill in requirements.get('skills', []):
                if skill.lower() in exp_description:
                    score += 2
                    matched_skills.append(skill)

            # Check responsibilities match
            for resp in requirements.get('responsibilities', []):
                if resp.lower() in exp_description:
                    score += 1

            exp_copy = exp.copy()
            exp_copy['relevance_score'] = score
            exp_copy['matched_skills'] = matched_skills
            scored_experience.append(exp_copy)

        # Sort by relevance score
        scored_experience.sort(key=lambda x: x['relevance_score'], reverse=True)
        return scored_experience

    def _select_relevant_experience(self, scored_experience: List[Dict], max_entries: int = 3) -> List[Dict]:
        """Select most relevant experience entries"""
        # Filter out low-scoring entries
        relevant = [exp for exp in scored_experience if exp['relevance_score'] > 0]

        # Return top entries
        return relevant[:max_entries] if relevant else scored_experience[:max_entries]

    def _customize_summary(self, original_summary: str, requirements: Dict) -> str:
        """Customize professional summary for job requirements"""
        if not requirements.get('skills') and not requirements.get('responsibilities'):
            return original_summary

        # Enhance summary with job-specific elements
        skills_mention = ", ".join(requirements.get('skills', [])[:3])
        if skills_mention:
            return f"{original_summary} Specializing in {skills_mention}."

        return original_summary

    def _customize_skills(self, original_skills: List[str], requirements: Dict) -> List[str]:
        """Prioritize skills based on job requirements"""
        required_skills = set(requirements.get('skills', []))
        original_skills_set = set(original_skills)

        # Prioritize required skills that match
        prioritized = list(required_skills.intersection(original_skills_set))

        # Add remaining skills
        remaining = list(original_skills_set - required_skills)

        return prioritized + remaining

    def _chronological_template(self) -> str:
        """Template for chronological resume format"""
        return """
{{ contact_info.get('name', '') }}
{{ contact_info.get('email', '') }} | {{ contact_info.get('phone', '') }} | {{ contact_info.get('linkedin', '') }}

PROFESSIONAL SUMMARY
{{ summary }}

TECHNICAL SKILLS
{% for skill in skills %}{{ skill }}{% if not loop.last %}, {% endif %}{% endfor %}

PROFESSIONAL EXPERIENCE
{% for exp in experience %}
{{ exp.get('position', '') }} | {{ exp.get('company', '') }} | {{ exp.get('dates', '') }}
{% if exp.get('description', '') %}
{{ exp.get('description', '') }}
{% endif %}
{% endfor %}

EDUCATION
{% for edu in education %}
{{ edu.get('degree', '') }} | {{ edu.get('institution', '') }} | {{ edu.get('dates', '') }}
{% endfor %}

CERTIFICATIONS
{% for cert in certifications %}
{{ cert.get('name', '') }} | {{ cert.get('issuer', '') }} | {{ cert.get('date', '') }}
{% endfor %}
"""

    def _functional_template(self) -> str:
        """Template for functional resume format"""
        return """
{{ contact_info.get('name', '') }}
{{ contact_info.get('email', '') }} | {{ contact_info.get('phone', '') }} | {{ contact_info.get('linkedin', '') }}

PROFESSIONAL SUMMARY
{{ summary }}

CORE COMPETENCIES
{% for skill in skills %}{{ skill }}{% if not loop.last %}, {% endif %}{% endfor %}

PROFESSIONAL EXPERIENCE
{% for exp in experience %}
{{ exp.get('position', '') }} | {{ exp.get('company', '') }} | {{ exp.get('dates', '') }}
{% if exp.get('description', '') %}
{{ exp.get('description', '') }}
{% endif %}
{% endfor %}

EDUCATION & CERTIFICATIONS
{% for edu in education %}
{{ edu.get('degree', '') }} | {{ edu.get('institution', '') }} | {{ edu.get('dates', '') }}
{% endfor %}
{% for cert in certifications %}
{{ cert.get('name', '') }} | {{ cert.get('issuer', '') }} | {{ cert.get('date', '') }}
{% endfor %}
"""

    def _combination_template(self) -> str:
        """Template for combination resume format"""
        return """
{{ contact_info.get('name', '') }}
{{ contact_info.get('email', '') }} | {{ contact_info.get('phone', '') }} | {{ contact_info.get('linkedin', '') }}

PROFESSIONAL SUMMARY
{{ summary }}

KEY SKILLS & COMPETENCIES
{% for skill in skills %}{{ skill }}{% if not loop.last %}, {% endif %}{% endfor %}

CORE QUALIFICATIONS
{% for exp in experience %}
• {{ exp.get('position', '') }} at {{ exp.get('company', '') }}: {{ exp.get('description', '')[:100] }}...
{% endfor %}

PROFESSIONAL HISTORY
{% for exp in experience %}
{{ exp.get('position', '') }} | {{ exp.get('company', '') }} | {{ exp.get('dates', '') }}
{% if exp.get('description', '') %}
{{ exp.get('description', '') }}
{% endif %}
{% endfor %}

EDUCATION
{% for edu in education %}
{{ edu.get('degree', '') }} | {{ edu.get('institution', '') }} | {{ edu.get('dates', '') }}
{% endfor %}
"""


# Usage example
if __name__ == "__main__":
    generator = ResumeGenerator()

    # Sample resume data (from your resume processor)
    sample_resume_data = {
        "contact_info": {
            "name": "John Doe",
            "email": "john.doe@email.com",
            "phone": "(555) 123-4567",
            "linkedin": "linkedin.com/in/johndoe"
        },
        "summary": "Experienced Software Engineer with 5+ years in AI and machine learning development.",
        "skills": ["Python", "Machine Learning", "TensorFlow", "PyTorch", "SQL", "Docker", "AWS"],
        "experience": [
            {
                "company": "TechCorp",
                "position": "Senior AI Engineer",
                "dates": "2022-Present",
                "description": "Developed machine learning models for predictive analytics. Led team of 3 engineers on AI projects."
            },
            {
                "company": "StartupXYZ",
                "position": "SOFTWARE ENGINEER",
                "dates": "2020-2022",
                "description": "Built recommendation systems using collaborative filtering. Implemented CI/CD pipelines for ML models."
            }
        ],
        "education": [
            {
                "institution": "University of Technology",
                "degree": "MS Computer Science",
                "field": "Artificial Intelligence",
                "dates": "2018-2020"
            }
        ]
    }

    # Sample job description
    job_description = """
    Senior Machine Learning Engineer - We are looking for an experienced ML engineer to join our team.
    Requirements: Python, TensorFlow, PyTorch, AWS, Docker, experience with recommendation systems.
    Responsibilities include developing predictive models and leading ML initiatives.
    """

    # Generate customized resume
    customized_resume = generator.generate_resume(sample_resume_data, job_description)
    print(customized_resume)
