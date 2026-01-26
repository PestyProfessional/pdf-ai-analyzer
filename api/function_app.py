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
        # Use connection string for storage
        storage_connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING') or os.getenv('AzureWebJobsStorage')
        blob_service_client = BlobServiceClient.from_connection_string(storage_connection_string)
    
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
        if not file.filename.lower().endswith('.pdf'):
            return func.HttpResponse(
                json.dumps({"error": "Only PDF files are allowed"}),
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
        
        # Find the PDF file in the blob storage
        container_client = blob_service_client.get_container_client("pdf-uploads")
        blobs = container_client.list_blobs(name_starts_with=file_id)
        
        pdf_blob = None
        for blob in blobs:
            if blob.name.endswith('.pdf'):
                pdf_blob = blob
                break
        
        if not pdf_blob:
            return func.HttpResponse(
                json.dumps({"error": "File not found"}),
                status_code=404,
                mimetype="application/json"
            )
        
        # Download blob content
        blob_client = blob_service_client.get_blob_client(
            container="pdf-uploads", 
            blob=pdf_blob.name
        )
        blob_data = blob_client.download_blob().readall()
        
        # Extract text using Document Intelligence
        poller = doc_client.begin_analyze_document("prebuilt-read", blob_data)
        result = poller.result()
        
        # Extract text content
        extracted_text = ""
        for page in result.pages:
            for line in page.lines:
                extracted_text += line.content + "\n"
        
        if not extracted_text.strip():
            return func.HttpResponse(
                json.dumps({"error": "No text could be extracted from the document"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Analyze with Azure OpenAI
        openai_client = openai.AzureOpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            api_version="2024-02-01",
            azure_endpoint=os.getenv('OPENAI_ENDPOINT')
        )
        
        # Create analysis prompt
        system_prompt = """Du er en AI-assistent som analyserer dokumenter for Dagens Næringsliv. 
        Analyser det oppgitte dokumentet og gi:
        1. En kort oppsummering (2-3 setninger)
        2. 3-5 hovedpunkter
        3. Viktige konklusjoner eller anbefalinger
        
        Svar på norsk og vær objektiv og faktabasert."""
        
        user_prompt = f"Analyser følgende dokument:\n\n{extracted_text[:8000]}"  # Limit text length
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1000,
            temperature=0.3
        )
        
        ai_analysis = response.choices[0].message.content
        
        # Parse the AI response to extract summary and key points
        lines = ai_analysis.split('\n')
        summary = ""
        key_points = []
        current_section = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if "oppsummering" in line.lower() or "sammendrag" in line.lower():
                current_section = "summary"
                continue
            elif "hovedpunkt" in line.lower() or "viktig" in line.lower():
                current_section = "points"
                continue
            elif line.startswith(('-', '•', '1.', '2.', '3.', '4.', '5.')):
                if current_section == "points":
                    key_points.append(line.lstrip('-• 123456789.').strip())
                continue
            
            if current_section == "summary" and not summary:
                summary = line
            elif current_section == "points" and line:
                key_points.append(line)
        
        # Fallback if parsing fails
        if not summary:
            summary = "Dokumentet har blitt analysert med AI."
        if not key_points:
            key_points = ["Dokumentanalyse ferdig", "Se full tekst for detaljer"]
        
        # Clean up - delete the uploaded file
        blob_client.delete_blob()
        
        return func.HttpResponse(
            json.dumps({
                "summary": summary,
                "key_points": key_points[:5],  # Limit to 5 points
                "confidence": 0.85,
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