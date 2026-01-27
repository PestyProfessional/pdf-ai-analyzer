#!/bin/bash

# Script for å hente Azure AI Foundry informasjon
# Kjør dette i terminalen: bash get_azure_foundry_info.sh

echo "=== Henter Azure AI Foundry informasjon ==="
echo ""

# Resource navn
RESOURCE_NAME="pdf-ai-openai-eastus"

echo "1. Henter resource informasjon..."
az cognitiveservices account show \
  --name "$RESOURCE_NAME" \
  --resource-group $(az cognitiveservices account list --query "[?name=='$RESOURCE_NAME'].resourceGroup" -o tsv) \
  --query "{endpoint:properties.endpoint, kind:kind}" -o json

echo ""
echo "2. Henter API keys..."
az cognitiveservices account keys list \
  --name "$RESOURCE_NAME" \
  --resource-group $(az cognitiveservices account list --query "[?name=='$RESOURCE_NAME'].resourceGroup" -o tsv) \
  --query "{key1:key1, key2:key2}" -o json

echo ""
echo "3. Henter deployments..."
az cognitiveservices account deployment list \
  --name "$RESOURCE_NAME" \
  --resource-group $(az cognitiveservices account list --query "[?name=='$RESOURCE_NAME'].resourceGroup" -o tsv) \
  --query "[].{name:name, model:properties.model.name, version:properties.model.version}" -o table

echo ""
echo "=== Ferdig ==="
echo ""
echo "For å sette secrets i GitHub, bruk verdiene over:"
echo "- AI_FOUNDRY_ENDPOINT: endpoint fra steg 1"
echo "- AI_FOUNDRY_API_KEY: key1 eller key2 fra steg 2"
echo "- AI_FOUNDRY_MODEL: name fra steg 3"
