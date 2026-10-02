data "google_storage_project_service_account" "gcs_account" {}

resource "google_pubsub_topic_iam_binding" "gcs_publisher" {
  topic   = google_pubsub_topic.topic.name
  role    = "roles/pubsub.publisher"
  members = ["serviceAccount:${data .google_storage_project_service_account.gcs_account.email_address}"]
}

resource "google_storage_bucket" "ingestion_bucket" {
  name                        = var.bucket_name
  location                    = var.region
  force_destroy               = true
  uniform_bucket_level_access = true

  # Ensure the permissions are granted before configuring notifications
  depends_on = [google_pubsub_topic_iam_binding.gcs_publisher]
}

resource "google_storage_notification" "notification" {
  bucket         = google_storage_bucket.ingestion_bucket.name
  payload_format = "JSON_API_V1"
  topic          = google_pubsub_topic.topic.id
  event_types    = ["OBJECT_FINALIZE"]

  depends_on = [google_pubsub_topic_iam_binding.gcs_publisher]
}
