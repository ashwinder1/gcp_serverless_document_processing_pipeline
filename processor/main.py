import base64
import json
import logging
from datetime import datetime, timezone
import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Request, status
from pydantic import BaseModel
from google.cloud import storage
from google.cloud import bigquery

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="GCS Event Processor")

# Read environment variables
PROJECT_ID = os.getenv("PROJECT_ID")
DATASET_ID = os.getenv("DATASET_ID", "document_processing")
TABLE_ID = os.getenv("TABLE_ID", "metadata")

# Initialize GCP clients lazily
storage_client = None
bigquery_client = None

def get_storage_client():
    global storage_client
    if storage_client is None:
        storage_client = storage.Client()
    return storage_client

def get_bigquery_client():
    global bigquery_client
    if bigquery_client is None:
        bigquery_client = bigquery.Client()
    return bigquery_client

class PubSubMessage(BaseModel):
    message: dict
    subscription: str

@app.post("/", status_code=status.HTTP_200_OK)
async def handle_pubsub_message(request: Request):
    """
    Receives Pub/Sub push notification from GCS when a new file is uploaded.
    """
    try:
        body = await request.json()
        logger.info(f"Received raw body: {body}")
    except Exception as e:
        logger.error(f"Error parsing raw JSON request body: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    if not body or "message" not in body:
        logger.error("Invalid Pub/Sub message format: missing 'message' block")
        raise HTTPException(status_code=400, detail="Invalid Pub/Sub message format")

    message = body["message"]
    if "data" not in message:
        logger.error("Invalid Pub/Sub message format: missing 'data' field")
        raise HTTPException(status_code=400, detail="Invalid data payload")

    # Decode base64 data payload
    try:
        data_str = base64.b64decode(message["data"]).decode("utf-8")
        event_data = json.loads(data_str)
        logger.info(f"Decoded GCS event data: {event_data}")
    except Exception as e:
        logger.error(f"Failed to decode base64 data: {str(e)}")
        raise HTTPException(status_code=400, detail="Failed to decode data payload")

    # Extract object details from GCS notification payload
    filename = event_data.get("name")
    bucket_name = event_data.get("bucket")
    content_type = event_data.get("contentType")
    size_str = event_data.get("size")

    if not filename or not bucket_name:
        logger.error("Missing required metadata: 'name' or 'bucket' not found in GCS payload")
        raise HTTPException(status_code=400, detail="Missing required GCS metadata")

    file_size = int(size_str) if size_str and size_str.isdigit() else None

    # Run simulated OCR
    word_count, tags = process_document(bucket_name, filename, content_type)

    # Prepare BigQuery record
    processed_at = datetime.now(timezone.utc).isoformat()
    record = {
        "filename": filename,
        "bucket_name": bucket_name,
        "content_type": content_type,
        "file_size": file_size,
        "word_count": word_count,
        "tags": tags,
        "processed_at": processed_at,
    }

    logger.info(f"Ingesting record to BigQuery: {record}")

    # Write to BigQuery
    try:
        write_to_bigquery(record)
    except Exception as e:
        logger.error(f"Failed to write to BigQuery: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database write failure: {str(e)}")

    return {"status": "success", "processed_file": filename}


def process_document(bucket_name: str, filename: str, content_type: Optional[str]) -> tuple[int, List[str]]:
    """
    Simulated OCR processing:
    - If it's a text file (.txt or text/plain), download it from GCS and calculate actual word count & tags.
    - Otherwise (e.g. PDF/image), simulate OCR by generating mock word count and tags based on file details.
    """
    logger.info(f"Processing document {filename} from bucket {bucket_name} (Content-Type: {content_type})")

    is_txt = (filename.lower().endswith(".txt") or (content_type and content_type.startswith("text/")))

    if is_txt:
        try:
            # Check if GCS client can be instantiated and read from
            client = get_storage_client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(filename)
            text_content = blob.download_as_text()
            
            # Simple word count
            words = text_content.split()
            word_count = len(words)
            
            # Extract tags based on word frequency (length > 4)
            clean_words = [w.strip(".,!?;:()\"'").lower() for w in words if len(w) > 4]
            unique_words = list(dict.fromkeys(clean_words))[:5]
            
            tags = unique_words if unique_words else ["text", "imported"]
            logger.info(f"Read real text file. Word count: {word_count}. Tags: {tags}")
            return word_count, tags

        except Exception as e:
            logger.warning(f"Could not read real GCS file (possibly local/mock testing): {str(e)}. Falling back to simulation.")
            return simulate_ocr(filename)
    else:
        return simulate_ocr(filename)


def simulate_ocr(filename: str) -> tuple[int, List[str]]:
    """
    Generates mock OCR metadata based on the filename.
    """
    import random
    
    # Generate reproducible/semi-random values based on filename
    random.seed(hash(filename))
    
    word_count = random.randint(100, 2500)
    
    # Pick random industry tags
    pool = ["finance", "invoice", "receipt", "legal", "report", "medical", "resume", "government", "education", "technical"]
    tags = random.sample(pool, k=random.randint(2, 4))
    
    # Add file extension tag
    ext = filename.split(".")[-1].lower() if "." in filename else "unknown"
    tags.append(ext)
    
    logger.info(f"Simulated OCR for {filename}. Word count: {word_count}. Tags: {tags}")
    return word_count, tags


def write_to_bigquery(record: dict):
    """
    Insert the metadata record into BigQuery.
    """
    # If PROJECT_ID is not set, we assume local mock testing
    if not PROJECT_ID:
        logger.info(f"[MOCK BIGQUERY] Writing to table {DATASET_ID}.{TABLE_ID}: {record}")
        return

    client = get_bigquery_client()
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    errors = client.insert_rows_json(table_ref, [record])
    if errors:
        logger.error(f"BigQuery insert errors: {errors}")
        raise RuntimeError(f"BigQuery write failed: {errors}")
    else:
        logger.info("Successfully inserted record into BigQuery")


@app.get("/health")
def health_check():
    return {"status": "healthy"}
