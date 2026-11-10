# Repositorio privado para las imagenes Docker
resource "google_artifact_registry_repository" "repo" {
  project       = var.project_id
  location      = var.region
  repository_id = var.repo_name
  description   = "Imagenes Docker de la clinica veterinaria"
  format        = "DOCKER"
}



# Cuenta de servicio utilizada por los nodos GKE
resource "google_service_account" "nodes" {
  project      = var.project_id
  account_id   = "gke-nodes-${var.team_id}"
  display_name = "Cuenta de servicio de nodos GKE"
}

# Permiso para descargar imagenes de Artifact Registry
resource "google_project_iam_member" "nodes_ar_reader" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.nodes.email}"
}

# Permiso para enviar registros a Cloud Logging
resource "google_project_iam_member" "nodes_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.nodes.email}"
}

# Permiso para enviar metricas a Cloud Monitoring
resource "google_project_iam_member" "nodes_metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.nodes.email}"
}



# Cluster Kubernetes GKE Standard zonal
resource "google_container_cluster" "primary" {
  project  = var.project_id
  name     = var.cluster_name
  location = var.zone

  # Utilizaremos un node pool independiente
  remove_default_node_pool = true
  initial_node_count       = 1

  # Permite destruir el cluster al finalizar
  deletion_protection = false

  # Identificacion de los recursos del equipo
  resource_labels = {
    equipo   = var.team_id
    proyecto = "veterinaria"
  }
}



# Node pool con dos nodos e2-small Spot
resource "google_container_node_pool" "spot" {
  project    = var.project_id
  name       = "spot-pool"
  cluster    = google_container_cluster.primary.name
  location   = var.zone
  node_count = var.node_count

  node_config {
    machine_type = "e2-small"
    spot         = true

    disk_size_gb = 30
    disk_type    = "pd-standard"

    service_account = google_service_account.nodes.email

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    labels = {
      equipo = var.team_id
    }
  }

  depends_on = [
    google_project_iam_member.nodes_ar_reader,
    google_project_iam_member.nodes_log_writer,
    google_project_iam_member.nodes_metric_writer
  ]
}
