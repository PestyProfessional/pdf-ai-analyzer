# Guide: Oppdater GitHub Secrets for Azure AI Foundry

Denne guiden viser deg nøyaktig hva som må oppdateres i GitHub Secrets når du migrerer fra Azure OpenAI til Azure AI Foundry.

## 🔄 Secrets som må OPPDATERES

### 1. Fjern gamle Azure OpenAI Secrets

Følgende secrets skal **SLETTES** fra GitHub (de brukes ikke lenger):

- ❌ `OPENAI_ENDPOINT` - **SLETT**
- ❌ `OPENAI_API_KEY` - **SLETT**

### 2. Legg til nye Azure AI Foundry Secrets

Følgende secrets skal **OPPRETTES** i GitHub:

- ✅ `AI_FOUNDRY_ENDPOINT` - **NY**
- ✅ `AI_FOUNDRY_API_KEY` - **NY**
- ✅ `AI_FOUNDRY_MODEL` - **NY**

## 📝 Steg-for-steg Instruksjoner

### Steg 1: Gå til GitHub Secrets

1. Gå til ditt GitHub repository
2. Klikk på **Settings** (øverst i repository)
3. I venstre meny, klikk på **Secrets and variables** → **Actions**
4. Du vil nå se alle eksisterende secrets

### Steg 2: Slett gamle OpenAI Secrets

1. Finn `OPENAI_ENDPOINT` i listen
2. Klikk på den
3. Klikk på **Delete** og bekreft
4. Gjenta for `OPENAI_API_KEY`

### Steg 3: Legg til nye Azure AI Foundry Secrets

#### 3.1 Legg til AI_FOUNDRY_ENDPOINT

1. Klikk på **New repository secret** (øverst til høyre)
2. **Name**: `AI_FOUNDRY_ENDPOINT`
3. **Secret**: `https://<resource-name>.services.ai.azure.com`
   - Erstatt `<resource-name>` med navnet på din Azure AI Foundry resource
   - Eksempel: `https://myfoundry.services.ai.azure.com`
4. Klikk **Add secret**

#### 3.2 Legg til AI_FOUNDRY_API_KEY

1. Klikk på **New repository secret**
2. **Name**: `AI_FOUNDRY_API_KEY`
3. **Secret**: Din Azure AI Foundry API-nøkkel
   - Finn denne i Azure Portal → Azure AI Foundry resource → Keys and Endpoint
   - Kopier Key 1 eller Key 2
4. Klikk **Add secret**

#### 3.3 Legg til AI_FOUNDRY_MODEL

1. Klikk på **New repository secret**
2. **Name**: `AI_FOUNDRY_MODEL`
3. **Secret**: Navnet på din model deployment
   - Dette er navnet du ga modellen da du deployet den
   - Eksempler: `gpt-4o-mini`, `mistral-large`, `llama-3-70b`
   - Standard: `gpt-4o-mini`
4. Klikk **Add secret**

### Steg 4: Verifiser at alle secrets er satt

Etter oppdatering skal du ha følgende secrets:

✅ **Behold disse (ikke endre):**
- `AZURE_STATIC_WEB_APPS_API_TOKEN`
- `DOC_INTELLIGENCE_ENDPOINT`
- `DOC_INTELLIGENCE_KEY`
- `AZURE_STORAGE_CONNECTION_STRING`
- `AZURE_STORAGE_ACCOUNT_KEY` (hvis du har denne)
- `AZUREWEBJOBSSTORAGE` (hvis du har denne)
- `GITHUB_TOKEN` (automatisk, ikke endre)

✅ **Nye secrets:**
- `AI_FOUNDRY_ENDPOINT`
- `AI_FOUNDRY_API_KEY`
- `AI_FOUNDRY_MODEL`

❌ **Fjernet:**
- `OPENAI_ENDPOINT` (slettet)
- `OPENAI_API_KEY` (slettet)

## 🔍 Hvor finner jeg verdiene?

### AI_FOUNDRY_ENDPOINT

1. Gå til [Azure Portal](https://portal.azure.com)
2. Finn din **Azure AI Foundry** resource
3. Gå til **Keys and Endpoint**
4. Kopier **Endpoint** (f.eks. `https://myfoundry.services.ai.azure.com`)

### AI_FOUNDRY_API_KEY

1. I samme **Keys and Endpoint** side
2. Kopier **Key 1** eller **Key 2**
3. Dette er din API-nøkkel

### AI_FOUNDRY_MODEL

1. Gå til [Microsoft Foundry Portal](https://ai.azure.com)
2. Gå til ditt prosjekt
3. Gå til **Deployments** eller **Models**
4. Se navnet på din deployede modell
5. Dette er modell-navnet (f.eks. `gpt-4o-mini`)

## ✅ Verifisering

Etter at du har oppdatert secrets:

1. Gå til **Actions** i GitHub repository
2. Trigger en ny deployment (push til main branch eller manuell trigger)
3. Sjekk at deployment kjører uten feil
4. Test at dokumentanalyse fungerer i applikasjonen

## 🚨 Feilsøking

### "Secret not found" feil

- Sjekk at secret-navnet er nøyaktig riktig (case-sensitive)
- Sjekk at du har lagt til secret i riktig repository

### "Authentication failed" feil

- Verifiser at `AI_FOUNDRY_API_KEY` er korrekt
- Sjekk at API-nøkkelen ikke er utløpt
- Prøv å regenerere API-nøkkelen i Azure Portal

### "Model not found" feil

- Sjekk at `AI_FOUNDRY_MODEL` matcher eksakt med deployment-navnet
- Verifiser at modellen faktisk er deployet i Azure AI Foundry
- Sjekk at modell-navnet ikke har ekstra mellomrom eller tegn

### "Endpoint not found" feil

- Sjekk at `AI_FOUNDRY_ENDPOINT` er riktig format
- Endpoint skal være: `https://<resource-name>.services.ai.azure.com`
- Ikke inkluder `/models` i endpoint (koden legger til dette automatisk)

## 📋 Checkliste

Før du starter deployment, sjekk at:

- [ ] Gamle `OPENAI_ENDPOINT` secret er slettet
- [ ] Gammel `OPENAI_API_KEY` secret er slettet
- [ ] Ny `AI_FOUNDRY_ENDPOINT` secret er opprettet
- [ ] Ny `AI_FOUNDRY_API_KEY` secret er opprettet
- [ ] Ny `AI_FOUNDRY_MODEL` secret er opprettet
- [ ] Alle verdiene er riktige (ingen ekstra mellomrom)
- [ ] Azure AI Foundry resource eksisterer og modell er deployet
- [ ] GitHub Actions workflow er oppdatert (allerede gjort i koden)

## 📞 Trenger du hjelp?

Hvis du støter på problemer:

1. Sjekk GitHub Actions logs for spesifikke feilmeldinger
2. Verifiser at alle secrets er satt riktig
3. Test Azure AI Foundry endpoint manuelt med API-nøkkelen
4. Sjekk at modellen er deployet og tilgjengelig
