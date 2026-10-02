resource "google_bigquery_dataset" "dataset" {
  dataset_id                  = var.dataset_id
  location                    = var.region
  delete_contents_on_destroy  = true
}

resource "google_bigquery_table" "table" {
  dataset_id          = google_bigquery_dataset.dataset.dataset_id
  table_id            = var.table_id
  deletion_protection = false

  schema = <<EOF
[
  {
    "name": "filename",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "The name of the processed file"
  },
  {
    "name": "bucket_name",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "The GCS bucket where the file was uploaded"
  },
  {
    "name": "content_type",
    "type": "STRING",
    "mode": "NULLABLE",
    "description": "The content type of the file"
  },
  {
    "name": "file_size",
    "type": "INTEGER",
    "mode": "NULLABLE",
    "description": "The size of the file in bytes"
  },
  {
    "name": "word_count",
    "type": "INTEGER",
    "mode": "NULLABLE",
    "description": "The word count of the document (simulated OCR)"
  },
  {
    "name": "tags",
    "type": "STRING",
    "mode": "REPEATED",
    "description": "Extracted key tags from the file"
  },
  {
    "name": "processed_at",
    "type": "TIMESTAMP",
    "mode": "REQUIRED",
    "description": "The timestamp when the file was processed"
  }
]
EOF
}
