# Contributing to PAT - Personal Assistant Twin

Welcome! We're excited that you're interested in contributing to PAT. This document provides guidelines and information to help you get started.

## 🤝 Welcome Contributors

PAT is an open-source project aimed at helping professionals excel in technical interviews through AI assistance. We welcome contributions from developers, AI researchers, UX designers, and anyone passionate about making interview preparation more accessible.

## 📋 Table of Contents
1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Project Structure](#project-structure)
5. [How to Contribute](#how-to-contribute)
6. [Coding Standards](#coding-standards)
7. [Testing](#testing)
8. [Documentation](#documentation)
9. [Pull Request Process](#pull-request-process)
10. [Community](#community)

## 📜 Code of Conduct

This project follows a code of conduct to ensure a welcoming and inclusive environment. By participating, you agree to:

- Be respectful and constructive
- Welcome newcomers and encourage diverse perspectives
- Focus on what is best for the community
- Show empathy towards other community members
- Accept constructive criticism gracefully

## 🚀 Getting Started

### Prerequisites
- Familiarity with Python and Docker
- Understanding of REST APIs and microservices
- Basic knowledge of AI/ML concepts (helpful but not required)
- Experience with FastAPI (preferred)

### Finding Issues to Work On
- Check [GitHub Issues](../../issues) for bugs and feature requests
- Look for labels like `good first issue`, `help wanted`, or `beginner`
- Join our community discussions to suggest new features

## 💻 Development Setup

### Fork and Clone
```bash
# Fork the repository on GitHub
git clone https://github.com/YOUR_USERNAME/PAT.git
cd PAT/backend
```

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Start development services
docker-compose up -d

# Install Ollama and models (see README.md)
```

### Development Branches
- `main`: Production-ready code
- `develop`: Active development branch
- `feature/*`: Feature-specific branches
- `hotfix/*`: Emergency fixes

## 🏗️ Project Structure

```
PAT/backend/
├── services/
│   ├── agent/           # AI brain with RAG
│   │   ├── app.py       # Main FastAPI application
│   │   ├── llm.py       # LLM integration
│   │   └── utils.py     # Utility functions
│   ├── ingest/          # Document processing
│   ├── teleprompter/    # On-screen display
│   └── whisper/         # Audio transcription
├── data/                # Uploaded documents
├── docs/                # Documentation
├── scripts/             # Helper scripts
├── tests/               # Test files
├── docker-compose.yml   # Service orchestration
├── requirements.txt     # Python dependencies
└── README.md           # Project documentation
```

## 🛠️ How to Contribute

### Types of Contributions

#### 1. Bug Reports
- Use the issue template
- Include steps to reproduce
- Provide system information
- Add screenshots/logs when possible

#### 2. Feature Requests
- Check if similar requests exist
- Explain the use case clearly
- Consider implementation feasibility
- Be open to discussion and feedback

#### 3. Code Contributions
- Fork the repository
- Create a feature branch
- Write clean, documented code
- Add tests for new functionality
- Submit a pull request

#### 4. Documentation
- Fix typos and grammar
- Improve clarity and examples
- Add new guides and tutorials
- Translate documentation

#### 5. Testing
- Write unit tests
- Perform integration testing
- Report performance issues
- Suggest test improvements

## 📝 Coding Standards

### Python Style Guide
We follow PEP 8 with some additional conventions:

```python
# Good example
def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two text documents.

    Args:
        text1 (str): First text document
        text2 (str): Second text document

    Returns:
        float: Similarity score between 0 and 1
    """
    # Implementation here
    pass

class DocumentProcessor:
    """Process and analyze text documents."""

    def __init__(self, model_name: str = "default"):
        self.model_name = model_name
        self.initialized = False

    def process_document(self, document_path: str) -> dict:
        """Process a document and return analysis results."""
        # Implementation here
        pass
```

### Naming Conventions
- Use `snake_case` for functions and variables
- Use `PascalCase` for classes
- Use `UPPER_CASE` for constants
- Be descriptive but concise

### Error Handling
```python
# Good error handling
import logging

logger = logging.getLogger(__name__)

def risky_operation(data: dict) -> dict:
    try:
        # Main operation
        result = process_data(data)
        return result
    except ValueError as e:
        logger.error(f"Invalid data format: {e}")
        raise HTTPException(status_code=400, detail="Invalid data format")
    except Exception as e:
        logger.error(f"Unexpected error in risky_operation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

## 🧪 Testing

### Test Structure
```
tests/
├── unit/
│   ├── test_agent.py
│   ├── test_ingest.py
│   └── test_utils.py
├── integration/
│   ├── test_endpoints.py
│   └── test_workflows.py
└── conftest.py
```

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_agent.py

# Run with coverage
pytest --cov=services

# Run integration tests
pytest tests/integration/
```

### Writing Tests
```python
import pytest
from services.agent.app import get_ai_response

def test_get_ai_response_basic():
    """Test basic AI response functionality."""
    response = get_ai_response("Hello", "")
    assert isinstance(response, str)
    assert len(response) > 0

def test_get_ai_response_with_context():
    """Test AI response with context."""
    context = "User has 5 years of Python experience"
    response = get_ai_response("What is your Python experience?", context)
    assert "Python" in response
```

## 📚 Documentation

### Inline Documentation
- Document all public functions and classes
- Use Google-style docstrings
- Include type hints
- Explain complex logic

### README Updates
- Keep README.md current with changes
- Update installation instructions
- Add new features to usage examples
- Maintain troubleshooting section

### API Documentation
- Use FastAPI's automatic documentation
- Provide clear endpoint descriptions
- Include example requests/responses
- Document error responses

## 🔄 Pull Request Process

### Before Submitting
1. **Update Documentation**: Ensure all changes are documented
2. **Write Tests**: Add tests for new functionality
3. **Follow Style Guide**: Adhere to coding standards
4. **Test Thoroughly**: Run all relevant tests
5. **Check Compatibility**: Ensure backward compatibility

### Pull Request Guidelines
- Use clear, descriptive titles
- Include detailed description of changes
- Reference related issues
- Keep PRs focused on single changes
- Request reviews from relevant maintainers

### PR Template
```markdown
## Description
Brief description of what this PR accomplishes.

## Related Issue
Fixes #123 or Related to #456

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Performance improvement

## How Has This Been Tested?
- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing
- [ ] No tests needed

## Checklist
- [ ] My code follows the style guidelines
- [ ] I have performed a self-review
- [ ] I have commented my code
- [ ] I have made corresponding changes to documentation
- [ ] My changes generate no new warnings
```

## 🌟 Community

### Communication Channels
- **GitHub Issues**: Bug reports and feature requests
- **Discord/Slack**: Real-time discussion (link in README)
- **Monthly Meetings**: Community sync-ups
- **Twitter**: Announcements and updates

### Recognition
We recognize contributors through:
- GitHub contributor list
- Release notes mentions
- Community spotlight
- Swag for significant contributions

### Mentorship
- Pair programming sessions available
- Code review guidance
- Architecture discussions
- Career development advice

## 🎯 Development Roadmap

Check [FUTURE_ENHANCEMENTS.md](FUTURE_ENHANCEMENTS.md) for upcoming features and priorities.

## 📞 Questions?

If you have questions about contributing:
1. Check existing documentation
2. Search GitHub issues
3. Join community discussions
4. Email maintainers directly

Thank you for contributing to PAT! Your efforts help make interview preparation more accessible to everyone. 🚀