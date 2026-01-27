# Guide for Lokal Testing

Denne guiden viser deg hvordan du tester applikasjonen både lokalt og i produksjon.

## 🏠 Lokal Testing

### Forutsetninger

1. **Node.js** installert (for frontend)
2. **Python 3.9+** installert (for backend)
3. **Azure Functions Core Tools** installert
4. **Azure CLI** installert (valgfritt)

### 1. Test Frontend Lokalt

```bash
cd frontend
npm install
npm run dev
```

Frontend vil kjøre på `http://localhost:5173` (eller annen port hvis 5173 er opptatt).

**Viktig:** Frontend trenger API-endepunkt. Se "Konfigurer API Proxy" under.

### 2. Test Backend (Azure Functions) Lokalt

#### Steg 1: Opprett local.settings.json

Opprett filen `api/local.settings.json`:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "DOC_INTELLIGENCE_ENDPOINT": "https://<din-doc-intelligence-endpoint>",
    "DOC_INTELLIGENCE_KEY": "<din-doc-intelligence-key>",
    "AI_FOUNDRY_ENDPOINT": "https://lillw-mkwnaj9t-eastus2.cognitiveservices.azure.com/",
    "AI_FOUNDRY_API_KEY": "<din-api-key>",
    "AI_FOUNDRY_MODEL": "gpt-4o-mini",
    "AZURE_STORAGE_CONNECTION_STRING": "<din-storage-connection-string>"
  }
}
```

**Viktig:** `local.settings.json` er allerede i `.gitignore` og vil ikke bli committet.

#### Steg 2: Installer Dependencies

```bash
cd api
pip install -r requirements.txt
```

#### Steg 3: Start Azure Functions

```bash
func start
```

API vil kjøre på `http://localhost:7071`

### 3. Konfigurer Frontend til å Bruke Lokal API

Oppdater `frontend/vite.config.js` for å legge til proxy:

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist'
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:7071',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api')
      }
    }
  }
})
```

### 4. Test Fullstendig Lokalt

1. Start backend:
   ```bash
   cd api
   func start
   ```

2. Start frontend (i nytt terminalvindu):
   ```bash
   cd frontend
   npm run dev
   ```

3. Åpne nettleser: `http://localhost:5173`

4. Last opp en PDF eller TXT fil og test funksjonaliteten

## 🌐 Testing i Produksjon

### 1. Sjekk Deployment Status

Gå til GitHub Actions:
- https://github.com/PestyProfessional/pdf-ai-analyzer/actions

Sjekk at siste deployment er vellykket.

### 2. Test Produksjons-URL

Din produksjons-URL er:
- https://brave-ground-0673aca03.6.azurestaticapps.net/

### 3. Test Funksjonalitet

1. Gå til produksjons-URL
2. Last opp en test-PDF eller TXT fil
3. Verifiser at analyse fungerer
4. Sjekk at resultatene vises korrekt

### 4. Sjekk Logs

Hvis noe ikke fungerer:

1. **Azure Portal** → Function App → `pdf-ai-functions` → Logs
2. **GitHub Actions** → Se deployment logs
3. **Browser Console** → F12 → Console tab

## 🔍 Feilsøking

### Frontend kan ikke nå API

- Sjekk at Azure Functions kjører på `http://localhost:7071`
- Sjekk proxy-innstillinger i `vite.config.js`
- Sjekk at CORS er konfigurert i `function_app.py`

### API feiler med "configuration missing"

- Sjekk at `local.settings.json` eksisterer i `api/` mappen
- Verifiser at alle environment variabler er satt
- Sjekk at verdiene er riktige (ingen ekstra mellomrom)

### Azure OpenAI feiler

- Verifiser at `AI_FOUNDRY_ENDPOINT` er riktig
- Sjekk at `AI_FOUNDRY_API_KEY` er korrekt
- Verifiser at `AI_FOUNDRY_MODEL` matcher deployment-navnet

### Storage feiler

- Sjekk at `AZURE_STORAGE_CONNECTION_STRING` er riktig
- Verifiser at container "pdf-uploads" eksisterer

## 📝 Test Checklist

### Lokal Testing
- [ ] Frontend starter uten feil
- [ ] Backend starter uten feil
- [ ] Kan laste opp PDF fil
- [ ] Kan laste opp TXT fil
- [ ] Analyse fungerer
- [ ] Resultater vises korrekt

### Produksjon Testing
- [ ] Deployment er vellykket
- [ ] Produksjons-URL fungerer
- [ ] Kan laste opp filer
- [ ] Analyse fungerer i produksjon
- [ ] Ingen feil i browser console
- [ ] Ingen feil i Azure Functions logs

## 🚀 Quick Start

For rask lokal testing:

```bash
# Terminal 1 - Backend
cd api
# Først: Kopier local.settings.json.example til local.settings.json og fyll inn verdiene
cp local.settings.json.example local.settings.json
# Rediger local.settings.json med dine faktiske verdier
func start

# Terminal 2 - Frontend  
cd frontend
npm install  # Hvis ikke allerede gjort
npm run dev
```

Åpne `http://localhost:5173` i nettleseren.

## 📋 Opprett local.settings.json

1. Kopier eksempel-filen:
   ```bash
   cd api
   cp local.settings.json.example local.settings.json
   ```

2. Rediger `local.settings.json` og fyll inn dine faktiske verdier:
   - `DOC_INTELLIGENCE_ENDPOINT` og `DOC_INTELLIGENCE_KEY` fra Azure Portal
   - `AI_FOUNDRY_ENDPOINT`: `https://lillw-mkwnaj9t-eastus2.cognitiveservices.azure.com/`
   - `AI_FOUNDRY_API_KEY`: Din API-nøkkel
   - `AI_FOUNDRY_MODEL`: `gpt-4o-mini`
   - `AZURE_STORAGE_CONNECTION_STRING`: Din storage connection string
