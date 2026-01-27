# DN AI Dokumentanalyse

Formell og profesjonell løsning for Dagens Næringsliv som automatiserer dokumentanalyse. Brukeren laster opp dokumenter og mottar en strukturert oppsummering, nøkkelinformasjon og mulige røde flagg – raskt og konsistent.

## Kort arkitekturbeskrivelse

- **Frontend**: React, Material UI og Vite for et strømlinjeformet brukergrensesnitt med opplasting, status og resultater.
- **Backend**: Azure Functions (Python) med to HTTP‑endepunkter: `POST /api/upload` og `POST /api/analyze/{file_id}`.
- **Lagring**: Azure Blob Storage (container `pdf-uploads`) for sikre opplastinger.
- **Tekstekstraksjon**: Azure AI Document Intelligence (`prebuilt-read`) for PDF/DOC/DOCX, direkte lesing for TXT/CSV.
- **Analyse**: Azure AI Foundry (eller Azure OpenAI‑kompatibelt endpoint) via `ChatCompletionsClient`.

## Hvordan KI brukes

- Etter opplasting hentes filen fra Blob Storage og tekst ekstraheres.
- En fast prompt instruerer modellen til å returnere:
  - **Kort sammendrag (5–8 punkter)**
  - **Nøkkelinformasjon** (personer, selskaper, etater, tidsperiode)
  - **Mulige røde flagg**
- Resultatet parses og presenteres i UI som sammendrag og hovedpunkter, med valgfri detaljert analyse.

## Nylig implementerte forbedringer

### ✅ Forbedret chunking og tekstbehandling
- **Smart chunking**: Erstatter 20k-tegngrensen med intelligent deling av dokumenter (7k tegn per chunk, 500 tegn overlapp)
- **Map-reduce**: Store dokumenter analyseres i deler og resultater syntetiseres for full dekning
- **Strukturbevarelse**: Bruk av `prebuilt-layout` for tabeller og dokumentstruktur

### ✅ Strukturert JSON-utdata
- **Konsistent format**: Erstatter markdown-parsing med direkte JSON-respons fra AI
- **Bedre pålitelighet**: Fallback-håndtering når JSON-parsing feiler

### ✅ Sikkerhetstiltak
- **Filstørrelsekontroll**: Maks 50MB per fil
- **Innholdvalidering**: Sjekk for tomme filer og gyldig innhold
- **Filtypebegrensning**: Kun tillatte filtyper aksepteres

### ✅ Kostnadskontroll
- **Konfigurerbare grenser**: `MAX_DOCUMENT_CHARS` (100k) og `MAX_CHUNKS` (15)
- **Smart begrensning**: Stopper prosessering ved grensene for å kontrollere kostnader

### ✅ Forbedret arkitektur
- **Ren AI Foundry-integrasjon**: Fjernet Azure OpenAI-konflikter
- **Bedre feilhåndtering**: Strukturert error-respons og logging

## Gjenstående begrensninger

- **Autentisering**: Endepunktene bruker anonym tilgang (prototype-nivå)
- **Rate limiting**: Ingen begrensning på antall requests per bruker
- **Avansert OCR**: Kan fortsatt miste kvalitet på komplekse dokumenter
- **Språkstøtte**: Primært optimalisert for norsk tekst

## Tekniske detaljer

### Miljøkonfigurasjon
```bash
# Påkrevd
AI_FOUNDRY_ENDPOINT=https://lillw-mkwnaj9t-eastus2.services.ai.azure.com/models
AI_FOUNDRY_API_KEY=<api-key>
AI_FOUNDRY_MODEL=gpt-4o-mini
DOC_INTELLIGENCE_ENDPOINT=<endpoint>
DOC_INTELLIGENCE_KEY=<key>
AZURE_STORAGE_CONNECTION_STRING=<connection-string>

# Valgfri (kostnadskontroll)
MAX_DOCUMENT_CHARS=100000
MAX_CHUNKS=15
```

### Deployment
- **Frontend**: Azure Static Web Apps via GitHub Actions  
- **Backend**: Azure Functions Python runtime
- **URL**: https://brave-ground-0673aca03.6.azurestaticapps.net

### Infrastruktur-requirements
- **Azure Storage Container**: Må opprette container `pdf-uploads` i Blob Storage før første kjøring
- **Azure AI Document Intelligence**: Service må være opprettet med korrekt endpoint og nøkkel
- **Azure AI Foundry**: Deployment med modell `lillw-mkwnaj9t-eastus2` må være tilgjengelig
