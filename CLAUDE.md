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
# Test OpenAI service integration
python -c "from openai_service import get_wisdom_quotes; print(get_wisdom_quotes('feeling stressed'))"

# Check deployed font loading (for troubleshooting image generation)
curl https://your-app.vercel.app/debug_files
```

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

**Database Strategy:**
- Development: SQLite with local file storage
- Production: PostgreSQL (Vercel Postgres recommended)
- Auto-migration on application startup

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