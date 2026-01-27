# Quick Setup - GitHub Secrets

## Sett opp disse 3 secrets i GitHub:

1. **AI_FOUNDRY_ENDPOINT**: `https://eastus.api.cognitive.microsoft.com/`
2. **AI_FOUNDRY_API_KEY**: `<din-api-key-fra-azure-portal>`
3. **AI_FOUNDRY_MODEL**: `gpt-4o-mini` (eller hva som er deployment-navnet ditt)

## Hvor:

GitHub → Repository → Settings → Secrets and variables → Actions → New repository secret

## Hvis model-navnet er annerledes:

Sjekk Azure Portal → pdf-ai-openai-eastus → Deployments og bruk det navnet.

## Test:

Etter at secrets er satt, push koden og se om deployment fungerer!
