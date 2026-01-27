# Azure AI Foundry Konfigurasjon

Denne guiden forklarer hvordan du konfigurerer Azure AI Foundry for dokumentanalyse.

## Hva er endret?

Løsningen er nå oppdatert til å bruke **Azure AI Foundry** i stedet for Azure OpenAI for LLM-basert dokumentanalyse. Vi bruker `azure-ai-inference` SDK med Azure AI Inference API.

## Konfigurasjon

### 1. Opprett Azure AI Foundry Resource

1. Gå til [Azure Portal](https://portal.azure.com) eller [Microsoft Foundry Portal](https://ai.azure.com)
2. Opprett en ny **Azure AI Foundry** resource
3. Noter ned:
   - **Endpoint URL**: `https://<resource-name>.services.ai.azure.com`
   - **API Key**: Fra "Keys and Endpoint" i portalen

### 2. Deploy en Model

Azure AI Foundry tilbyr **over 11,000+ modeller** fra flere leverandører:

**Tilgjengelige modeller inkluderer:**
- **Microsoft/Azure OpenAI**: GPT-4o, GPT-4o-mini, GPT-4, GPT-3.5-turbo
- **Mistral AI**: Mistral Large 3, Mistral Small
- **Meta**: Llama 2, Llama 3 (7B til 70B parametere)
- **DeepSeek**: DeepSeek R1, DeepSeek V2
- **Cohere**: Command, Command R+
- **Anthropic**: Claude (hvis tilgjengelig)
- **xAI**: Grok modeller
- Og mange flere...

**Slik deployer du en modell:**

1. I Azure AI Foundry, gå til **"Models"** eller **"Model Catalog"**
2. Søk etter og velg en modell (f.eks. "gpt-4o-mini", "mistral-large", "llama-3-70b")
3. Klikk **"Deploy"** og velg deployment type (Serverless eller Managed Compute)
4. Noter ned **deployment navnet** (f.eks. "gpt-4o-mini")

### 3. Sett Environment Variabler

#### For Azure Function App (via Azure Portal):

Gå til Function App → Configuration → Application settings og legg til:

```
AI_FOUNDRY_ENDPOINT=https://<resource-name>.services.ai.azure.com
AI_FOUNDRY_API_KEY=<din-api-key>
AI_FOUNDRY_MODEL=<deployment-navn>
```

**Viktig:** Endpoint skal være base URL uten `/models` (koden legger til dette automatisk).

#### For GitHub Secrets (CI/CD):

**VIKTIG:** Se den detaljerte guiden i `GITHUB_SECRETS_UPDATE_GUIDE.md` for steg-for-steg instruksjoner.

Kort oppsummert:

1. **Slett gamle secrets:**
   - `OPENAI_ENDPOINT` ❌
   - `OPENAI_API_KEY` ❌

2. **Legg til nye secrets:**
   - `AI_FOUNDRY_ENDPOINT` ✅ (f.eks. `https://myfoundry.services.ai.azure.com`)
   - `AI_FOUNDRY_API_KEY` ✅ (din API-nøkkel fra Azure Portal)
   - `AI_FOUNDRY_MODEL` ✅ (f.eks. `gpt-4o-mini`)

Gå til: GitHub Repository → Settings → Secrets and variables → Actions

## Endringer i Koden

### requirements.txt

- Erstattet `openai` med `azure-ai-inference` SDK

### function_app.py

- Bruker `azure-ai-inference` SDK med `ChatCompletionsClient`
- Endpoint format: `https://<resource-name>.services.ai.azure.com/models`
- Bruker `SystemMessage` og `UserMessage` fra `azure.ai.inference.models`
- Bruker miljøvariabler: `AI_FOUNDRY_ENDPOINT`, `AI_FOUNDRY_API_KEY`, `AI_FOUNDRY_MODEL`

### GitHub Actions

- Oppdatert `.github/workflows/azure-static-web-apps.yml` til å bruke Azure AI Foundry secrets

## Testing

For å teste lokalt:

1. Installer dependencies:
```bash
cd api
pip install -r requirements.txt
```

2. Sett environment variabler i `local.settings.json` (for Azure Functions):
```json
{
  "Values": {
    "AI_FOUNDRY_ENDPOINT": "https://<resource-name>.services.ai.azure.com",
    "AI_FOUNDRY_API_KEY": "<din-api-key>",
    "AI_FOUNDRY_MODEL": "gpt-4o-mini"
  }
}
```

**Eksempel med forskjellige modeller:**
```json
{
  "Values": {
    "AI_FOUNDRY_ENDPOINT": "https://myfoundry.services.ai.azure.com",
    "AI_FOUNDRY_API_KEY": "your-key-here",
    "AI_FOUNDRY_MODEL": "gpt-4o-mini"  // eller "mistral-large", "llama-3-70b", etc.
  }
}
```

3. Start Azure Functions:
```bash
func start
```

4. Test med en PDF eller TXT fil via frontend

## Feilsøking

### "Azure AI Foundry configuration missing"
- Sjekk at alle tre miljøvariabler er satt: `AI_FOUNDRY_ENDPOINT`, `AI_FOUNDRY_API_KEY`, `AI_FOUNDRY_MODEL`

### "Model not found"
- Sjekk at modell-deployment navnet i `AI_FOUNDRY_MODEL` matcher eksakt med navnet i Azure AI Foundry

### "Authentication failed"
- Verifiser at `AI_FOUNDRY_API_KEY` er korrekt
- Sjekk at API key ikke er utløpt

## Støttede Modeller

Azure AI Foundry tilbyr **over 11,000+ modeller** fra flere leverandører. Noen populære valg:

### Anbefalte Modeller for Dokumentanalyse

- **GPT-4o-mini** - Kostnadseffektiv, rask, god for norsk tekst
- **GPT-4o** - Høyere kvalitet, bedre for komplekse analyser
- **Mistral Large 3** - God balanse mellom kvalitet og kostnad
- **Llama 3 70B** - Åpen kildekode, kraftig modell
- **DeepSeek R1** - God for resonnering og analyse

### Hvordan Vise Tilgjengelige Modeller

1. Gå til [Microsoft Foundry Portal](https://ai.azure.com)
2. Klikk på **"Discover"** → **"Models"**
3. Søk etter modeller eller filtrer etter leverandør
4. Se detaljer, prising og deploy direkte

## Kostnader

Kostnader varierer basert på modell og deployment type:
- **Serverless**: Pay-per-use, ingen minimumsforpliktelse
- **Managed Compute**: Dedikerte ressurser, fast månedlig kostnad

Se [Azure AI Foundry prising](https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/) for detaljer. GPT-4o-mini er typisk den mest kostnadseffektive for dokumentanalyse.
