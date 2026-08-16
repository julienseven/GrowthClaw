# Contributing to $GROWTH

Thank you for your interest in contributing to $GROWTH: The Autonomous Marketing Growth Hacker! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, inclusive, and professional. All contributors are expected to uphold the highest standards of conduct.

## Getting Started

1. **Fork the Repository**: Click "Fork" on the GitHub repository
2. **Clone Your Fork**: `git clone https://github.com/your-username/growth.git`
3. **Create a Branch**: `git checkout -b feature/your-feature-name`
4. **Follow Development Guide**: See [DEVELOPMENT.md](./DEVELOPMENT.md)

## Development Workflow

### Before Starting
1. Check existing issues and PRs to avoid duplicate work
2. Create an issue for major features
3. Discuss approach before implementing

### While Developing
1. Write clean, well-documented code
2. Add tests for new functionality
3. Follow code style guidelines
4. Commit with clear messages
5. Keep commits atomic and focused

### Code Style

#### Python (Backend)
```bash
# Format with Black
black backend/

# Check with Flake8
flake8 backend/

# Sort imports
isort backend/
```

#### TypeScript/JavaScript (Frontend)
```bash
# Format with Prettier
npm run format

# Lint with ESLint
npm run lint -- --fix
```

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that don't affect code meaning
- `refactor`: Code change without feature/bug changes
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `ci`: CI/CD configuration changes

**Examples:**
```
feat(market): Add market sentiment analysis endpoint

fix(solana): Resolve RPC timeout handling

docs(deployment): Update production deployment guide
```

### Testing

#### Backend Tests
```bash
cd backend
pip install pytest pytest-asyncio
pytest tests/
```

#### Frontend Tests
```bash
npm test
```

Ensure tests pass before submitting PR.

## Pull Request Process

1. **Update Docs**: Update README.md, ARCHITECTURE.md if needed
2. **Run Tests**: All tests must pass
3. **Format Code**: Run linters and formatters
4. **Descriptive Title**: Use clear, descriptive PR title
5. **Description**: Explain changes, why, and testing approach
6. **Link Issues**: Reference any related issues with `Closes #123`

### PR Template
```markdown
## Description
Describe your changes here.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update

## Testing
Describe the tests you ran and how to reproduce them.

## Checklist
- [ ] My code follows the code style of this project
- [ ] I have updated the documentation accordingly
- [ ] I have added tests to cover my changes
- [ ] All new and existing tests passed
- [ ] I have not increased complexity without good reason
```

## Areas for Contribution

### High Priority
- [ ] Solana blockchain integrations (solders/solana-py)
- [ ] OpenAI API implementations
- [ ] Market data collection and analysis
- [ ] Strategy execution mechanisms

### Medium Priority
- [ ] UI/UX improvements
- [ ] Performance optimizations
- [ ] Documentation enhancements
- [ ] Test coverage expansion

### Community Contributions
- [ ] Bug reports and fixes
- [ ] Feature suggestions
- [ ] Documentation improvements
- [ ] Translation support

## Reporting Bugs

Use the issue tracker with the following information:
1. **Title**: Brief description of the bug
2. **Environment**: OS, Node/Python versions, etc.
3. **Steps to Reproduce**: Clear step-by-step instructions
4. **Expected vs Actual**: What should happen vs what happens
5. **Logs/Screenshots**: Any relevant error messages or screenshots

## Feature Requests

When proposing new features:
1. **Title**: Brief description
2. **Motivation**: Why this feature is needed
3. **Proposed Solution**: How you envision it working
4. **Alternatives**: Other approaches considered
5. **Context**: Any relevant background

## Questions & Discussions

- Use GitHub Discussions for questions
- Check existing discussions before posting
- Be specific and provide context

## Documentation

### Code Comments
```python
# Good
def calculate_growth_score(data: dict) -> float:
    """
    Calculate growth score based on market metrics.
    
    Args:
        data: Dictionary with market metrics
        
    Returns:
        Growth score between 0 and 100
        
    Raises:
        ValueError: If data is missing required fields
    """
    pass

# Bad
def calc_score(d):
    # calculate score
    pass
```

### README Updates
- Keep README.md up to date
- Document new features
- Provide clear examples
- Fix outdated information

## Release Process

1. Update version in package.json and backend
2. Update CHANGELOG.md
3. Create release notes
4. Tag release: `git tag v0.1.0`
5. Push tag: `git push origin v0.1.0`

## Development Tips

### Backend Debugging
```python
import logging
logger = logging.getLogger(__name__)
logger.debug("Debug message")
```

### Frontend Debugging
```typescript
console.log("Debug:", value);
debugger; // Browser will pause here
```

### Performance Tips
- Use async/await properly in Python
- Memoize expensive computations in React
- Cache API responses in Redis
- Use lazy loading for components

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Python asyncio](https://docs.python.org/3/library/asyncio.html)
- [React Best Practices](https://react.dev/learn)
- [Solana Docs](https://docs.solana.com/)

## Support

- **Questions**: Create a GitHub Discussion
- **Bugs**: Open an issue with reproduction steps
- **Security**: Email security@growth.example.com (do not use issues)

## Recognition

Contributors will be recognized in:
- README.md acknowledgments
- Release notes
- GitHub contributors page

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

**Thank you for contributing to $GROWTH! Together we're building the future of autonomous marketing on Solana.** 🚀

Questions? Open a GitHub Discussion or reach out to the team.
