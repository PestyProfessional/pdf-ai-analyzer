import azure.functions as func
import logging
import json
import os
import io
from azure.storage.blob import BlobServiceClient
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
import uuid
import asyncio

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Azure service clients
blob_service_client = None
doc_client = None

def get_clients():
    global blob_service_client, doc_client
    
    if not blob_service_client:
        # Try connection string first, then account key, fallback to managed identity
        storage_connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING') or os.getenv('AzureWebJobsStorage')
        if storage_connection_string and storage_connection_string.strip():
            blob_service_client = BlobServiceClient.from_connection_string(storage_connection_string)
        else:
            # Try using account key
            account_key = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')
            if account_key:
                account_url = "https://pdfaianalyzernorway.blob.core.windows.net"
                blob_service_client = BlobServiceClient(
                    account_url=account_url, 
                    credential=account_key
                )
            else:
                # Fallback to managed identity
                account_url = "https://pdfaianalyzernorway.blob.core.windows.net"
                blob_service_client = BlobServiceClient(
                    account_url=account_url, 
                    credential=DefaultAzureCredential()
                )
    
    if not doc_client:
        # Document Intelligence client
        doc_intelligence_endpoint = os.getenv('DOC_INTELLIGENCE_ENDPOINT')
        doc_intelligence_key = os.getenv('DOC_INTELLIGENCE_KEY')
        doc_client = DocumentAnalysisClient(
            endpoint=doc_intelligence_endpoint,
            credential=AzureKeyCredential(doc_intelligence_key)
        )
    
    return blob_service_client, doc_client

@app.route(route="upload", methods=["POST"])
def upload_pdf(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('PDF upload function triggered.')
    
    try:
        # Get file from request
        files = req.files
        if 'file' not in files:
            return func.HttpResponse(
                json.dumps({"error": "No file provided"}),
                status_code=400,
                mimetype="application/json"
            )
        
        file = files['file']
        if file.filename == '':
            return func.HttpResponse(
                json.dumps({"error": "No file selected"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Validate file type
        allowed_extensions = ('.pdf', '.txt', '.csv', '.doc', '.docx')
        if not file.filename.lower().endswith(allowed_extensions):
            return func.HttpResponse(
                json.dumps({"error": "Only PDF, TXT, CSV, DOC, and DOCX files are allowed"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Security: Check file size (limit to 50MB)
        file_content = file.read()
        max_file_size = 50 * 1024 * 1024  # 50MB in bytes
        if len(file_content) > max_file_size:
            return func.HttpResponse(
                json.dumps({"error": f"File size too large. Maximum allowed size is {max_file_size // (1024*1024)}MB"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Security: Basic file content validation
        if len(file_content) == 0:
            return func.HttpResponse(
                json.dumps({"error": "Empty file not allowed"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        blob_name = f"{file_id}/{file.filename}"
        
        # Upload to Azure Blob Storage
        blob_service_client, _ = get_clients()
        blob_client = blob_service_client.get_blob_client(
            container="pdf-uploads", 
            blob=blob_name
        )
        
        blob_client.upload_blob(file_content, overwrite=True)
        
        return func.HttpResponse(
            json.dumps({
                "message": "File uploaded successfully",
                "file_id": file_id,
                "filename": file.filename
            }),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"Upload error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Upload failed: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="analyze/{file_id}", methods=["POST"])
def analyze_pdf(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('PDF analysis function triggered.')
    
    try:
        file_id = req.route_params.get('file_id')
        if not file_id:
            return func.HttpResponse(
                json.dumps({"error": "File ID required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Get blob from storage
        blob_service_client, doc_client = get_clients()
        
        # Find the document file in the blob storage
        container_client = blob_service_client.get_container_client("pdf-uploads")
        blobs = container_client.list_blobs(name_starts_with=file_id)
        
        doc_blob = None
        for blob in blobs:
            # Support all allowed file types
            allowed_extensions = ('.pdf', '.txt', '.csv', '.doc', '.docx')
            if blob.name.lower().endswith(allowed_extensions):
                doc_blob = blob
                break
        
        if not doc_blob:
            return func.HttpResponse(
                json.dumps({"error": "File not found"}),
                status_code=404,
                mimetype="application/json"
            )
        
        # Download blob content
        blob_client = blob_service_client.get_blob_client(
            container="pdf-uploads", 
            blob=doc_blob.name
        )
        blob_data = blob_client.download_blob().readall()
        
        # Extract text based on file type with improved structure preservation
        filename = doc_blob.name.lower()
        if filename.endswith('.txt') or filename.endswith('.csv'):
            # For text files, directly use content
            extracted_text = blob_data.decode('utf-8')
        elif filename.endswith('.pdf'):
            # Use Document Intelligence for PDFs with enhanced structure preservation
            poller = doc_client.begin_analyze_document("prebuilt-layout", blob_data)  # Use layout for better structure
            result = poller.result()
            
            # Extract text content with preserved structure
            extracted_text = ""
            for page_num, page in enumerate(result.pages):
                if page_num > 0:
                    extracted_text += f"\n--- Side {page_num + 1} ---\n"
                
                # Process tables first to maintain layout
                for table in result.tables:
                    if hasattr(table, 'bounding_regions') and table.bounding_regions:
                        for region in table.bounding_regions:
                            if region.page_number == page_num + 1:
                                extracted_text += "\n[TABELL]\n"
                                for cell in table.cells:
                                    extracted_text += f"{cell.content}\t"
                                    if cell.column_index == table.column_count - 1:
                                        extracted_text += "\n"
                                extracted_text += "[/TABELL]\n\n"
                
                # Then add regular text content
                for line in page.lines:
                    extracted_text += line.content + "\n"
        else:
            # For DOC/DOCX files, try Document Intelligence with layout
            try:
                poller = doc_client.begin_analyze_document("prebuilt-layout", blob_data)
                result = poller.result()
                
                extracted_text = ""
                for page_num, page in enumerate(result.pages):
                    if page_num > 0:
                        extracted_text += f"\n--- Side {page_num + 1} ---\n"
                    
                    # Process tables first
                    for table in result.tables:
                        if hasattr(table, 'bounding_regions') and table.bounding_regions:
                            for region in table.bounding_regions:
                                if region.page_number == page_num + 1:
                                    extracted_text += "\n[TABELL]\n"
                                    for cell in table.cells:
                                        extracted_text += f"{cell.content}\t"
                                        if cell.column_index == table.column_count - 1:
                                            extracted_text += "\n"
                                    extracted_text += "[/TABELL]\n\n"
                    
                    for line in page.lines:
                        extracted_text += line.content + "\n"
            except Exception as structure_error:
                logging.warning(f"Layout analysis failed, falling back to basic read: {structure_error}")
                # Fallback to basic read
                try:
                    poller = doc_client.begin_analyze_document("prebuilt-read", blob_data)
                    result = poller.result()
                    
                    extracted_text = ""
                    for page in result.pages:
                        for line in page.lines:
                            extracted_text += line.content + "\n"
                except:
                    extracted_text = "Kunne ikke lese dokument. Prøv med PDF eller TXT format."
        
        if not extracted_text.strip():
            return func.HttpResponse(
                json.dumps({"error": "No text could be extracted from the document"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Cost control: Limit total text size for analysis
        max_total_chars = int(os.getenv('MAX_DOCUMENT_CHARS', '100000'))  # Default 100k chars
        max_chunks = int(os.getenv('MAX_CHUNKS', '15'))  # Default 15 chunks max
        
        if len(extracted_text) > max_total_chars:
            logging.info(f"Document too large ({len(extracted_text)} chars), truncating to {max_total_chars}")
            extracted_text = extracted_text[:max_total_chars]
        
        # Chunking implementation for large documents
        def chunk_text(text, max_chunk_size=7000):
            """Split text into overlapping chunks for better analysis coverage"""
            if len(text) <= max_chunk_size:
                return [text]
            
            chunks = []
            overlap = 500  # Character overlap between chunks
            start = 0
            
            while start < len(text):
                end = start + max_chunk_size
                if end >= len(text):
                    chunks.append(text[start:])
                    break
                
                # Try to break at sentence boundary near the end
                chunk = text[start:end]
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > start + max_chunk_size * 0.7:  # If we found a good break point
                    chunks.append(text[start:start + break_point + 1])
                    start = start + break_point + 1 - overlap
                else:  # Otherwise break at max size
                    chunks.append(chunk)
                    start = end - overlap
                    
                # Cost control: Limit number of chunks
                if len(chunks) >= max_chunks:
                    logging.info(f"Reached maximum chunks limit ({max_chunks}), stopping chunking")
                    break
                    
            return chunks

        # Analyse med Azure AI Foundry
        ai_foundry_endpoint = os.getenv('AI_FOUNDRY_ENDPOINT')
        ai_foundry_api_key = os.getenv('AI_FOUNDRY_API_KEY')
        ai_foundry_model = os.getenv('AI_FOUNDRY_MODEL', 'gpt-4o-mini')
        
        if not ai_foundry_endpoint or not ai_foundry_api_key:
            return func.HttpResponse(
                json.dumps({"error": "Azure AI Foundry-konfigurasjon mangler. Sett AI_FOUNDRY_ENDPOINT og AI_FOUNDRY_API_KEY."}),
                status_code=500,
                mimetype="application/json"
            )
        
        endpoint = ai_foundry_endpoint.rstrip('/')
        if not endpoint.startswith('https://'):
            return func.HttpResponse(
                json.dumps({"error": f"Ugyldig endpoint: {endpoint}. Må starte med https://"}),
                status_code=500,
                mimetype="application/json"
            )
        
        if 'services.ai.azure.com' not in endpoint:
            return func.HttpResponse(
                json.dumps({"error": "Kun Azure AI Foundry endpoints (services.ai.azure.com) støttes."}),
                status_code=500,
                mimetype="application/json"
            )
        
        # AI Foundry format: https://<resource>.services.ai.azure.com/models
        if not endpoint.endswith('/models'):
            endpoint = f"{endpoint}/models"
        
        logging.info(f"Bruker Azure AI Foundry: {endpoint}, modell: {ai_foundry_model}")
        try:
            ai_client = ChatCompletionsClient(
                endpoint=endpoint,
                credential=AzureKeyCredential(ai_foundry_api_key)
            )
        except Exception as client_error:
            logging.error(f"Kunne ikke opprette AI Foundry-klient: {client_error}")
            raise Exception(f"Kunne ikke opprette Azure AI Foundry-klient: {str(client_error)}")
        
        # Process document in chunks if it's large
        text_chunks = chunk_text(extracted_text)
        logging.info(f"Dokument delt i {len(text_chunks)} chunks")
        
        if len(text_chunks) == 1:
            # Single chunk - direct analysis
            system_prompt = """Du er en AI-assistent som analyserer dokumenter for Dagens Næringsliv. 
Returner resultatet som gyldig JSON i følgende format:

{
  "sammendrag": ["Punkt 1", "Punkt 2", "Punkt 3", "Punkt 4", "Punkt 5"],
  "nøkkelinformasjon": {
    "personer": ["Person 1", "Person 2"],
    "selskaper": ["Selskap 1", "Selskap 2"],
    "offentlige_etater": ["Etat 1", "Etat 2"],
    "tidsperiode": "Beskrivelse av tidsperiode"
  },
  "røde_flagg": {
    "uvanlige_formuleringer": ["Formulering 1", "Formulering 2"],
    "avvik_og_kritikk": ["Kritikk 1", "Kritikk 2"],
    "økonomiske_størrelser": ["Beløp/tall 1", "Beløp/tall 2"],
    "varsler_og_mangler": ["Varsel 1", "Varsel 2"],
    "andre_røde_flagg": ["Flagg 1", "Flagg 2"]
  }
}

Analyser dokumentet objektivt og detaljert på norsk."""
            
            user_prompt = f"Analyser følgende dokument:\n\n{text_chunks[0]}"
            
            try:
                response = ai_client.complete(
                    model=ai_foundry_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=2000,
                    temperature=0.3
                )
                ai_analysis = response.choices[0].message.content
            except Exception as api_error:
                error_str = str(api_error)
                logging.error(f"AI Foundry-feil: {error_str}", exc_info=True)
                raise Exception(f"Azure AI Foundry feil: {error_str}")
                
        else:
            # Multiple chunks - map-reduce approach
            chunk_analyses = []
            
            # Step 1: Analyze each chunk
            for i, chunk in enumerate(text_chunks):
                logging.info(f"Analyserer chunk {i+1}/{len(text_chunks)}")
                
                chunk_prompt = f"""Analyser denne delen av et større dokument for Dagens Næringsliv.
Returner resultatet som gyldig JSON:

{{
  "sammendrag": ["Viktige punkter fra denne delen"],
  "nøkkelinformasjon": {{
    "personer": ["Personer nevnt i denne delen"],
    "selskaper": ["Selskaper nevnt i denne delen"],
    "offentlige_etater": ["Etater nevnt i denne delen"],
    "tidsperiode": "Tidsinfo fra denne delen"
  }},
  "røde_flagg": {{
    "uvanlige_formuleringer": ["Mistenkelige formuleringer"],
    "avvik_og_kritikk": ["Kritikk og avvik"],
    "økonomiske_størrelser": ["Tall og beløp"],
    "varsler_og_mangler": ["Mangler og varsler"],
    "andre_røde_flagg": ["Andre bekymringer"]
  }}
}}

Del {i+1} av {len(text_chunks)}:
{chunk}"""
                
                try:
                    response = ai_client.complete(
                        model=ai_foundry_model,
                        messages=[
                            {"role": "user", "content": chunk_prompt}
                        ],
                        max_tokens=1500,
                        temperature=0.3
                    )
                    chunk_analyses.append(response.choices[0].message.content)
                except Exception as api_error:
                    logging.error(f"Feil ved analyse av chunk {i+1}: {api_error}")
                    chunk_analyses.append('{"sammendrag": ["Kunne ikke analysere denne delen"], "nøkkelinformasjon": {}, "røde_flagg": {}}')
            
            # Step 2: Synthesize all chunk analyses
            synthesis_prompt = f"""Du har mottatt analyser av {len(text_chunks)} deler av et dokument for Dagens Næringsliv.
Kombiner og syntetiser disse analysene til en sammenhengende, komplett analyse.
Returner resultatet som gyldig JSON:

{{
  "sammendrag": ["5-8 hovedpunkter fra hele dokumentet"],
  "nøkkelinformasjon": {{
    "personer": ["Alle personer nevnt i dokumentet"],
    "selskaper": ["Alle selskaper nevnt i dokumentet"],
    "offentlige_etater": ["Alle etater nevnt i dokumentet"],
    "tidsperiode": "Samlet tidsperiode for dokumentet"
  }},
  "røde_flagg": {{
    "uvanlige_formuleringer": ["Alle mistenkelige formuleringer"],
    "avvik_og_kritikk": ["All kritikk og avvik"],
    "økonomiske_størrelser": ["Alle viktige tall og beløp"],
    "varsler_og_mangler": ["Alle mangler og varsler"],
    "andre_røde_flagg": ["Andre bekymringsfulle elementer"]
  }}
}}

Analyser fra delene:
{chr(10).join([f"Del {i+1}: {analysis}" for i, analysis in enumerate(chunk_analyses)])}"""
            
            try:
                response = ai_client.complete(
                    model=ai_foundry_model,
                    messages=[
                        {"role": "user", "content": synthesis_prompt}
                    ],
                    max_tokens=2500,
                    temperature=0.3
                )
                ai_analysis = response.choices[0].message.content
                logging.info("Map-reduce analyse fullført")
            except Exception as api_error:
                error_str = str(api_error)
                logging.error(f"Feil ved syntese: {error_str}", exc_info=True)
                raise Exception(f"Feil ved syntese av analyse: {error_str}")
        
        # Parse JSON response instead of markdown
        try:
            analysis_data = json.loads(ai_analysis)
        except json.JSONDecodeError as json_error:
            logging.error(f"JSON parsing feil: {json_error}, response: {ai_analysis}")
            # Fallback to simple response
            analysis_data = {
                "sammendrag": ["Dokumentet har blitt analysert"],
                "nøkkelinformasjon": {"personer": [], "selskaper": [], "offentlige_etater": [], "tidsperiode": ""},
                "røde_flagg": {"uvanlige_formuleringer": [], "avvik_og_kritikk": [], "økonomiske_størrelser": [], "varsler_og_mangler": [], "andre_røde_flagg": []}
            }
        
        # Create formatted output from structured JSON
        sammendrag_punkter = analysis_data.get("sammendrag", [])
        nøkkelinfo = analysis_data.get("nøkkelinformasjon", {})
        røde_flagg = analysis_data.get("røde_flagg", {})
        
        # Create summary from first 3 summary points
        summary = " ".join(sammendrag_punkter[:3]) if sammendrag_punkter else "Kunne ikke generere sammendrag"
        
        # Build key_points list from all structured data
        key_points = []
        
        # Add summary points
        key_points.extend(sammendrag_punkter[:5])
        
        # Add key information if available
        if nøkkelinfo.get("personer"):
            personer = nøkkelinfo["personer"]
            if isinstance(personer, list) and personer:
                key_points.append(f"Personer: {', '.join(personer[:3])}")
            elif isinstance(personer, str) and personer.strip():
                key_points.append(f"Personer: {personer}")
                
        if nøkkelinfo.get("selskaper"):
            selskaper = nøkkelinfo["selskaper"]
            if isinstance(selskaper, list) and selskaper:
                key_points.append(f"Selskaper: {', '.join(selskaper[:3])}")
            elif isinstance(selskaper, str) and selskaper.strip():
                key_points.append(f"Selskaper: {selskaper}")
        
        # Add red flags if found
        all_red_flags = []
        for category, flags in røde_flagg.items():
            if isinstance(flags, list):
                all_red_flags.extend(flags[:2])  # Limit per category
            elif isinstance(flags, str) and flags.strip():
                all_red_flags.append(flags)
        
        # Add red flags to key points
        for flag in all_red_flags[:3]:  # Limit total red flags
            key_points.append(f"Rødt flagg: {flag}")
        
        # Fallback if no data
        if not summary or not key_points:
            summary = "Dokumentet har blitt analysert med AI."
            key_points = ["Dokumentanalyse ferdig", "Se full tekst for detaljer"]
        
        # Keep file for potential re-analysis or user access
        # blob_client.delete_blob()  # Commented out - keep files
        
        return func.HttpResponse(
            json.dumps({
                "summary": summary,
                "key_points": key_points[:8],
                "confidence": 0.85,
                "full_analysis": ai_analysis,
                "structured_analysis": analysis_data,  # Include parsed JSON structure
                "chunks_processed": len(text_chunks),
                "extracted_text": extracted_text[:1000] + "..." if len(extracted_text) > 1000 else extracted_text
            }),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Analysis error: {error_msg}", exc_info=True)
        
        # Provide more helpful error messages
        if "Could not resolve host" in error_msg or "Connection" in error_msg:
            error_msg = "Kunne ikke koble til Azure AI-tjenesten. Sjekk nettverkstilkobling."
        elif "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower() or "401" in error_msg:
            error_msg = "Autentisering feilet. Sjekk at API-nøkkelen er korrekt."
        elif "model" in error_msg.lower() or "deployment" in error_msg.lower() or "404" in error_msg:
            error_msg = f"Modell ikke funnet. Sjekk at '{ai_foundry_model}' er riktig deployment-navn."
        elif "endpoint" in error_msg.lower():
            error_msg = "Endpoint-konfigurasjon feilet. Sjekk AI_FOUNDRY_ENDPOINT."
        
        return func.HttpResponse(
            json.dumps({"error": error_msg}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="health")
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint"""
    return func.HttpResponse(
        json.dumps({"status": "healthy", "service": "PDF AI Analyzer"}),
        status_code=200,
        mimetype="application/json"
    )