variable "project_id" {
  description = "The GCP Project ID where resources will be created"
  type        = string
}

variable "region" {
  description = "The region to deploy resources in"
  type        = string
  default     = "us-central1"
}

variable "bucket_name" {
  description = "The name of the GCS bucket for document ingestion. Must be globally unique."
  type        = string
}

variable "dataset_id" {
  description = "The BigQuery dataset ID"
  type        = string
  default     = "document_processing"
}

variable "table_id" {
  description = "The BigQuery table ID for streaming metadata"
  type        = string
  default     = "metadata"
}

variable "processor_image" {
  description = "The container image to deploy to Cloud Run"
  type        = string
}
