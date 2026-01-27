# Azure Resource Recreation Plan

Fra skjermbildet kan jeg se følgende ressurser som må gjenskapes:

## Ressurser som skal gjenskapes:

### 1. **pdf-ai-analyzer-app** (Static Web App)
- **Type**: Static Web App
- **Location**: West Europe
- **GitHub Integration**: https://github.com/PestyProfessional/pdf-ai-analyzer
- **Custom Domain**: brave-ground-0673aca03.6.azurestaticapps.net

### 2. **pdf-ai-document-intelligence-no** (Document Intelligence)
- **Type**: Document intelligence 
- **Location**: Norway East
- **SKU**: F0 (Free tier)
- **Endpoint**: https://norwayeast.api.cognitive.microsoft.com/

### 3. **pdf-ai-functions** (Function App)
- **Type**: Function App
- **Location**: Norway East
- **Runtime**: Python
- **Plan**: Consumption (serverless)

### 4. **pdfaianalyzernorway** (Storage Account)
- **Type**: Storage account
- **Location**: Norway East
- **SKU**: Standard LRS
- **Container**: pdf-uploads

### 5. **Azure AI Foundry Resource** (MUST OPPRETTES)
- **Type**: Azure AI Foundry / Cognitive Services
- **Location**: Kan være i flere regioner (sjekk tilgjengelighet)
- **Purpose**: LLM-basert dokumentanalyse
- **Deployment**: Deploy en modell (f.eks. gpt-4o-mini, mistral-large)

## Kommandoer for gjenopprettelse:

```bash
# 1. Resource Group
az group create --name "pdf-ai-analyzer-rg" --location "westeurope"

# 2. Storage Account
az storage account create --name "pdfaianalyzernorway" --resource-group "pdf-ai-analyzer-rg" --location "norwayeast" --sku "Standard_LRS"

# 3. Document Intelligence
az cognitiveservices account create --name "pdf-ai-document-intelligence-no" --resource-group "pdf-ai-analyzer-rg" --kind "FormRecognizer" --sku "F0" --location "norwayeast"

# 4. Function App
az functionapp create --name "pdf-ai-functions" --resource-group "pdf-ai-analyzer-rg" --storage-account "pdfaianalyzernorway" --consumption-plan-location "norwayeast" --runtime "python" --runtime-version "3.9"

# 5. Azure AI Foundry Resource (KRITISK - må fungere)
# OBS: Azure AI Foundry opprettes via Azure Portal eller Microsoft Foundry Portal
# Gå til https://ai.azure.com eller https://portal.azure.com
# Opprett en Azure AI Foundry resource og deploy en modell
# Noter ned: Endpoint og API Key

# 7. Static Web App (via GitHub Actions)
az staticwebapp create --name "pdf-ai-analyzer-app" --resource-group "pdf-ai-analyzer-rg" --source "https://github.com/PestyProfessional/pdf-ai-analyzer" --location "westeurope" --branch "main" --app-location "/frontend" --api-location "/api" --output-location "dist"
```

## Nødvendige secrets/nøkler som må oppdateres:

1. **GitHub Secrets** (se `GITHUB_SECRETS_UPDATE_GUIDE.md` for detaljer):
   - AZURE_STATIC_WEB_APPS_API_TOKEN
   - DOC_INTELLIGENCE_ENDPOINT
   - DOC_INTELLIGENCE_KEY
   - AI_FOUNDRY_ENDPOINT (NY - erstatter OPENAI_ENDPOINT)
   - AI_FOUNDRY_API_KEY (NY - erstatter OPENAI_API_KEY)
   - AI_FOUNDRY_MODEL (NY - modell deployment navn)
   - AZURE_STORAGE_CONNECTION_STRING
   - AZURE_STORAGE_ACCOUNT_KEY (hvis brukt)
   - AZUREWEBJOBSSTORAGE (hvis brukt)

2. **Azure Function App Settings** (via Azure Portal):
   - DOC_INTELLIGENCE_ENDPOINT
   - DOC_INTELLIGENCE_KEY
   - AI_FOUNDRY_ENDPOINT (NY)
   - AI_FOUNDRY_API_KEY (NY)
   - AI_FOUNDRY_MODEL (NY)
   - AZURE_STORAGE_CONNECTION_STRING eller AzureWebJobsStorage

## Kritiske punkter:
- **Azure AI Foundry-ressursen** er kritisk - DETTE MÅ FUNGERE
- Modell må være deployet i Azure AI Foundry
- Alle secrets må oppdateres i GitHub (se `GITHUB_SECRETS_UPDATE_GUIDE.md`)
- Alle andre ressurser eksisterer og kan gjenskapes identisk
- GitHub repository og kode er intakt
- Storage container må opprettes: "pdf-uploads"

## Migrasjon fra Azure OpenAI til Azure AI Foundry:
- Se `AZURE_AI_FOUNDRY_SETUP.md` for konfigurasjonsguide
- Se `GITHUB_SECRETS_UPDATE_GUIDE.md` for oppdatering av secrets