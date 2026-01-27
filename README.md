# DN AI Dokumentanalyse

Formell og profesjonell løsning for Dagens Næringsliv som automatiserer dokumentanalyse. Brukeren laster opp dokumenter og mottar en strukturert oppsummering, nøkkelinformasjon og mulige røde flagg – raskt og konsistent.

## Kort arkitekturbeskrivelse

- **Frontend**: React + Material UI (Vite) for et strømlinjeformet brukergrensesnitt med opplasting, status og resultater.
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

## Begrensninger i løsningen

- **Tekstgrense**: Kun de første ~20 000 tegnene sendes til modellen, som kan gi ufullstendig dekning av lange dokumenter.
- **Kvalitet av OCR**: Analysen avhenger av kvaliteten i Document Intelligence‑ekstraksjonen.
- **Ingen autentisering**: Endepunktene er satt til anonym tilgang.
- **Filhåndtering**: Opplastede filer blir liggende i Blob Storage (sletting er kommentert ut), selv om UI antyder automatisk sletting.
- **Validering**: Frontend tillater 50 MB og flere filtyper, mens backend kun sjekker filendelse (ikke innhold).

## Hva jeg ville forbedret med mer tid

- **Sikkerhet og tilgang**: Innføre autentisering/autorisasjon, rate limiting og bedre validering av filinnhold.
- **Databehandling**: Automatisk sletting/retensjonspolicy og presis brukerkommunikasjon om lagring.
- **Analyse**: Chunking av lange dokumenter og sammenslåing av resultater for full dekning.
- **Kvalitet**: Domene‑spesifikke prompt‑varianter og kontrollpunkter for høyere presisjon.
- **Observability**: Strukturert logging, korrelasjons‑ID og metrikker for drift og feilsøking.
