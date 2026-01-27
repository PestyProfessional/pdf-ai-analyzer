# Azure Secrets - Verdier for GitHub

## Verdier som skal settes i GitHub Secrets

### 1. AI_FOUNDRY_ENDPOINT
```
https://eastus.api.cognitive.microsoft.com/
```

### 2. AI_FOUNDRY_API_KEY
```
<din-api-key-fra-azure-portal>
```

### 3. AI_FOUNDRY_MODEL
**MÅ FINNES** - Gå til Azure Portal → pdf-ai-openai-eastus → Deployments
Vanlige navn: `gpt-4o-mini`, `gpt-4o`, `gpt-35-turbo`

## Hvordan sette opp i GitHub

1. Gå til GitHub → Settings → Secrets and variables → Actions
2. Klikk "New repository secret" for hver verdi
3. Sett navn og verdi
4. Klikk "Add secret"

## Notater

- Endpoint kan være regionalt format (eastus.api.cognitive.microsoft.com)
- Koden er oppdatert til å støtte både Azure OpenAI og Azure AI Foundry format
- Model-navnet må matche eksakt med deployment-navnet i Azure Portal
