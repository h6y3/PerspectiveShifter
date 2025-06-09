# PerspectiveShifter Development Runbook

This document captures institutional knowledge, testing patterns, and operational procedures for the PerspectiveShifter application.

## Table of Contents
- [Quick Reference](#quick-reference)
- [Testing Patterns](#testing-patterns)
- [Debugging Procedures](#debugging-procedures)
- [Deployment Checklist](#deployment-checklist)
- [Common Issues & Solutions](#common-issues--solutions)
- [Monitoring & Alerts](#monitoring--alerts)

## Quick Reference

### Essential Commands
```bash
# Production health check
uv run python scripts/tests/deployment/test_production_health.py

# Local development
uv run python main.py
uv run flask run --debug

# Database migration (production)
OPENAI_API_KEY="dummy" DATABASE_URL="<prod_url>" uv run python scripts/maintenance/migrate_sharing.py

# Run all tests
uv run python scripts/tests/run_tests.py
uv run python test_real_instagram_downloads.py
uv run python test_tracking_fix.py
```

### Key URLs
- **Production**: https://theperspectiveshift.vercel.app
- **Health Check**: https://theperspectiveshift.vercel.app/health
- **Share Stats**: https://theperspectiveshift.vercel.app/share-stats
- **Test Share Page**: https://theperspectiveshift.vercel.app/share/51_0

## Testing Patterns

### Manual Testing Checklist

**Basic Functionality:**
```bash
# Homepage loads
curl -s -o /dev/null -w "%{http_code}" "https://theperspectiveshift.vercel.app/"

# Share page loads  
curl -s -o /dev/null -w "%{http_code}" "https://theperspectiveshift.vercel.app/share/51_0"

# Image generation works
curl -s -o /dev/null -w "%{http_code}" "https://theperspectiveshift.vercel.app/image/51_0?design=3"
```

**Social Media Meta Tags:**
```bash
# Check Open Graph tags
curl -s "https://theperspectiveshift.vercel.app/share/51_0" | grep -E "(og:image|og:title|twitter:image)"

# Validate image URL works
curl -s -I "https://theperspectiveshift.vercel.app/image/51_0?design=3" | grep "content-length"
```

**Share Tracking:**
```bash
# Test valid platforms
curl -X POST "https://theperspectiveshift.vercel.app/track-share/51_0" \
  -H "Content-Type: application/json" \
  -d '{"platform": "instagram"}' -s

# Test invalid platform rejection (should return 400)
curl -X POST "https://theperspectiveshift.vercel.app/track-share/51_0" \
  -H "Content-Type: application/json" \
  -d '{"platform": "invalid"}' -s
```

**Image Consistency (Instagram bug prevention):**
```bash
# All these should return same content-length
curl -s -I "https://theperspectiveshift.vercel.app/image/51_0?design=3" | grep content-length
curl -s -I "$(curl -s 'https://theperspectiveshift.vercel.app/share/51_0' | grep -o 'property="og:image"[^>]*content="[^"]*"' | cut -d'"' -f4)" | grep content-length
```

### Automated Testing Scripts

**Comprehensive Tests:**
- `scripts/tests/deployment/test_production_health.py` - Full production health check  
- `scripts/tests/run_tests.py` - Run complete test suite
- `scripts/tests/integration/test_quotes_api.py` - API endpoint testing
- `scripts/tests/integration/test_mcp_integration.py` - MCP server testing

**Specialized Tests:**
- `scripts/tests/integration/validate_sharing_platforms.py` - Platform-specific validation
- `scripts/tests/performance/test_performance_sharing.py` - Load testing
- `scripts/tests/unit/test_wisdom_service.py` - Unit tests for core services

## Debugging Procedures

### Common Debug Commands

**Check Application Logs:**
```bash
# Vercel deployment logs
vercel logs

# Local Flask debugging
FLASK_ENV=development FLASK_DEBUG=1 uv run python main.py
```

**Database Debugging:**
```bash
# Test database connection
DATABASE_URL="<prod_url>" uv run python -c "from api.index import app, db; app.app_context().push(); print(db.session.execute('SELECT 1').scalar())"

# Check table structure
DATABASE_URL="<prod_url>" uv run python -c "from api.index import app, db; app.app_context().push(); print(db.engine.table_names())"

# Verify ShareStats model
DATABASE_URL="<prod_url>" uv run python -c "from models import ShareStats; from api.index import app; app.app_context().push(); print(ShareStats.get_total_shares())"
```

**URL Construction Debugging:**
```bash
# Test template helpers work
uv run python -c "from utils import get_social_media_image_url; from api.index import app; app.app_context().push(); print(get_social_media_image_url('51_0'))"

# Check JavaScript helpers loaded
curl -s "https://theperspectiveshift.vercel.app/" | grep -A 10 "window.UrlHelpers"
```

### Image Generation Issues

**Font Loading Problems:**
```bash
# Test font availability
curl -s "https://theperspectiveshift.vercel.app/static/fonts/SpaceMono-Bold.ttf" -I

# Debug image generation
uv run python -c "from image_generator import create_share_image_route; print('Image generator loaded')"
```

**Design Parameter Issues:**
```bash
# Test different designs
curl -s -I "https://theperspectiveshift.vercel.app/image/51_0?design=1" | grep content-length
curl -s -I "https://theperspectiveshift.vercel.app/image/51_0?design=3" | grep content-length

# Check for duplicate parameters (bug we fixed)
curl -s "https://theperspectiveshift.vercel.app/share/51_0" | grep -o "design=3" | wc -l
```

## Deployment Checklist

### Pre-Deployment
- [ ] Run production health check locally
- [ ] Execute all test suites
- [ ] Verify database migrations if needed
- [ ] Check environment variables are set

### Deployment Steps
```bash
# 1. Commit and push changes
git add .
git commit -m "feat: describe changes"
git push

# 2. Deploy to production
vercel --prod

# 3. Run post-deployment health check
uv run python scripts/tests/deployment/test_production_health.py

# 4. Verify key functionality manually
curl -s "https://theperspectiveshift.vercel.app/health"
```

### Post-Deployment
- [ ] Monitor error rates for 10 minutes
- [ ] Test social media sharing on actual platforms
- [ ] Verify analytics are collecting data
- [ ] Check performance metrics

## Common Issues & Solutions

### Import Errors
**Symptom:** `ImportError: cannot import name 'ShareStats'`
**Solution:** Database migration needed
```bash
DATABASE_URL="<prod_url>" uv run python scripts/maintenance/migrate_sharing.py
```

### Image Inconsistency
**Symptom:** Different image sizes for view vs download
**Solution:** Check for duplicate design parameters
```bash
# Look for ?design=3?design=3 patterns
curl -s "share_page_url" | grep -o "design=3" | sort | uniq -c
```

### Share Tracking 400 Errors
**Symptom:** Tracking returns 400 Bad Request
**Solution:** Verify platform names are valid
```bash
# Valid platforms: x, linkedin, native, instagram
curl -X POST "track_url" -d '{"platform": "instagram"}' -H "Content-Type: application/json"
```

### Template Errors
**Symptom:** `'moment' is undefined` or similar
**Solution:** Check template context and imports
```bash
# Verify all template variables are passed from routes
grep -r "moment\|undefined_var" templates/
```

## Monitoring & Alerts

### Key Metrics to Monitor
- **Error Rate**: < 1% of requests should fail
- **Response Time**: 95th percentile < 2 seconds
- **Share Success Rate**: Track share attempts vs successes
- **Image Generation**: Should not fail or timeout

### Health Check Automation
```bash
# Run health check every 15 minutes
*/15 * * * * cd /path/to/project && uv run python scripts/tests/deployment/test_production_health.py >> /var/log/perspectiveshift-health.log 2>&1
```

### Alert Conditions
- Any health check failure
- Error rate > 5% for 10 minutes
- Database connection failures
- Image generation failures > 10%

### Dashboard URLs
- **Vercel Analytics**: https://vercel.com/dashboard
- **Share Stats API**: https://theperspectiveshift.vercel.app/share-stats
- **Health Status**: https://theperspectiveshift.vercel.app/health

## Development Patterns

### Adding New Features
1. **Always start with tests** - Create test scripts first
2. **Use centralized helpers** - Don't duplicate URL construction
3. **Follow DRY principles** - Update utils.py and url_helpers.html
4. **Test on production** - Use real curl commands, not just local

### Code Organization
- **Routes**: Business logic in routes.py
- **Utilities**: Pure functions in utils.py  
- **Templates**: Jinja2 helpers from utils.py
- **JavaScript**: Centralized in url_helpers.html
- **Tests**: Permanent tests in scripts/, temporary in root

### Database Changes
- **Always create migration scripts** in scripts/
- **Test on production clone** before deploying
- **Make migrations idempotent** (safe to run multiple times)
- **Update models.py** and corresponding routes

---

**Last Updated:** $(date)
**Version:** 1.0.0

*This runbook should be updated whenever new testing patterns or procedures are discovered.*