resource "google_service_account" "processor_sa" {
  account_id   = "document-processor-sa"
  display_name = "Service Account for Document Processor Cloud Run Service"
}

# Grant GCS Object Viewer permissions on the ingestion bucket
resource "google_storage_bucket_iam_member" "gcs_viewer" {
  bucket = google_storage_bucket.ingestion_bucket.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.processor_sa.email}"
}

# Grant BigQuery Data Editor permissions on the dataset
resource "google_bigquery_dataset_iam_member" "bq_editor" {
  dataset_id = google_bigquery_dataset.dataset.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.processor_sa.email}"
}

resource "google_cloud_run_v2_service" "processor" {
  name     = "document-processor"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.processor_sa.email

    containers {
      image = var.processor_image

      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "DATASET_ID"
        value = var.dataset_id
      }
      env {
        name  = "TABLE_ID"
        value = var.table_id
      }
    }
  }
}

# Allow unauthenticated (public) invocations as per user request
resource "google_cloud_run_v2_service_iam_member" "noauth" {
  project  = google_cloud_run_v2_service.processor.project
  location = google_cloud_run_v2_service.processor.location
  name     = google_cloud_run_v2_service.processor.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
