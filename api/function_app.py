import azure.functions as func
import logging
import json
import os
import io
from azure.storage.blob import BlobServiceClient
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
import openai
from azure.identity import DefaultAzureCredential
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
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        blob_name = f"{file_id}/{file.filename}"
        
        # Upload to Azure Blob Storage
        blob_service_client, _ = get_clients()
        blob_client = blob_service_client.get_blob_client(
            container="pdf-uploads", 
            blob=blob_name
        )
        
        file_content = file.read()
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
        
        # Extract text based on file type
        filename = doc_blob.name.lower()
        if filename.endswith('.txt') or filename.endswith('.csv'):
            # For text files, directly use content
            extracted_text = blob_data.decode('utf-8')
        elif filename.endswith('.pdf'):
            # Use Document Intelligence for PDFs
            poller = doc_client.begin_analyze_document("prebuilt-read", blob_data)
            result = poller.result()
            
            # Extract text content
            extracted_text = ""
            for page in result.pages:
                for line in page.lines:
                    extracted_text += line.content + "\n"
        else:
            # For DOC/DOCX files, try Document Intelligence
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
        
        # Analyze with Azure OpenAI / Azure AI Foundry
        # Supports both Azure OpenAI and Azure AI Foundry endpoints
        ai_foundry_endpoint = os.getenv('AI_FOUNDRY_ENDPOINT')
        ai_foundry_api_key = os.getenv('AI_FOUNDRY_API_KEY')
        # Default model - kan overstyres med environment variable
        # Vanlige navn: gpt-4o-mini, gpt-4o, gpt-35-turbo
        ai_foundry_model = os.getenv('AI_FOUNDRY_MODEL', 'gpt-4o-mini')
        
        if not ai_foundry_endpoint or not ai_foundry_api_key:
            return func.HttpResponse(
                json.dumps({"error": "Azure AI configuration missing. Please set AI_FOUNDRY_ENDPOINT and AI_FOUNDRY_API_KEY"}),
                status_code=500,
                mimetype="application/json"
            )
        
        # Handle different endpoint formats
        endpoint = ai_foundry_endpoint.rstrip('/')
        
        # Use Azure OpenAI SDK with latest API version
        # Supports various endpoint formats:
        # - https://<resource>.cognitiveservices.azure.com/
        # - https://<resource>.openai.azure.com/
        # - https://<region>.api.cognitive.microsoft.com/
        # - https://<resource>.services.ai.azure.com/
        
        if 'cognitiveservices.azure.com' in endpoint or 'openai.azure.com' in endpoint:
            # Direct Azure OpenAI/Cognitive Services endpoint
            openai_client = openai.AzureOpenAI(
                api_key=ai_foundry_api_key,
                api_version="2024-12-01-preview",  # Latest API version
                azure_endpoint=endpoint
            )
        elif 'api.cognitive.microsoft.com' in endpoint:
            # Regional endpoint - construct resource-specific endpoint
            # For regional endpoints, we may need the full resource endpoint
            # Try to use as-is first, or construct from resource name
            resource_name = os.getenv('AI_FOUNDRY_RESOURCE_NAME', 'pdf-ai-openai-eastus')
            # If it's a regional endpoint, try to construct full endpoint
            if 'eastus' in endpoint.lower() or 'eastus2' in endpoint.lower():
                # Try to use the endpoint as provided, or construct
                endpoint = endpoint  # Use as provided
            openai_client = openai.AzureOpenAI(
                api_key=ai_foundry_api_key,
                api_version="2024-12-01-preview",
                azure_endpoint=endpoint
            )
        elif 'services.ai.azure.com' in endpoint:
            # Azure AI Foundry format - add /models if not present
            if not endpoint.endswith('/models'):
                endpoint = f"{endpoint}/models"
            # Use OpenAI SDK with custom base_url for Azure AI Foundry
            openai_client = openai.OpenAI(
                api_key=ai_foundry_api_key,
                base_url=f"{endpoint}/openai/deployments/{ai_foundry_model}"
            )
        else:
            # Default: try Azure OpenAI format with latest API version
            openai_client = openai.AzureOpenAI(
                api_key=ai_foundry_api_key,
                api_version="2024-12-01-preview",
                azure_endpoint=endpoint
            )
        
        # Create analysis prompt
        system_prompt = """Du er en AI-assistent som analyserer dokumenter for Dagens Næringsliv. 
        Analyser det oppgitte dokumentet og gi NØYAKTIG følgende struktur:

        **KORT SAMMENDRAG (5-8 punkter):**
        - [Punkt 1]
        - [Punkt 2] 
        - [Punkt 3]
        - [Punkt 4]
        - [Punkt 5]
        - [Punkt 6 hvis relevant]
        - [Punkt 7 hvis relevant]
        - [Punkt 8 hvis relevant]

        **NØKKELINFORMASJON:**
        Personer: [Liste opp alle navngitte personer]
        Selskaper: [Liste opp alle navngitte selskaper/organisasjoner]
        Offentlige etater: [Liste opp alle offentlige institusjoner]
        Tidsperiode: [Spesifiser hvilken tidsperiode dokumentet gjelder]

        **MULIGE RØDE FLAGG:**
        - Uvanlige formuleringer: [Noter spesielle eller mistenkelige formuleringer]
        - Avvik og kritikk: [Identifiser kritikkpunkter eller avvik]
        - Økonomiske størrelser: [Fremhev alle økonomiske tall, budsjettoverskridelser, tap]
        - Varsler og manglende svar: [Noter hvis noe mangler eller virker uklart]
        - Andre røde flagg: [Andre bekymringsfulle elementer]
        
        Svar på norsk, vær objektiv og detaljert."""
        
        user_prompt = f"Analyser følgende dokument:\n\n{extracted_text[:20000]}"  # Increased text length for larger documents
        
        # Use OpenAI SDK to call the model
        # Matches Azure OpenAI format: model parameter should be deployment name
        response = openai_client.chat.completions.create(
            model=ai_foundry_model,  # Model deployment name (e.g., "gpt-4o-mini")
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=2000,  # Increased tokens for more detailed analysis
            temperature=0.3
        )
        
        ai_analysis = response.choices[0].message.content
        
        # Parse the structured AI response
        lines = ai_analysis.split('\n')
        summary_points = []
        key_info = {}
        red_flags = []
        current_section = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Identify sections
            if "**KORT SAMMENDRAG" in line or "sammendrag" in line.lower():
                current_section = "summary"
                continue
            elif "**NØKKELINFORMASJON" in line or "nøkkelinformasjon" in line.lower():
                current_section = "info"
                continue
            elif "**MULIGE RØDE FLAGG" in line or "røde flagg" in line.lower():
                current_section = "flags"
                continue
            
            # Parse content based on section
            if current_section == "summary" and line.startswith('-'):
                summary_points.append(line.lstrip('-• ').strip())
            elif current_section == "info":
                if "Personer:" in line:
                    key_info["personer"] = line.replace("Personer:", "").strip()
                elif "Selskaper:" in line:
                    key_info["selskaper"] = line.replace("Selskaper:", "").strip()
                elif "Offentlige etater:" in line:
                    key_info["etater"] = line.replace("Offentlige etater:", "").strip()
                elif "Tidsperiode:" in line:
                    key_info["tidsperiode"] = line.replace("Tidsperiode:", "").strip()
            elif current_section == "flags" and line.startswith('-'):
                red_flags.append(line.lstrip('-• ').strip())
        
        # Create formatted summary and key points for frontend
        summary = " ".join(summary_points[:3]) if summary_points else "Kunne ikke generere sammendrag"
        key_points = summary_points + [f"Nøkkelinfo: {info}" for info in key_info.values() if info] + [f"Rødt flagg: {flag}" for flag in red_flags[:3]]
        
        # Fallback if parsing fails
        if not summary:
            summary = "Dokumentet har blitt analysert med AI."
        if not key_points:
            key_points = ["Dokumentanalyse ferdig", "Se full tekst for detaljer"]
        
        # Keep file for potential re-analysis or user access
        # blob_client.delete_blob()  # Commented out - keep files
        
        return func.HttpResponse(
            json.dumps({
                "summary": summary,
                "key_points": key_points[:8],  # Increased to show more details
                "confidence": 0.85,
                "full_analysis": ai_analysis,  # Include full structured analysis
                "extracted_text": extracted_text[:1000] + "..." if len(extracted_text) > 1000 else extracted_text
            }),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"Analysis error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Analysis failed: {str(e)}"}),
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