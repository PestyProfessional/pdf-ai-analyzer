# Secrets Checklist - Rask Oversikt

Denne checklisten gir deg en rask oversikt over hva som må oppdateres i GitHub Secrets.

## ✅ Secrets som skal BEHOLDES (ikke endre)

- `AZURE_STATIC_WEB_APPS_API_TOKEN`
- `DOC_INTELLIGENCE_ENDPOINT`
- `DOC_INTELLIGENCE_KEY`
- `AZURE_STORAGE_CONNECTION_STRING`
- `AZURE_STORAGE_ACCOUNT_KEY` (hvis du har denne)
- `AZUREWEBJOBSSTORAGE` (hvis du har denne)
- `GITHUB_TOKEN` (automatisk, ikke endre)

## ❌ Secrets som skal SLETTES

- `OPENAI_ENDPOINT` → **SLETT**
- `OPENAI_API_KEY` → **SLETT**

## ✅ Secrets som skal OPPRETTES (nye)

- `AI_FOUNDRY_ENDPOINT` → **OPPRETT**
  - Format: `https://<resource-name>.services.ai.azure.com`
  - Eksempel: `https://myfoundry.services.ai.azure.com`

- `AI_FOUNDRY_API_KEY` → **OPPRETT**
  - Din API-nøkkel fra Azure AI Foundry
  - Finn i Azure Portal → Keys and Endpoint

- `AI_FOUNDRY_MODEL` → **OPPRETT**
  - Navnet på din deployede modell
  - Eksempler: `gpt-4o-mini`, `mistral-large`, `llama-3-70b`
  - Standard: `gpt-4o-mini`

## 📋 Quick Actions

1. [ ] Gå til GitHub → Settings → Secrets and variables → Actions
2. [ ] Slett `OPENAI_ENDPOINT`
3. [ ] Slett `OPENAI_API_KEY`
4. [ ] Opprett `AI_FOUNDRY_ENDPOINT` med din endpoint URL
5. [ ] Opprett `AI_FOUNDRY_API_KEY` med din API-nøkkel
6. [ ] Opprett `AI_FOUNDRY_MODEL` med modell-navnet
7. [ ] Verifiser at alle secrets er satt riktig
8. [ ] Test deployment

## 📖 Detaljert Guide

For steg-for-steg instruksjoner, se `GITHUB_SECRETS_UPDATE_GUIDE.md`
