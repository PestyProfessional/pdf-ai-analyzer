import azure.functions as func
import logging
import json
import os
import io
from azure.storage.blob import BlobServiceClient
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.inference import ChatCompletionsClient
from azure.identity import DefaultAzureCredential
import uuid

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
            # Try Document Intelligence Read first (cheaper/faster), fallback to Layout if needed
            try:
                poller = doc_client.begin_analyze_document("prebuilt-read", blob_data)
                result = poller.result()
                
                # Simple text extraction
                extracted_text = ""
                for page_num, page in enumerate(result.pages):
                    if page_num > 0:
                        extracted_text += f"\n--- Side {page_num + 1} ---\n"
                    
                    for line in page.lines:
                        extracted_text += line.content + "\n"
                
                # Check if we should fallback to layout analysis for better structure
                # Simple heuristic: if document seems to have many short lines (potential tables)
                lines = extracted_text.split('\n')
                short_lines = sum(1 for line in lines if len(line.strip()) < 20 and len(line.strip()) > 0)
                if short_lines > len(lines) * 0.3:  # More than 30% short lines
                    logging.info("Document appears to have tables, using layout analysis")
                    raise Exception("Fallback to layout")
                    
            except:
                # Fallback to layout analysis for better structure preservation
                logging.info("Using layout analysis for better structure preservation")
                poller = doc_client.begin_analyze_document("prebuilt-layout", blob_data)
                result = poller.result()
                
                # Group tables by page to avoid duplication
                tables_by_page = {}
                if hasattr(result, 'tables') and result.tables:
                    for table in result.tables:
                        if hasattr(table, 'bounding_regions') and table.bounding_regions:
                            page_num = table.bounding_regions[0].page_number
                            if page_num not in tables_by_page:
                                tables_by_page[page_num] = []
                            tables_by_page[page_num].append(table)
                
                # Extract text content with preserved structure
                extracted_text = ""
                for page_num, page in enumerate(result.pages):
                    current_page = page_num + 1
                    if page_num > 0:
                        extracted_text += f"\n--- Side {current_page} ---\n"
                    
                    # Add tables for this page
                    if current_page in tables_by_page:
                        for table in tables_by_page[current_page]:
                            extracted_text += "\n[TABELL]\n"
                            for cell in table.cells:
                                extracted_text += f"{cell.content}\t"
                                if cell.column_index == table.column_count - 1:
                                    extracted_text += "\n"
                            extracted_text += "[/TABELL]\n\n"
                    
                    # Add regular text content
                    for line in page.lines:
                        extracted_text += line.content + "\n"
        else:
            # For DOC/DOCX files, try Document Intelligence Read first, then Layout if needed
            try:
                # Try basic read first
                poller = doc_client.begin_analyze_document("prebuilt-read", blob_data)
                result = poller.result()
                
                extracted_text = ""
                for page_num, page in enumerate(result.pages):
                    if page_num > 0:
                        extracted_text += f"\n--- Side {page_num + 1} ---\n"
                    
                    for line in page.lines:
                        extracted_text += line.content + "\n"
                
                # Check if layout analysis might be beneficial
                lines = extracted_text.split('\n')
                short_lines = sum(1 for line in lines if len(line.strip()) < 20 and len(line.strip()) > 0)
                if short_lines > len(lines) * 0.3:
                    raise Exception("Fallback to layout for better structure")
                    
            except Exception as structure_error:
                logging.warning(f"Attempting layout analysis for better structure: {structure_error}")
                try:
                    # Fallback to layout analysis
                    poller = doc_client.begin_analyze_document("prebuilt-layout", blob_data)
                    result = poller.result()
                    
                    # Group tables by page
                    tables_by_page = {}
                    if hasattr(result, 'tables') and result.tables:
                        for table in result.tables:
                            if hasattr(table, 'bounding_regions') and table.bounding_regions:
                                page_num = table.bounding_regions[0].page_number
                                if page_num not in tables_by_page:
                                    tables_by_page[page_num] = []
                                tables_by_page[page_num].append(table)
                    
                    extracted_text = ""
                    for page_num, page in enumerate(result.pages):
                        current_page = page_num + 1
                        if page_num > 0:
                            extracted_text += f"\n--- Side {current_page} ---\n"
                        
                        # Add tables for this page
                        if current_page in tables_by_page:
                            for table in tables_by_page[current_page]:
                                extracted_text += "\n[TABELL]\n"
                                for cell in table.cells:
                                    extracted_text += f"{cell.content}\t"
                                    if cell.column_index == table.column_count - 1:
                                        extracted_text += "\n"
                                extracted_text += "[/TABELL]\n\n"
                        
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
                
                if break_point > 0 and break_point > max_chunk_size * 0.7:  # Good break point found
                    chunks.append(text[start:start + break_point + 1])
                    start = start + break_point + 1 - overlap
                else:  # No good break point, use max size
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
        ai_foundry_model = os.getenv('AI_FOUNDRY_MODEL', 'lillw-mkwnaj9t-eastus2')
        
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
                
                chunk_system = "Du analyserer dokumenter for Dagens Næringsliv. Returner KUN gyldig JSON uten markdown eller kommentarer."
                chunk_user = f"""Analyser denne delen av et større dokument.

JSON format:
{{
  "sammendrag": ["Viktige punkter fra denne delen"],
  "nøkkelinformasjon": {{
    "personer": ["Personer nevnt"], "selskaper": ["Selskaper nevnt"], 
    "offentlige_etater": ["Etater nevnt"], "tidsperiode": "Tidsinfo"
  }},
  "røde_flagg": {{
    "uvanlige_formuleringer": [], "avvik_og_kritikk": [], "økonomiske_størrelser": [],
    "varsler_og_mangler": [], "andre_røde_flagg": []
  }}
}}

Del {i+1}/{len(text_chunks)}:
{chunk}"""
                
                try:
                    response = ai_client.complete(
                        model=ai_foundry_model,
                        messages=[
                            {"role": "system", "content": chunk_system},
                            {"role": "user", "content": chunk_user}
                        ],
                        max_tokens=1500,
                        temperature=0.3
                    )
                    chunk_analyses.append(response.choices[0].message.content)
                except Exception as api_error:
                    logging.error(f"Feil ved analyse av chunk {i+1}: {api_error}")
                    chunk_analyses.append('{"sammendrag": ["Kunne ikke analysere denne delen"], "nøkkelinformasjon": {"personer": [], "selskaper": [], "offentlige_etater": [], "tidsperiode": ""}, "røde_flagg": {"uvanlige_formuleringer": [], "avvik_og_kritikk": [], "økonomiske_størrelser": [], "varsler_og_mangler": [], "andre_røde_flagg": []}}')
            
            # Step 2: Synthesize all chunk analyses
            synthesis_system = "Du syntetiserer dokumentanalyser for Dagens Næringsliv. Returner KUN gyldig JSON uten markdown."
            synthesis_user = f"""Kombiner disse {len(text_chunks)} delanalysene til en komplett analyse.

JSON format:
{{
  "sammendrag": ["5-8 hovedpunkter fra hele dokumentet"],
  "nøkkelinformasjon": {{
    "personer": ["Alle personer"], "selskaper": ["Alle selskaper"], 
    "offentlige_etater": ["Alle etater"], "tidsperiode": "Samlet periode"
  }},
  "røde_flagg": {{
    "uvanlige_formuleringer": [], "avvik_og_kritikk": [], "økonomiske_størrelser": [],
    "varsler_og_mangler": [], "andre_røde_flagg": []
  }}
}}

Delanalyser:
{chr(10).join([f"Del {i+1}: {analysis}" for i, analysis in enumerate(chunk_analyses)])}"""
            
            try:
                response = ai_client.complete(
                    model=ai_foundry_model,
                    messages=[
                        {"role": "system", "content": synthesis_system},
                        {"role": "user", "content": synthesis_user}
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
        
        # Parse JSON response with repair attempt
        try:
            analysis_data = json.loads(ai_analysis)
        except json.JSONDecodeError as json_error:
            logging.warning(f"Første JSON parsing feil: {json_error}, prøver reparasjon")
            # Try JSON repair
            try:
                repair_system = "Du reparerer ugyldig JSON. Returner KUN gyldig JSON, ingen forklaringer eller markdown."
                repair_user = f"Reparer denne JSON til gyldig format:\n{ai_analysis}"
                
                repair_response = ai_client.complete(
                    model=ai_foundry_model,
                    messages=[
                        {"role": "system", "content": repair_system},
                        {"role": "user", "content": repair_user}
                    ],
                    max_tokens=1500,
                    temperature=0.1
                )
                
                repaired_json = repair_response.choices[0].message.content
                analysis_data = json.loads(repaired_json)
                logging.info("JSON reparasjon suksessful")
                
            except Exception as repair_error:
                logging.error(f"JSON reparasjon feilet: {repair_error}")
                # Final fallback to simple response
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