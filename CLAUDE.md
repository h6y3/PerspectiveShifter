# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

**Local Development Setup:**
```bash
# Install dependencies (UV recommended)
uv sync

# Alternative with pip
pip install -r requirements.txt

# Run development server
uv run python main.py

# Run with Flask directly
uv run flask run --debug
```

**Database Operations:**
```bash
# Reset local database (development only)
rm instance/perspective_shift.db
python main.py  # Auto-creates tables
```

**Testing and Debugging:**
```bash
# Test OpenAI service integration (local development)
python3 -c "from openai_service import get_wisdom_quotes; print(get_wisdom_quotes('feeling stressed'))"

# PRODUCTION DEPLOYMENT VERIFICATION (CRITICAL - run after every deploy)
python3 scripts/tests/deployment/production_health_check.py

# Run complete test suite (unit, integration, deployment, performance)
python3 scripts/tests/run_tests.py

# Test specific deployed endpoints manually
python3 -c "import urllib.request; import json; response = urllib.request.urlopen('https://theperspectiveshift.vercel.app/health'); print(json.loads(response.read().decode()))"

# Test API v1 endpoints (after fixing deployment issues)
python3 -c "import urllib.request; response = urllib.request.urlopen('https://theperspectiveshift.vercel.app/api/v1/health'); print(response.status)"

# Check deployed font loading (for troubleshooting image generation)
curl https://theperspectiveshift.vercel.app/debug_files

# Troubleshoot deployment failures
vercel logs https://theperspectiveshift.vercel.app
```

**Network Access Notes:**
- Claude Code CAN make HTTP requests using urllib (built-in)
- Claude Code CANNOT use requests library (not installed)
- Use urllib.request for testing deployed endpoints
- Can verify deployment success and API functionality remotely

## Architecture Overview

**PerspectiveShifter** is a Flask-based web application that generates personalized wisdom quotes using OpenAI's GPT-4o-mini model. The app is designed as a stateless, anonymous service optimized for Vercel's serverless deployment.

### Key Architectural Principles

- **100% Python Stack:** Uses PIL/Pillow for image generation instead of Node.js dependencies
- **Stateless & Anonymous:** No user accounts, sessions, or personal data storage
- **Graceful Degradation:** Fallback quotes when AI service is unavailable
- **Intelligent Caching:** SHA256-based input hashing for quote deduplication without privacy concerns

### Core Components

**Flask Application (`api/index.py`):**
- Application factory pattern for Vercel compatibility
- Auto-database initialization with fallback handling
- ProxyFix configuration for proper HTTPS URLs in production

**Route Handlers (`routes.py`):**
- Main `/shift` endpoint processes user input and returns personalized quotes
- `/share/<quote_id>` generates shareable quote images
- Comprehensive error handling with user-friendly fallbacks

**AI Service (`openai_service.py`):**
- JSON-structured prompts for reliable GPT-4o-mini responses
- Validates all required fields (quote, attribution, perspective, context)
- High-quality fallback quotes when OpenAI API is unavailable

**Image Generation (`image_generator.py`):**
- Pure Python PIL/Pillow implementation (no Node.js dependencies)
- Multiple design templates controlled by `design` parameter
- Robust font fallback system for deployment environments
- 1080x1080 format optimized for social media sharing

**Database Models (`models.py`):**
- `QuoteCache`: Stores generated quotes with input hash for deduplication
- `DailyStats`: Anonymous usage analytics without personal identifiers

### Environment Configuration

Required environment variables:
```env
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=sqlite:///perspective_shift.db  # Local dev
DATABASE_URL=postgresql://...  # Production
SESSION_SECRET=your_secret_key_here
FLASK_ENV=development
FLASK_PORT=5001
```

### Deployment Architecture

**Vercel Configuration (`vercel.json`):**
- Uses `@vercel/python` exclusively (no Node.js build phase)
- Static file serving for CSS, JS, fonts, and images
- Route rewrites with static routes prioritized before Flask catch-all

**CRITICAL: Vercel Configuration Rules (Learned 2025-06-08):**
- **CANNOT use both `builds` and `functions`** - Vercel will reject deployment
- **Use `functions` only** for modern Vercel deployments
- **Pattern matching** in functions config applies to multiple endpoints
- **maxDuration** can be set per function pattern (30s for API, 60s for MCP)
- **Route rewrites** must map sources to specific .py files

**Correct vercel.json structure:**
```json
{
  "version": 2,
  "functions": {
    "api/*.py": {"runtime": "@vercel/python", "maxDuration": 30},
    "api/v1/*.py": {"runtime": "@vercel/python", "maxDuration": 30},
    "api/mcp/*.py": {"runtime": "@vercel/python", "maxDuration": 60}
  },
  "rewrites": [
    {"source": "/api/v1/quotes", "destination": "/api/v1/quotes.py"},
    {"source": "/api/mcp/server", "destination": "/api/mcp/server.py"}
  ]
}
```

**Deployment Methods:**

**Option 1: Git-based Deployment (Automatic)**
```bash
# Commit changes and push to main branch
git add .
git commit -m "your commit message"
git push origin main
# Vercel automatically deploys from main branch
```

**Option 2: Direct CLI Deployment (Manual)**
```bash
# Preview deployment (feature branch)
vercel --prod=false --yes

# Production deployment  
vercel --prod --yes

# Check deployment status
vercel ls

# Comprehensive deployment verification (CRITICAL)
python3 scripts/tests/deployment/production_health_check.py

# Check deployment logs for troubleshooting
vercel logs https://theperspectiveshift.vercel.app
```

**Database Strategy:**
- Development: SQLite with local file storage
- Production: PostgreSQL (Vercel Postgres recommended)
- Auto-migration on application startup

## Vercel Python Serverless Functions (CRITICAL KNOWLEDGE - 2025-06-08)

**LESSON LEARNED**: Our initial Flask-based API implementation failed in production. Vercel Python functions require a specific pattern that differs from standard Flask applications.

### Required Serverless Function Pattern

**Correct Pattern (✅):**
```python
from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):  # Must be lowercase 'handler'
    def do_GET(self):
        """Handle GET requests"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response_data = {"status": "ok", "message": "Hello from API"}
        self.wfile.write(json.dumps(response_data).encode())
    
    def do_POST(self):
        """Handle POST requests"""
        content_length = int(self.headers.get('content-length', 0))
        post_data = self.rfile.read(content_length)
        request_data = json.loads(post_data.decode('utf-8'))
        
        # Process request...
        response_data = {"received": request_data}
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode())
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
```

**Incorrect Pattern (❌) - DO NOT USE:**
```python
# This Flask pattern DOES NOT WORK in Vercel serverless functions
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/endpoint')
def endpoint():
    return jsonify({"status": "ok"})

def handler(request):
    return app.full_dispatch_request()  # This fails!
```

### Key Requirements for Vercel Python Functions

1. **Handler Class Name**: Must be exactly `handler` (lowercase)
2. **Inheritance**: Must inherit from `BaseHTTPRequestHandler`
3. **HTTP Methods**: Implement `do_GET()`, `do_POST()`, `do_OPTIONS()` as needed
4. **CORS Headers**: Must manually set all CORS headers
5. **Error Handling**: Must handle all exceptions within the class methods
6. **Dependencies**: Keep dependencies minimal - complex imports may fail

### Common Error Patterns and Solutions

**Error: "TypeError: issubclass() arg 1 must be a class"**
- **Cause**: Handler is not properly inheriting from BaseHTTPRequestHandler
- **Solution**: Ensure `class handler(BaseHTTPRequestHandler)` with lowercase 'handler'

**Error: "ImportError" or "ModuleNotFoundError"**
- **Cause**: Complex import paths or custom modules not accessible
- **Solution**: Use simple, self-contained functions with minimal imports

**Error: "Internal Server Error" with no specific message**
- **Cause**: Unhandled exception in handler methods
- **Solution**: Add comprehensive try/catch blocks

### Deployment Verification Process

**Always run after deployment:**
```bash
# 1. Deploy to Vercel
vercel --prod --yes

# 2. Verify deployment health
python3 scripts/tests/deployment/production_health_check.py

# 3. If issues found, check logs
vercel logs https://theperspectiveshift.vercel.app

# 4. Test specific endpoints manually
python3 -c "import urllib.request; print(urllib.request.urlopen('https://theperspectiveshift.vercel.app/api/v1/health').read().decode())"
```

### Debugging Failed Deployments

1. **Check Runtime Logs**: `vercel logs <deployment-url>`
2. **Check Build Logs**: `vercel inspect --logs <deployment-id>`
3. **Verify Handler Pattern**: Ensure BaseHTTPRequestHandler inheritance
4. **Test Locally**: Use simple HTTP server for testing before deployment
5. **Simplify Dependencies**: Remove complex imports if possible

### Key Integration Points

**OpenAI API:**
- Model: `gpt-4o-mini` (most cost-effective for quote generation)
- Response format: JSON with quote, attribution, perspective, context fields
- Temperature: 0.7 for balanced creativity and consistency

**Image Generation:**
- Space Mono font for distinctive typography
- Font loading handles both local development and Vercel deployment paths
- Supports multiple design styles via template system

### Frontend Architecture

**Templates:**
- `base.html`: Social meta tags and responsive layout foundation
- `index.html`: Main UI with form, results display, and sharing functionality

**Static Assets:**
- Modern Apple-inspired design system in `static/css/style.css`
- Enhanced JavaScript with dark mode, animations, and copy functionality
- Space Mono fonts for consistent typography across web and images

### Development Workflow Notes

- **Single Technology Focus:** Avoid introducing Node.js dependencies
- **Privacy-First Design:** Never store personal data or implement user tracking
- **Serverless Optimization:** Minimize cold start overhead in all code paths
- **Error Resilience:** Every external integration has fallback mechanisms
- **Deployment Verification:** ALWAYS run health check after deployment
- **Vercel Function Pattern:** Use BaseHTTPRequestHandler, not Flask, for API endpoints

## Deployment Troubleshooting Guide (2025-06-08)

**Common Issues and Solutions:**

### Issue: API endpoints returning 500 errors
**Symptoms:** `HTTP 500: Internal Server Error` on `/api/v1/*` endpoints
**Root Cause:** Incorrect Vercel Python function pattern
**Solution:** 
1. Check handler class inherits from `BaseHTTPRequestHandler`
2. Ensure class name is exactly `handler` (lowercase)
3. Verify no complex imports or Flask usage
4. Check logs: `vercel logs <deployment-url>`

### Issue: Import errors in serverless functions
**Symptoms:** `ModuleNotFoundError` or `ImportError` in logs
**Root Cause:** Complex import paths don't work in Vercel environment
**Solution:**
1. Simplify imports to built-in modules only
2. Avoid custom `lib/` module imports in serverless functions
3. Use self-contained function implementations

### Issue: Deployment appears successful but endpoints fail
**Symptoms:** `vercel --prod` succeeds but health check fails
**Root Cause:** Build success ≠ runtime success
**Solution:**
1. Always run `python3 scripts/tests/deployment/production_health_check.py` after deployment
2. Check runtime logs: `vercel logs <url>`
3. Test critical endpoints manually

### Issue: CORS errors in browser
**Symptoms:** Browser blocks API requests due to CORS policy
**Root Cause:** Missing CORS headers in serverless functions
**Solution:** Add these headers to all responses:
```python
self.send_header('Access-Control-Allow-Origin', '*')
self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
self.send_header('Access-Control-Allow-Headers', 'Content-Type')
```

**Debugging Workflow:**
1. Deploy: `vercel --prod --yes`
2. Verify: `python3 scripts/tests/deployment/production_health_check.py`
3. If failures: `vercel logs <deployment-url>`
4. Fix issues and redeploy
5. Re-verify until health check passes

## MCP and REST API Architecture (2025-06-08)

**PerspectiveShifter** now includes comprehensive API capabilities enabling Claude Desktop integration and future mobile app development through a strangler pattern migration.

### API Architecture Overview

**Strangler Pattern Implementation:**
- **Phase 1**: New `WisdomService` wraps legacy `openai_service.py` 
- **Phase 2**: REST API v1 endpoints using new service layer
- **Phase 3**: MCP server for Claude Desktop integration
- **Legacy Compatibility**: Web application continues using existing routes during migration

**Service Layer (`lib/api/`):**
- `wisdom_service.py`: Core quote generation with rate limiting integration
- `rate_limiter.py`: Budget-based quota management ($1/day OpenAI budget)
- `response_formatter.py`: Multi-format responses (API, MCP, Web)

**REST API Endpoints (`api/v1/`) - IMPLEMENTED:**
- `POST /api/v1/quotes`: Generate wisdom quotes with validation ✅
- `GET /api/v1/quotes/{id}`: Retrieve cached quotes ✅
- `GET /api/v1/images/{id}`: Generate quote images (redirects to existing endpoint) ✅
- `GET /api/v1/health`: System health and quota monitoring ✅
- `GET /api/v1/stats`: Anonymous usage statistics ✅

**Implementation Status (2025-06-08):**
- **Working**: All API v1 endpoints return 200 OK responses
- **Pattern**: Using BaseHTTPRequestHandler (not Flask) for Vercel compatibility
- **Integration**: Basic responses implemented; full service layer integration pending
- **Testing**: Comprehensive health check script validates all endpoints

**MCP Integration (`api/mcp/`):**
- `POST /api/mcp/server`: JSON-RPC 2.0 endpoint for Claude Desktop
- `GET /api/mcp/info`: Server capabilities and tool listing
- `GET /api/mcp/config`: Claude Desktop configuration generator

### Rate Limiting Strategy

**Multi-Tier Protection:**
- **Global Budget**: $1/day OpenAI spending limit (≈2,200 quotes)
- **Per-IP Limits**: 50 quotes/hour per IP address
- **Burst Protection**: 1-5 quotes/minute per IP
- **AI Agent Detection**: 2x higher limits for Claude Desktop (User-Agent based)

**Environment Variables:**
```env
API_DAILY_BUDGET_USD=1.00
API_RATE_LIMIT_ENABLED=true
API_MAX_QUOTES_PER_IP_HOUR=50
```

### MCP Tools for Claude Desktop

**Available Tools:**
1. `generate_wisdom_quote`: Create personalized quotes with style preferences
2. `create_quote_image`: Generate shareable images for quotes
3. `get_wisdom_quote`: Retrieve quotes by ID
4. `get_system_status`: Check service health and quota status

**Claude Desktop Setup:**
1. Get configuration from `/api/mcp/config`
2. Add to Claude Desktop MCP settings
3. Restart Claude Desktop
4. Tools appear automatically in conversations

## Script Organization Rules

**Directory Structure:**
```
scripts/
├── tests/          # Core test suite - runs on every deploy
├── dev-tools/      # Developer productivity tools (ongoing use)
├── maintenance/    # Production maintenance scripts (must be credential-free)
└── temp/           # Local experiments (.gitignore'd, never committed)
```

**Script Placement Guidelines:**

**scripts/tests/** - Comprehensive test suite organized by category:

**Test Suite Structure:**
```
scripts/tests/
├── run_tests.py              # Main test runner (run all tests)
├── unit/                     # Unit tests for individual components
│   ├── test_wisdom_service.py
│   ├── test_rate_limiter.py
│   └── test_response_formatter.py
├── integration/              # Integration and API tests
│   ├── test_quotes_api.py
│   ├── test_mcp_integration.py
│   ├── test_sharing_api.py
│   └── validate_sharing_platforms.py
├── deployment/               # Production deployment verification
│   └── production_health_check.py
└── performance/              # Performance and load tests
    └── performance_test_sharing.py
```

**Running Tests:**
```bash
# Run complete test suite
python3 scripts/tests/run_tests.py

# Run specific test categories
python3 scripts/tests/unit/test_wisdom_service.py
python3 scripts/tests/deployment/production_health_check.py

# CRITICAL: Always run after deployment
python3 scripts/tests/deployment/production_health_check.py
```

**Test Categories:**
- **Unit Tests**: Core service logic, data validation, utility functions
- **Integration Tests**: API endpoints, database operations, external services
- **Deployment Tests**: Production health, environment validation, configuration
- **Performance Tests**: Load testing, response times, resource usage

**scripts/dev-tools/** - Developer productivity tools:
- Performance testing utilities
- Quick status checks for development
- Debugging helpers and diagnostics
- Tools for ongoing development workflow

**scripts/maintenance/** - Production maintenance:
- Database migration scripts
- Production health monitoring
- Deployment utilities
- Must NEVER contain hardcoded credentials (use environment variables)

**scripts/temp/** - Temporary experiments (gitignored):
- One-time verification scripts
- Ad-hoc testing and debugging
- Feature exploration and prototyping
- Anything that doesn't provide ongoing value

**Key Rules:**
1. **Core test suite priority**: If a script could be part of automated testing, place in `scripts/tests/`
2. **Developer productivity**: Ongoing useful tools go in `scripts/dev-tools/`
3. **Zero credentials**: Production scripts must use environment variables only
4. **Temporary = temp/**: One-time scripts go in `scripts/temp/` (never committed)
5. **Clean up regularly**: Remove outdated scripts to prevent feature drift

## Documentation Organization Standards

### Directory Structure and Naming Conventions

```
docs/
├── specs/                           # Feature specifications (permanent)
│   └── YYYY-MM-DD-feature-name.md
├── runbooks/                        # Operational procedures (permanent)
│   ├── development.md              # Development procedures and commands
│   ├── deployment.md               # Vercel deployment procedures
│   └── testing.md                  # Testing standards and procedures
├── temp/                           # Ephemeral documentation (gitignored)
│   └── YYYY-MM-DD-description.md
└── archive/                        # Deprecated docs (moved, not deleted)
    └── deprecated-YYYY-MM-DD-original-name.md

Root level:
├── README.md                 # Project overview and setup
├── CLAUDE.md                # Development guidance (this file)
└── CLAUDE.local.md          # Local development preferences
```

### File Naming Standards

**Specifications (docs/specs/):**
- Format: `YYYY-MM-DD-feature-name.md`
- Example: `2025-06-08-social-media-sharing-strategy.md`
- Use kebab-case for feature names
- Include comprehensive implementation details
- Permanent record of architectural decisions

**Runbooks (docs/runbooks/):**
- Format: `category.md`
- Examples: `development.md`, `deployment.md`, `testing.md`
- Use kebab-case for descriptive names
- Operational procedures and standards
- Living documents that stay current with project evolution

**Work Logs (if absolutely necessary):**
- Format: `YYYY-MM-DD-feature-name_work_log.md`
- Example: `2025-06-08-mcp-rest-api-integration_work_log.md`
- Use EXACT same name as parent spec with `_work_log.md` suffix
- Should be avoided - prefer updating the main spec document
- Only create if tracking complex implementation details separately

**Ephemeral Documentation (docs/temp/):**
- Format: `YYYY-MM-DD-description.md`
- Example: `2025-06-08-mobile-testing-checklist.md`
- Include "TEMPORARY FILE" header with deletion criteria
- Use descriptive names for development context
- Auto-deleted after development phase

### Documentation Content Guidelines

**Specifications Must Include:**
- Clear feature scope and goals
- Implementation approach and rationale
- API contracts and data models
- Testing and validation criteria
- Rollback and migration considerations

**Permanent Documentation Should:**
- Remain current and actionable
- Include examples and usage patterns
- Reference related specifications
- Provide troubleshooting guidance
- Link to external resources appropriately

**Ephemeral Documentation Rules:**
1. **Mark temporary nature**: Include clear headers indicating temporary status
2. **Define cleanup criteria**: Specify when the document should be deleted
3. **Use for development phases**: Testing plans, investigation notes, temporary procedures
4. **Never commit to main repo**: Always place in gitignored `docs/temp/`
5. **Convert valuable insights**: Promote useful findings to permanent documentation

**Ephemeral Document Retention Criteria:**
- **DELETE if**: Feature-specific testing completed, outdated script references, time-sensitive content
- **RETAIN temporarily if**: Active development phase, pending feature completion
- **PROMOTE to permanent if**: Contains reusable procedures, architectural insights, or standards
- **Default action**: DELETE aggressively - temporary documents should have short lifecycles

**Regular Cleanup Schedule:**
- Review `docs/temp/` after each major feature completion
- Delete documents >30 days old unless actively referenced
- Promote valuable content to appropriate permanent locations
- Goal: Keep `docs/temp/` minimal and current

### Specification Update Process

**CRITICAL: Complete Document Accuracy Check**
When updating specifications during implementation:

1. **Never update parts in isolation** - always review the entire document for accuracy
2. **Check all sections** for consistency with current implementation state
3. **Update status, progress sections, and implementation notes** comprehensively
4. **Verify all code examples** and references are still accurate
5. **Cross-reference related specifications** for consistency

**Common Issues to Avoid:**
- Updating progress section but leaving contradictory statements in earlier sections
- Changing implementation approach without updating risk assessment
- Adding new features without updating success metrics or testing strategy
- Leaving outdated code examples or file references

**Best Practice:** Read through the entire specification after any updates to ensure the document tells a coherent, accurate story of the current state.

### Issue Documentation Requirements

**When Features Are Complete:**
When completing any feature implementation, ALWAYS:

1. **Document discovered issues immediately** - create separate specs for problems found during implementation
2. **Example pattern:** After completing MCP integration, production health check revealed 5 failing tests
3. **Action required:** Create `2025-06-09-production-stability-fixes.md` to document and plan fixes
4. **Don't leave issues undocumented** - we will lose track and re-learn the same problems later

**Issue Specification Standards:**
- Use date format: `YYYY-MM-DD-issue-description.md`
- Include root cause analysis and proposed solutions
- Document impact assessment and implementation timeline
- Reference the completed feature that revealed the issues
- Follow full specification format (not just a bug list)

**Benefits:**
- Issues become trackable features rather than forgotten problems
- Implementation approach is documented and reviewed
- Progress can be measured and validated
- Prevents repeated discovery of the same issues

## Root Directory Hygiene

**Keep Root Clean**: The project root should only contain:
- **Core application files**: Main Flask app files (routes.py, models.py, openai_service.py, etc.)
- **Configuration files**: requirements.txt, vercel.json, .gitignore, etc.
- **Essential documentation**: README.md, DEPLOYMENT.md, CLAUDE.md, CLAUDE.local.md

**Never Leave in Root:**
- Debug scripts (debug-*.py, test-*.py, scratch-*.py)
- Temporary test files or experimental code
- One-off investigation scripts
- Development artifacts

**Root Cleanup Rule**: Any debug, test, or temporary .py files in root should be moved to `scripts/temp/` immediately. The root directory represents the professional face of the project.