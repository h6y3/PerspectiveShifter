# Testing Standards for PerspectiveShifter
**PERMANENT DOCUMENTATION** - Should be committed to repo

## Overview

This document establishes testing standards and practices for PerspectiveShifter, including test organization, script conventions, and testing workflows. These standards ensure consistent, maintainable, and effective testing across all features.

## File Organization

### Directory Structure
```
/scripts/                     # Permanent testing and utility scripts
  ├── tests/                  # Organized test suite
  │   ├── run_tests.py        # Main test runner
  │   ├── unit/               # Unit tests for individual components
  │   ├── integration/        # API and integration tests
  │   ├── deployment/         # Production deployment verification
  │   └── performance/        # Performance and load tests
  ├── maintenance/            # Database migration and maintenance scripts
  └── dev-tools/              # Developer productivity tools

/docs/                        # Permanent documentation
  ├── testing-standards.md    # This file
  └── specs/                  # Feature specifications

/test-*.md                    # Temporary testing files (delete after testing)
/test-*.py                    # Temporary testing scripts (delete after testing)
```

### Script Categories

#### 1. Permanent Scripts (`/scripts/`)
**Purpose**: Scripts that should be committed to the repository for ongoing use.

**Naming Convention**: `{category}_{feature}_{type}.py`
- Examples: `test_sharing_api.py`, `validate_sharing_platforms.py`, `migrate_sharing.py`

**Requirements**:
- Include comprehensive docstring with usage examples
- Support command-line arguments with `--help`
- Follow error handling standards (see below)
- Include version/date information in header comment

#### 2. Temporary Scripts (`/test-*.py`)
**Purpose**: One-time testing scripts for specific features or debugging.

**Naming Convention**: `test-{feature}-{purpose}.py`
- Examples: `test-sharing-integration.py`, `test-mobile-responsiveness.py`

**Requirements**:
- Must include "TEMPORARY SCRIPT" in header comment
- Should be deleted after successful testing/deployment
- Can be less formal but still include basic error handling

## Script Standards

### Python Script Template
```python
#!/usr/bin/env python3
"""
{Script Purpose} - One line description
PERMANENT SCRIPT - Should be committed to repo
OR
TEMPORARY SCRIPT - Delete after testing

Detailed description of what this script does.

Usage:
    python scripts/{script_name}.py
    python scripts/{script_name}.py --arg value
    
Dependencies:
    - requests>=2.32.0
    - (other requirements)

Author: PerspectiveShifter Team
Created: YYYY-MM-DD
Last Modified: YYYY-MM-DD
"""

import sys
import os
import argparse
import logging

# Configuration
DEFAULT_CONFIG = "default_value"
TIMEOUT = 30

def main():
    parser = argparse.ArgumentParser(description='Script description')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    try:
        # Main script logic here
        result = do_main_work()
        
        if result:
            print("✅ Script completed successfully")
            sys.exit(0)
        else:
            print("❌ Script completed with errors")
            sys.exit(1)
            
    except Exception as e:
        logging.error(f"Script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Error Handling Standards

#### 1. Exit Codes
- `0`: Success
- `1`: General error
- `2`: Invalid arguments
- `3`: Network/connectivity error
- `4`: Database error

#### 2. Logging Levels
- `DEBUG`: Detailed tracing for debugging
- `INFO`: General information and progress
- `WARNING`: Unexpected but recoverable issues
- `ERROR`: Errors that cause script failure

#### 3. Exception Handling
```python
try:
    risky_operation()
except requests.exceptions.RequestException as e:
    logging.error(f"Network error: {e}")
    sys.exit(3)
except DatabaseError as e:
    logging.error(f"Database error: {e}")
    sys.exit(4)
except Exception as e:
    logging.error(f"Unexpected error: {e}")
    sys.exit(1)
```

## Testing Types and Standards

### 1. Unit Testing
**Status**: Not yet implemented (Python project without formal test framework)

**Future Implementation**:
- Use `pytest` for Python unit tests
- Test individual functions and classes
- 80%+ code coverage target
- Fast execution (< 1 second per test)

### 2. Integration Testing
**Current Implementation**: Manual and scripted API testing

**Standards**:
- Test complete workflows (quote generation → sharing → tracking)
- Use real database connections but isolated test data
- Validate all API endpoints return expected formats
- Test error conditions and edge cases

**Example**: `scripts/tests/integration/test_quotes_api.py`

### 3. Performance Testing
**Current Implementation**: Load testing with response time monitoring

**Standards**:
- Test under realistic load conditions
- Monitor response times, throughput, and error rates
- Validate Vercel serverless function limits (60s timeout, memory usage)
- Test concurrent access patterns

**Example**: `scripts/tests/performance/test_performance_sharing.py`

### 4. Platform Validation Testing
**Current Implementation**: Cross-platform sharing validation

**Standards**:
- Validate Open Graph meta tags across platforms
- Test sharing URLs work in social media platforms
- Verify image generation works correctly
- Check mobile browser compatibility

**Example**: `scripts/tests/integration/validate_sharing_platforms.py`

### 5. Manual Testing
**Current Implementation**: Comprehensive checklists and test plans

**Standards**:
- Use structured checklists for all manual testing
- Document test results and issues found
- Include cross-browser and cross-device testing
- Test user workflows end-to-end

**Examples**: 
- `test-sharing-manual-checklist.md` (temporary)
- `test-mobile-responsiveness-plan.md` (temporary)

## Development Workflow

### Pre-Deployment Testing

#### 1. Local Development Testing
```bash
# Install dependencies
uv sync  # or pip install -r requirements.txt

# Run database migrations
python scripts/maintenance/migrate_sharing.py

# Start development server
FLASK_ENV=development flask run --port 5001

# Run all tests
python scripts/tests/run_tests.py

# Run specific API tests
python scripts/tests/integration/test_quotes_api.py --base-url http://localhost:5001

# Run performance tests
python scripts/tests/performance/test_performance_sharing.py --url http://localhost:5001
```

#### 2. Staging Deployment Testing
```bash
# Deploy to staging
vercel --prod

# Validate deployment
python scripts/tests/integration/validate_sharing_platforms.py --url https://your-app.vercel.app

# Run performance tests on staging
python scripts/tests/performance/test_performance_sharing.py --url https://your-app.vercel.app
```

#### 3. Production Deployment Testing
```bash
# After production deployment
python scripts/tests/integration/validate_sharing_platforms.py --url https://theperspectiveshift.vercel.app

# Monitor performance
python scripts/tests/performance/test_performance_sharing.py --url https://theperspectiveshift.vercel.app --iterations 5
```

### Continuous Integration (Future)

When CI/CD is implemented, include these checks:

```yaml
# Example GitHub Actions workflow
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.13'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install requests  # For testing scripts
      
      - name: Run test suite
        run: python scripts/tests/run_tests.py
      
      - name: Run API tests
        run: python scripts/tests/integration/test_quotes_api.py --base-url ${{ secrets.STAGING_URL }}
      
      - name: Run platform validation
        run: python scripts/tests/integration/validate_sharing_platforms.py --url ${{ secrets.STAGING_URL }}
      
      - name: Performance baseline check
        run: python scripts/tests/performance/test_performance_sharing.py --url ${{ secrets.STAGING_URL }} --iterations 5
```

## Testing Environment Management

### Environment Variables
```bash
# Local testing
export FLASK_ENV=development
export FLASK_PORT=5001
export DATABASE_URL=sqlite:///test_perspective_shift.db

# Staging testing
export TEST_BASE_URL=https://staging-app.vercel.app
export OPENAI_API_KEY=your_test_key

# Production testing
export PROD_BASE_URL=https://theperspectiveshift.vercel.app
```

### Test Data Management

#### Database Testing
- Use separate test database for automated tests
- Reset test data between test runs
- Use realistic but anonymized test data
- Don't test against production database

#### API Testing
- Use consistent test inputs for reproducible results
- Test with both valid and invalid data
- Include edge cases (empty strings, special characters, very long inputs)
- Respect rate limits in automated tests

## Documentation Standards

### Test Documentation Requirements

1. **Test Plans** (for major features)
   - Objective and scope
   - Test environment setup
   - Detailed test cases
   - Expected results
   - Risk assessment

2. **Test Scripts** (all automated scripts)
   - Purpose and usage instructions
   - Dependencies and setup
   - Command-line interface documentation
   - Example outputs

3. **Test Results** (for formal testing cycles)
   - Test execution summary
   - Issues found and their status
   - Performance metrics
   - Recommendations

### Documentation Location
- **Permanent docs**: `/docs/runbooks/` directory
- **Specifications**: `/docs/specs/` directory
- **Temporary docs**: `/docs/temp/` directory (gitignored)

## Quality Gates

### Before Feature Development
- [ ] Test plan created and reviewed
- [ ] Test environment prepared
- [ ] Testing scripts planned

### Before Code Commit
- [ ] Manual testing completed
- [ ] Automated tests pass locally
- [ ] Performance acceptable locally

### Before Deployment
- [ ] All tests pass on staging
- [ ] Performance meets benchmarks
- [ ] Cross-browser testing completed
- [ ] Mobile testing completed

### After Deployment
- [ ] Production validation tests pass
- [ ] Performance monitoring in place
- [ ] Error monitoring active
- [ ] User feedback collection ready

## Tool Recommendations

### Required Tools
- **Python 3.13+**: For all testing scripts
- **uv or pip**: Dependency management
- **requests**: HTTP testing library
- **Chrome DevTools**: Frontend debugging and testing
- **Vercel CLI**: Deployment testing

### Recommended Tools
- **pytest**: For future unit testing implementation
- **locust**: For load testing (alternative to custom performance scripts)
- **selenium**: For browser automation testing (if needed)
- **browserstack**: For cross-device testing (paid service)

### Testing Services
- **Facebook Sharing Debugger**: Open Graph validation
- **Twitter Card Validator**: Twitter card testing
- **LinkedIn Post Inspector**: LinkedIn sharing validation
- **Google PageSpeed Insights**: Performance monitoring

## Maintenance and Updates

### Monthly Tasks
- [ ] Review and update test scripts
- [ ] Check for broken external validation URLs
- [ ] Update browser compatibility matrix
- [ ] Review performance benchmarks

### Quarterly Tasks
- [ ] Evaluate testing tool updates
- [ ] Review and update testing standards
- [ ] Assess test coverage gaps
- [ ] Update documentation

### After Major Updates
- [ ] Update all relevant test scripts
- [ ] Re-run complete test suite
- [ ] Update documentation
- [ ] Review and update standards if needed

---

## Conclusion

These testing standards ensure that PerspectiveShifter maintains high quality while allowing for efficient development and deployment. All team members should follow these standards when creating tests, and the standards should be updated as the project evolves.

For questions about testing standards or to propose changes, create an issue in the project repository with the label "testing".