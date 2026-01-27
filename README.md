# DN AI Dokumentanalyse

AI-drevet dokumentanalyse for Dagens Næringsliv som ekstraherer tekst fra PDF-filer og genererer intelligente oppsummeringer.

## 🚀 Funksjonalitet

- **PDF Upload**: Dra og slipp PDF-dokumenter (maks 10MB)
- **AI Tekstekstraksjon**: Azure AI Document Intelligence for robust OCR
- **Intelligent Analyse**: Azure AI Foundry LLM for norskspråklig oppsummering
- **Sikker Lagring**: Azure Blob Storage i Norge for GDPR-compliance

## 🏗️ Arkitektur

### Frontend
- **React 18** med TypeScript og Material-UI
- **Vite** for rask utvikling og build
- **Azure Static Web Apps** for hosting

### Backend
- **Azure Functions** (Python) for serverless API
- **Azure AI Document Intelligence** (Norway East)
- **Azure AI Foundry** for LLM-basert dokumentanalyse 
- **Azure Blob Storage** (Norway East)

### Deployment
- **GitHub Actions** for CI/CD
- **Azure Static Web Apps** med integrert API
- **Environment Secrets** for sikker nøkkelbehandling

## 🛠️ Lokal Utvikling

```bash
# Frontend
cd frontend
npm install
npm run dev

# Backend  
cd api
pip install -r requirements.txt
func start
```

## 🔐 Environment Variabler

### For GitHub Secrets (CI/CD):
**Se `GITHUB_SECRETS_UPDATE_GUIDE.md` for detaljert steg-for-steg guide.**

Nødvendige secrets:
- `DOC_INTELLIGENCE_KEY`: Azure Document Intelligence API-nøkkel
- `DOC_INTELLIGENCE_ENDPOINT`: Azure Document Intelligence endpoint URL
- `AI_FOUNDRY_ENDPOINT`: Azure AI Foundry endpoint (f.eks. https://<resource-name>.services.ai.azure.com)
- `AI_FOUNDRY_API_KEY`: Azure AI Foundry API-nøkkel
- `AI_FOUNDRY_MODEL`: Model deployment name i Azure AI Foundry (standard: gpt-4o-mini)
- `AZURE_STORAGE_CONNECTION_STRING`: Azure Storage tilkoblingsstreng
- `AZURE_STORAGE_ACCOUNT_KEY`: (valgfritt) Azure Storage account key
- `AZUREWEBJOBSSTORAGE`: (valgfritt) Azure Functions storage connection

### For Azure Function App (via Azure Portal):
Se `AZURE_AI_FOUNDRY_SETUP.md` for konfigurasjonsguide.

## 📊 Kostnadsoptimalisering

- **Azure Functions Consumption Plan**: Pay-per-use
- **GPT-4o-mini**: Kostnadseffektiv AI-modell
- **Free Tier**: Document Intelligence F0, Storage LRS
- **Estimat**: <50 NOK/måned ved moderat bruk

## 🇳🇴 Compliance

- **Data i Norge**: Storage og Document Intelligence i Norway East
- **GDPR**: Automatisk sletting av opplastede filer
- **Sikkerhet**: HTTPS, API-nøkler, ingen persistent lagring

## 🚦 Status

✅ Infrastructure (Azure)  
✅ Backend API (Functions)  
✅ Frontend (React)  
✅ Deployment (GitHub Actions)  
✅ Live Application: https://brave-ground-0673aca03.6.azurestaticapps.net/

## 🎨 Design Features

- **DN Branding**: Dagens Næringsliv logo og farger
- **Aeonik Typography**: Work Sans font for moderne utseende  
- **Glassmorphism**: Moderne UI med blur-effekter
- **Seamless Sections**: Sømløs overgang mellom UI-seksjoner
- **Responsive Design**: Optimalisert for alle enheter# Trigger deployment
