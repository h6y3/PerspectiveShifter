# 🚀 Vercel Deployment Guide for PerspectiveShifter

This guide will walk you through deploying your **100% Python Flask** PerspectiveShifter application to Vercel.

## ✅ Prerequisites

1. GitHub account with your code pushed to a repository
2. Vercel account (free tier is sufficient)
3. OpenAI API key
4. Database setup (we'll use Vercel Postgres for production)

## 🎯 Step-by-Step Deployment

### Step 1: Prepare Your Repository

Ensure these files are in your repository:
- ✅ `vercel.json` (Python-only configuration)
- ✅ `.vercelignore` (excludes development artifacts)
- ✅ `requirements.txt` (Python dependencies only)
- ✅ `api/index.py` (Flask application entry point)

### Step 2: Connect to Vercel

1. Go to [vercel.com](https://vercel.com) and sign up/login
2. Click "New Project"
3. Import your GitHub repository
4. Vercel will auto-detect it as a Python project

### Step 3: Configure Environment Variables

In the Vercel dashboard, add these environment variables:

**Required:**
- `OPENAI_API_KEY`: Your OpenAI API key
- `DATABASE_URL`: Will be provided by Vercel Postgres

**Optional:**
- `FLASK_ENV`: `production`
- `PYTHONPATH`: `.` (usually auto-set)

### Step 4: Add Database (Vercel Postgres)

1. In your Vercel project dashboard, go to "Storage"
2. Click "Create Database" → "Postgres"
3. Choose the free tier: "Hobby - $0/month"
4. Name it something like `perspectiveshift-db`
5. Vercel will automatically add the `DATABASE_URL` environment variable

### Step 5: Deploy!

1. Click "Deploy" in Vercel
2. Wait for the build to complete (~2-3 minutes)
3. Your app will be live at: `https://your-project-name.vercel.app`

## 🔧 Post-Deployment Setup

### Database Initialization

The app will automatically create tables on first run, but if you need to reset:

1. Go to your Vercel Postgres dashboard
2. Use the Query editor to run:
```sql
DROP TABLE IF EXISTS quote_cache;
DROP TABLE IF EXISTS daily_stats;
```
3. Restart your deployment (the app will recreate tables)

### Custom Domain (Optional)

1. In Vercel dashboard, go to "Domains"
2. Add your custom domain
3. Follow Vercel's DNS setup instructions

## 🛠️ Local Development vs Production

### Environment Variables Comparison

| Variable | Local Development | Production (Vercel) |
|----------|-------------------|---------------------|
| `DATABASE_URL` | `sqlite:///perspective_shift.db` | `postgresql://...` (auto-provided) |
| `OPENAI_API_KEY` | Your dev API key | Your production API key |
| `FLASK_ENV` | `development` | `production` |

### Testing Your Deployment

1. Visit your Vercel URL
2. Try submitting a perspective shift
3. Test image generation by sharing a quote
4. Check the Vercel Function logs for any errors
5. Verify database connections in Vercel Postgres dashboard

## 🚨 Troubleshooting

### Common Issues:

**Build Fails:**
- Check that `requirements.txt` includes all Python dependencies
- Ensure no syntax errors in Python files
- Verify `vercel.json` is configured for Python-only
- Check Vercel build logs for specific errors

**Database Connection Issues:**
- Verify `DATABASE_URL` is set in environment variables
- Ensure Vercel Postgres database is created and connected
- Check that `psycopg2-binary` is in requirements.txt

**Image Generation Issues:**
- Verify PIL/Pillow is in requirements.txt
- Check font files exist in `static/fonts/` directory
- Ensure image generation routes return proper Flask Response
- Test with `/health` endpoint to verify PIL installation

**OpenAI API Errors:**
- Verify `OPENAI_API_KEY` is set correctly
- Check your OpenAI API quota and billing
- Ensure the API key has proper permissions

**Static Files Not Loading:**
- Verify your static files are in the `static/` directory
- Check `.vercelignore` isn't excluding necessary files
- Ensure static file routes in `vercel.json` are correct

### Checking Logs

1. Go to your Vercel project dashboard
2. Click on a deployment
3. View "Functions" tab for runtime logs
4. Check "Build Logs" for deployment issues

## 📊 Monitoring & Analytics

Vercel provides built-in analytics:
- Visit your project dashboard
- Click "Analytics" to see traffic, performance
- Monitor function execution times and errors
- Use `/health` endpoint for application health checks

## 💰 Cost Considerations

**Vercel Free Tier Includes:**
- 100GB bandwidth per month
- 100 serverless function invocations per day
- Custom domains
- HTTPS certificates

**Vercel Postgres Free Tier:**
- 60 hours of compute per month
- 0.5 GB storage
- 1 GB data transfer

For a hobby project, this should be more than sufficient!

## 🔄 Continuous Deployment

Once set up:
- Every push to your main branch auto-deploys
- Preview deployments for pull requests
- Rollback to previous deployments with one click

## 🎉 You're Live!

Your PerspectiveShifter app is now live on the internet! Share the URL with friends and start collecting wisdom quotes.

**Architecture Highlights:**
- ✅ 100% Python Flask application
- ✅ PIL/Pillow for image generation
- ✅ Direct Flask responses (no redirects)
- ✅ Single technology stack
- ✅ Optimized for Vercel serverless

**Next Steps:**
- Set up custom domain (optional)
- Monitor usage through Vercel dashboard
- Scale up database if needed as usage grows 