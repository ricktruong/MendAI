# Render Deployment Quick Start

This is a condensed guide for deploying MendAI to Render. For detailed instructions, see [RENDER_DEPLOYMENT.md](./RENDER_DEPLOYMENT.md).

## Prerequisites Checklist

- [ ] Render account created
- [ ] GitHub repository connected to Render
- [ ] OpenAI API key ready
- [ ] Google Cloud service account JSON ready (for Patient Data service)

## Quick Deployment Steps

### 1. Deploy Using Blueprint (Easiest)

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub repository
4. Render will detect `render.yaml` automatically
5. Click **"Apply"** to create all 5 services

### 2. Configure Environment Variables

**Deploy services in this order** (set env vars before deploying):

#### Step 1: Deploy Backend Services First

**Patient Data Service** (`mendai-patient-data`):
```
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}  # Full JSON as string
```

**Medical Imaging Service** (`mendai-medical-imaging`):
```
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-5.1
```

**Biomedical LLM Service** (`mendai-biomedical-llm`):
```
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
PATIENT_DATA_URL=https://mendai-patient-data.onrender.com  # Update after deployment
```

**Engine Service** (`mendai-engine`):
```
OPENAI_API_KEY=sk-your-key-here
PATIENT_DATA_SERVICE_URL=https://mendai-patient-data.onrender.com  # Update after deployment
MEDICAL_IMAGING_SERVICE_URL=https://mendai-medical-imaging.onrender.com  # Update after deployment
BIOMEDICAL_LLM_URL=https://mendai-biomedical-llm.onrender.com  # Update after deployment
CORS_ORIGINS=["https://mendai-frontend.onrender.com"]  # Update after deployment
```

#### Step 2: Deploy Frontend Last

**Frontend Service** (`mendai-frontend`):
```
VITE_API_BASE_URL=https://mendai-engine.onrender.com  # Update after engine is deployed
```

**⚠️ Important**: Set `VITE_API_BASE_URL` BEFORE deploying frontend, as it's embedded at build time.

### 3. Update Service URLs

After all services are deployed:

1. Get each service's URL from Render dashboard
2. Update environment variables that reference other services:
   - Frontend → Engine URL
   - Engine → All backend service URLs + CORS_ORIGINS
   - Biomedical LLM → Patient Data URL
3. Trigger redeployments for services that changed

### 4. Verify Deployment

Test each service:

```bash
# Backend services
curl https://mendai-engine.onrender.com/health
curl https://mendai-patient-data.onrender.com/health
curl https://mendai-medical-imaging.onrender.com/health
curl https://mendai-biomedical-llm.onrender.com/health

# Frontend (should load in browser)
open https://mendai-frontend.onrender.com
```

## Common Issues

### Frontend shows "Cannot connect to API"
- **Fix**: Check `VITE_API_BASE_URL` is set correctly and redeploy frontend

### Backend services can't connect to each other
- **Fix**: Verify all service URLs in environment variables are correct
- Check that services are running (not sleeping on free tier)

### Google Cloud authentication fails
- **Fix**: Verify `GOOGLE_SERVICE_ACCOUNT_JSON` is valid JSON (escape quotes properly)
- Ensure service account has necessary permissions

### Build fails with "Poetry lock file not found"
- **Fix**: Generate lock files locally and commit:
  ```bash
  cd backend/engine && poetry lock && git add poetry.lock
  cd ../patient_data && poetry lock && git add poetry.lock
  cd ../medical_imaging && poetry lock && git add poetry.lock
  cd ../biomedical_llm && poetry lock && git add poetry.lock
  git commit -m "Add poetry lock files"
  git push
  ```

## Service URLs Pattern

Render URLs follow this pattern:
- `https://{service-name}.onrender.com`

Your services will be:
- `https://mendai-frontend.onrender.com`
- `https://mendai-engine.onrender.com`
- `https://mendai-patient-data.onrender.com`
- `https://mendai-medical-imaging.onrender.com`
- `https://mendai-biomedical-llm.onrender.com`

## Cost Estimate

- **Free Tier**: 90 days free for all services
- **After Free Tier**: ~$7/month per service = ~$35/month total
- **Recommendation**: Use free tier for testing, upgrade when ready for production

## Next Steps

1. Set up custom domains (optional)
2. Configure monitoring and alerts
3. Set up CI/CD for automatic deployments
4. Review security settings (CORS, secrets)

For detailed information, see [RENDER_DEPLOYMENT.md](./RENDER_DEPLOYMENT.md).
