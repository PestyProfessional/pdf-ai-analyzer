# DN AI Dokumentanalyse (prototype)

Prototype for automatisert dokumentanalyse rettet mot redaksjonelle arbeidsflyter hos Dagens Næringsliv.  
Løsningen gjør det mulig å laste opp dokumenter og få en rask, strukturert oversikt med sammendrag, nøkkelinformasjon og mulige røde flagg ved hjelp av Azure-basert AI.

## Arkitektur (oversikt)

- **Frontend**: React + Vite med Material UI for opplasting, status og visning av analyseresultater  
- **Backend**: Azure Functions (Python) med HTTP-endepunktene  
  - `POST /api/upload`  
  - `POST /api/analyze/{file_id}`  
- **Lagring**: Azure Blob Storage (`pdf-uploads`) for midlertidig lagring av opplastede dokumenter  
- **Tekstekstraksjon**: Azure AI Document Intelligence  
  - `prebuilt-read` for PDF/DOC/DOCX  
  - Direkte lesing for TXT/CSV  
  - Automatisk fallback til `prebuilt-layout` ved tabeller og kompleks struktur  
- **Språkanalyse**: GPT-4o-mini via Azure OpenAI, konsumert gjennom Azure AI Foundry sitt inference-endepunkt  

## Hvordan løsningen fungerer

1. Bruker laster opp et dokument via frontend  
2. Filen lagres i Blob Storage og tekst ekstraheres  
3. Dokumentet deles automatisk opp i mindre tekstbiter ved behov (chunking)  
4. Hver del analyseres av språkmodellen, og resultatene samles til én helhetlig analyse  
5. Frontend mottar både et kort sammendrag og en strukturert analyse i JSON-format  

## Output fra AI

Modellen instrueres til å returnere strukturert JSON med:

- **Sammendrag** (5–8 punkter)  
- **Nøkkelinformasjon**
  - Personer  
  - Selskaper  
  - Offentlige etater  
  - Tidsperiode  
- **Mulige røde flagg**
  - Uvanlige formuleringer  
  - Kritikk og avvik  
  - Økonomiske tall  
  - Manglende eller uklare opplysninger  

## Viktige tekniske valg

- **Chunking + map-reduce** for å håndtere store dokumenter uten å sprenge token-grenser  
- **Strukturert JSON-output** i stedet for fri tekst for enklere viderebruk  
- **Kostnadskontroll** via eksplisitte grenser på dokumentstørrelse og antall chunks  
- **Robusthet**: Automatisk reparasjon av ugyldig JSON fra modellen  

## Begrensninger i prototypen

- Ingen autentisering eller rate limiting  
- OCR-kvalitet avhenger av dokumentets struktur og kvalitet  
- Primært optimalisert for norsk språk  

## Konfigurasjon

```bash
# Påkrevd
AI_FOUNDRY_ENDPOINT=https://lillw-mkwnaj9t-eastus2.services.ai.azure.com/models
AI_FOUNDRY_API_KEY=<api-key>
AI_FOUNDRY_MODEL=gpt-4o-mini
DOC_INTELLIGENCE_ENDPOINT=<endpoint>
DOC_INTELLIGENCE_KEY=<key>
AZURE_STORAGE_CONNECTION_STRING=<connection-string>

# Valgfritt (kostnadskontroll)
MAX_DOCUMENT_CHARS=100000
MAX_CHUNKS=15
