# Serverless Event-Driven Document Processing Pipeline

This project implements a serverless, event-driven pipeline on Google Cloud Platform (GCP) to ingest documents into Cloud Storage, trigger processing via Pub/Sub, extract metadata (using simulated OCR) with a FastAPI service running on Cloud Run, and stream that metadata into BigQuery.


![image](./assets/mermaid-diagram.svg)


## Implementation Details

> - **FastAPI** as the Python web framework.
> - **Cloud Storage Pub/Sub Notifications** for the trigger mechanism.
> - **BigQuery Streaming Inserts** via the Google Cloud Python Client library.
> - **Structured BigQuery Schema** including repeated tags and processing metadata.
> - **Unauthenticated Cloud Run** to simplify testing and deployment for this phase.
> - **Local State** for Terraform.
> - **Local Mock Script** to test locally without GCP dependencies.

## Proposed Project Structure

The repository has two main components:
- [Processor](/processor): The FastAPI application code, requirements, and Dockerfile.
- [Terraform](/terraform): Terraform configurations to provision GCS, Pub/Sub, Cloud Run, BigQuery, IAM permissions, and service accounts.

---

### Ingestion & Triggering Component

#### [terraform/main.tf](/terraform/main.tf)
Defines the main GCP provider and local state configuration.

#### [terraform/variables.tf](/terraform/variables.tf)
Defines the configurable variables (e.g. project_id, region, bucket_name, dataset_id).

#### [terraform/gcs.tf](/terraform/gcs.tf)
Provisions the ingestion GCS bucket and enables Pub/Sub notifications on file uploads.

#### [terraform/pubsub.tf](/terraform/pubsub.tf)
Provisions the Pub/Sub topic and a push subscription targeting the Cloud Run service URL.

---

### Processing Component (Cloud Run & FastAPI)

#### [processor/main.py](/processor/main.py)
A FastAPI web application that:
- Receives Pub/Sub push messages containing the GCS file upload metadata.
- Downloads/reads the file from GCS if it is a `.txt` file, or simulates OCR logic for other formats.
- Extracts metadata (filename, bucket_name, content_type, file_size, word_count, tags, processed_at).
- Streams the extracted metadata into BigQuery.

#### [processor/requirements.txt](/processor/requirements.txt)
Lists dependencies: `fastapi`, `uvicorn`, `google-cloud-storage`, `google-cloud-bigquery`, `pydantic`.

#### [processor/Dockerfile](/processor/Dockerfile)
Containerizes the FastAPI application for deployment to Cloud Run.

#### [terraform/cloud_run.tf](/terraform/cloud_run.tf)
Provisions the Cloud Run service, configures it to run public (unauthenticated), and sets up the required IAM roles.

---

### Storage Component (BigQuery)

#### [terraform/bigquery.tf](/terraform/bigquery.tf)
Provisions the BigQuery dataset and the structured metadata table. The schema is as follows:
- `filename`: STRING
- `bucket_name`: STRING
- `content_type`: STRING
- `file_size`: INTEGER
- `word_count`: INTEGER
- `tags`: REPEATED STRING (Array of strings)
- `processed_at`: TIMESTAMP

---

### Verification and Local Testing Component

#### [scripts/test_local.py](/scripts/test_local.py)
A local mock script that:
- Runs the FastAPI app locally.
- Sends a mock Pub/Sub HTTP POST request containing sample file event payloads.
- Verifies that the FastAPI application parses the payload and simulates metadata extraction correctly.

## Verification Plan

### Automated Tests
- Running basic script-based request verification against the local FastAPI server.

### Manual Verification
1. Run local mock script to verify the FastAPI processing logic.
2. Initialize and apply Terraform configs (`terraform init`, `terraform apply`).
3. Upload a sample `.txt` file and a sample `.pdf` file to the ingestion GCS bucket.
4. Check Cloud Run logs to verify receipt and processing of events.
5. Query the BigQuery table to ensure metadata streams correctly and tags are indexed as arrays.
