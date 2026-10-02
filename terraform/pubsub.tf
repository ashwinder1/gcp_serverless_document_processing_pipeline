resource "google_pubsub_topic" "topic" {
  name = "${var.bucket_name}-notifications"
}

resource "google_pubsub_subscription" "push_subscription" {
  name  = "${var.bucket_name}-subscription"
  topic = google_pubsub_topic.topic.name

  ack_deadline_seconds = 60

  push_config {
    push_endpoint = google_cloud_run_v2_service.processor.uri
  }
}
