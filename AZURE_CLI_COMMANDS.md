# Azure CLI Kommandoer for å Hente Azure AI Foundry Info

Hvis Azure CLI har permission problemer, kan du kjøre disse kommandoene direkte i terminalen.

## Forutsetninger

1. Logg inn i Azure CLI:
```bash
az login
```

2. Sett riktig subscription (hvis du har flere):
```bash
az account list --output table
az account set --subscription "<subscription-id>"
```

## Hent Informasjon

### 1. Finn Resource Group

```bash
az cognitiveservices account list \
  --query "[?name=='pdf-ai-openai-eastus'].{name:name, resourceGroup:resourceGroup, location:location}" \
  --output table
```

### 2. Hent Endpoint og Keys

```bash
# Sett resource group navnet (erstatt med faktisk navn fra steg 1)
RESOURCE_GROUP="<din-resource-group>"
RESOURCE_NAME="pdf-ai-openai-eastus"

# Hent endpoint
az cognitiveservices account show \
  --name "$RESOURCE_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query "properties.endpoint" -o tsv

# Hent API keys
az cognitiveservices account keys list \
  --name "$RESOURCE_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query "key1" -o tsv
```

### 3. Hent Deployments (Modell-navn)

```bash
# List alle deployments
az cognitiveservices account deployment list \
  --name "$RESOURCE_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query "[].{name:name, model:properties.model.name}" \
  --output table
```

## Alternativ: Bruk Script

Kjør scriptet jeg har laget:

```bash
bash get_azure_foundry_info.sh
```

## Eksempel Output

Etter å ha kjørt kommandoene, vil du få:

- **Endpoint**: `https://pdf-ai-openai-eastus.openai.azure.com` (eller lignende)
- **API Key**: En lang streng med tegn
- **Model Name**: F.eks. `gpt-4o-mini`

## Sett Secrets i GitHub

Når du har verdiene, sett dem i GitHub Secrets:

1. Gå til GitHub → Settings → Secrets and variables → Actions
2. Klikk "New repository secret"
3. Legg til:
   - Name: `AI_FOUNDRY_ENDPOINT`, Value: endpoint fra steg 2
   - Name: `AI_FOUNDRY_API_KEY`, Value: key1 fra steg 2
   - Name: `AI_FOUNDRY_MODEL`, Value: name fra steg 3
