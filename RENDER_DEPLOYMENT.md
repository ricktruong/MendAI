# Render Deployment Guide for MendAI

This guide will help you deploy your MendAI application to Render PaaS.

## Prerequisites

1. **Render Account**: Sign up at [render.com](https://render.com)
2. **GitHub Repository**: Your code should be in a GitHub repository
3. **API Keys**:
   - OpenAI API Key (for LLM and Medical Imaging services)
   - Google Cloud credentials (for Patient Data service)

## Overview

MendAI consists of 5 services that need to be deployed:
1. **Frontend** - React application (Static Site)
2. **Engine** - API Gateway (Web Service)
3. **Patient Data** - FHIR data service (Web Service)
4. **Medical Imaging** - Image analysis service (Web Service)
5. **Biomedical LLM** - Language model service (Web Service)

## Deployment Steps

### Step 1: Connect Your Repository

1. Log in to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Blueprint"** (or use individual services)
3. Connect your GitHub repository
4. Select the repository containing MendAI

### Step 2: Deploy Using render.yaml (Recommended)

Render supports Blueprint deployments using `render.yaml`:

1. **Create Blueprint**:
   - In Render Dashboard, click **"New +"** → **"Blueprint"**
   - Connect your repository
   - Render will automatically detect `render.yaml`
   - Click **"Apply"** to create all services

2. **Configure Environment Variables**:
   After services are created, you need to configure environment variables for each service.

### Step 3: Configure Environment Variables

For each service, go to the **Environment** tab and set the following:

#### Frontend Service (`mendai-frontend`)

**IMPORTANT**: Set this environment variable **BEFORE** the first deployment, as Vite embeds environment variables at build time.

```
VITE_API_BASE_URL=https://mendai-engine.onrender.com
```

**Note**: 
- Replace `mendai-engine.onrender.com` with your actual Engine service URL
- If you need to change this later, you'll need to trigger a new deployment (Render will rebuild the Docker image)
- You can set a placeholder initially, then update it and redeploy after all services are up

#### Engine Service (`mendai-engine`)

```
PATIENT_DATA_SERVICE_URL=https://mendai-patient-data.onrender.com
MEDICAL_IMAGING_URL=https://mendai-medical-imaging.onrender.com
BIOMEDICAL_LLM_URL=https://mendai-biomedical-llm.onrender.com
OPENAI_API_KEY=sk-your-openai-api-key-here
```

**Note**: Replace URLs with your actual service URLs after deployment.

#### Patient Data Service (`mendai-patient-data`)

**Using Service Account JSON as Environment Variable**

Your Google Service Account JSON file is located at:
```
backend/patient_data/mendai-470816-d39912146cc6.json
```

To convert it to a single-line string for Render, use Python:
```bash
cd /path/to/MendAI
cat backend/patient_data/mendai-470816-d39912146cc6.json | python3 -c "import json, sys; print(json.dumps(json.load(sys.stdin), separators=(',', ':')))"
```

Then set these environment variables in Render:
```
GOOGLE_CLOUD_PROJECT=mendai-470816
GOOGLE_SERVICE_ACCOUNT_JSON=<paste the single-line JSON string here>
```

**Important**: 
- Copy the entire output (it will be one long line)
- Paste it directly into Render's `GOOGLE_SERVICE_ACCOUNT_JSON` environment variable
- Do NOT add quotes around it in Render (Render will handle that)
- The JSON contains sensitive credentials - keep it secure!

#### Medical Imaging Service (`mendai-medical-imaging`)

```
OPENAI_API_KEY=sk-your-openai-api-key-here
```

**Note**: The OpenAI model is configured via dynaconf settings, not environment variables.

#### Biomedical LLM Service (`mendai-biomedical-llm`)

```
OPENAI_API_KEY=sk-your-openai-api-key-here
PATIENT_DATA_URL=https://mendai-patient-data.onrender.com
```

**Note**: The OpenAI model is configured via dynaconf settings, not environment variables.

### Step 4: Update Service URLs

After all services are deployed, update the environment variables with the actual Render URLs:

1. Get each service's URL from the Render dashboard
2. Update the environment variables that reference other services:
   - Frontend → Engine URL
   - Engine → Patient Data, Medical Imaging, Biomedical LLM URLs
   - Biomedical LLM → Patient Data URL

### Step 5: Handle Google Cloud Credentials

**IMPORTANT**: Your Google Service Account JSON file (`mendai-470816-d39912146cc6.json`) is **NOT** in your repository (it's in `.gitignore` for security). This is correct and secure!

Since Render doesn't support file uploads directly, we use the environment variable approach:

#### Option A: Use Environment Variable (Recommended for Render)

The Patient Data service already supports reading credentials from the `GOOGLE_SERVICE_ACCOUNT_JSON` environment variable. You just need to:

1. Convert your Google Cloud service account JSON to a single-line string using Python:
   ```bash
   cat backend/patient_data/mendai-470816-d39912146cc6.json | python3 -c "import json, sys; print(json.dumps(json.load(sys.stdin), separators=(',', ':')))"
   ```
2. Set `GOOGLE_SERVICE_ACCOUNT_JSON` environment variable in Render with the single-line JSON string
3. Set `GOOGLE_CLOUD_PROJECT` environment variable (already configured in `render.yaml` as `mendai-470816`)

**Security Note**: The credentials file (`mendai-470816-d39912146cc6.json`) is correctly excluded from your repository via `.gitignore`. The Dockerfile has been updated to NOT copy this file, so it won't be included in the Docker image. This is the secure approach.

### Step 6: Deploy Services

1. **Manual Deployment** (if not using Blueprint):
   - For each service, click **"New +"** → **"Web Service"**
   - Connect repository
   - Configure:
     - **Name**: `mendai-{service-name}`
     - **Environment**: Docker
     - **Dockerfile Path**: `./backend/{service}/Dockerfile` (or `./frontend/Dockerfile` for frontend)
     - **Docker Context**: `./backend` (or `./frontend` for frontend)
     - **Build Command**: Leave default or customize
     - **Start Command**: Leave default (handled by Dockerfile)

2. **Set Environment Variables** for each service (as listed above)

3. **Deploy**: Click **"Create Web Service"** or **"Save Changes"**

### Step 7: Verify Deployment

After deployment, verify each service:

```bash
# Check Engine
curl https://mendai-engine.onrender.com/health

# Check Patient Data
curl https://mendai-patient-data.onrender.com/health

# Check Medical Imaging
curl https://mendai-medical-imaging.onrender.com/health

# Check Biomedical LLM
curl https://mendai-biomedical-llm.onrender.com/health
```

Expected response:
```json
{"status": "healthy", "service": "..."}
```

## Service Dependencies

Services depend on each other in this order:

1. **Patient Data** → No dependencies (deploy first)
2. **Medical Imaging** → No dependencies
3. **Biomedical LLM** → Depends on Patient Data
4. **Engine** → Depends on Patient Data, Medical Imaging, Biomedical LLM
5. **Frontend** → Depends on Engine

**Deployment Order**:
1. Deploy Patient Data, Medical Imaging first
2. Deploy Biomedical LLM (after Patient Data is up)
3. Deploy Engine (after all backend services are up)
4. Deploy Frontend (after Engine is up)

## Troubleshooting

### Build Failures

**Issue**: Docker build fails
- **Solution**: Check Dockerfile paths and context are correct
- Verify all dependencies are listed in `pyproject.toml` or `package.json`
- Check build logs in Render dashboard

**Issue**: Poetry lock file missing
- **Solution**: Generate lock files locally:
  ```bash
  cd backend/engine && poetry lock
  cd ../patient_data && poetry lock
  cd ../medical_imaging && poetry lock
  cd ../biomedical_llm && poetry lock
  ```
  Commit and push the `poetry.lock` files.

### Runtime Errors

**Issue**: Service can't connect to other services
- **Solution**: Verify all service URLs in environment variables are correct
- Check that services are deployed and running
- Verify CORS settings allow requests from frontend

**Issue**: Google Cloud authentication fails
- **Solution**: 
  - Verify `GOOGLE_SERVICE_ACCOUNT_JSON` is valid JSON
  - Check that service account has necessary permissions
  - Ensure project ID is correct

**Issue**: OpenAI API errors
- **Solution**:
  - Verify `OPENAI_API_KEY` is set correctly
  - Check API key has sufficient credits
  - Verify model names are correct (`gpt-4o-mini`, `gpt-5.1`)

### Service Health Checks

All services expose `/health` endpoints. If health checks fail:

1. Check service logs in Render dashboard
2. Verify environment variables are set correctly
3. Check that ports are exposed correctly (8000, 8001, 8002, 8003)

## Cost Considerations

Render pricing:
- **Starter Plan**: $7/month per service (free tier available for 90 days)
- **5 Services**: ~$35/month (or free for 90 days)

**Cost Optimization**:
- Use free tier for development/testing
- Consider combining services if possible (not recommended for microservices)
- Monitor usage and scale down when not needed

## Security Best Practices

1. **Never commit secrets**: All sensitive data should be in environment variables
2. **Use Render Secrets**: Store API keys in Render's environment variables (encrypted)
3. **Restrict CORS**: Update `CORS_ORIGINS` to only allow your frontend domain
4. **Use HTTPS**: Render provides HTTPS by default
5. **Rotate Keys**: Regularly rotate API keys and credentials

## Custom Domains

To use custom domains:

1. Go to service settings in Render dashboard
2. Click **"Custom Domains"**
3. Add your domain
4. Update DNS records as instructed
5. Update `CORS_ORIGINS` to include your custom domain

## Monitoring

Render provides:
- **Logs**: Real-time logs in dashboard
- **Metrics**: CPU, memory, request metrics
- **Alerts**: Set up alerts for service failures

## Continuous Deployment

Render automatically deploys on:
- Push to main/master branch (if configured)
- Manual deployment trigger

To enable auto-deploy:
1. Go to service settings
2. Enable **"Auto-Deploy"**
3. Select branch (usually `main` or `master`)

## Rollback

If deployment fails:

1. Go to service in Render dashboard
2. Click **"Manual Deploy"**
3. Select previous successful commit
4. Deploy

## Additional Resources

- [Render Documentation](https://render.com/docs)
- [Render Docker Guide](https://render.com/docs/docker)
- [Render Environment Variables](https://render.com/docs/environment-variables)

## Support

If you encounter issues:
1. Check Render service logs
2. Review this guide
3. Check Render status page
4. Contact Render support

---

**Last Updated**: December 2024
