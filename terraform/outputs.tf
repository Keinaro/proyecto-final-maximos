
# Identificador del proyecto
output "project_id" {
  description = "Proyecto utilizado en Google Cloud"
  value       = var.project_id
}

# Nombre del cluster GKE
output "cluster_name" {
  description = "Nombre del cluster Kubernetes"
  value       = google_container_cluster.primary.name
}

# Zona del cluster
output "cluster_zone" {
  description = "Zona donde se encuentra GKE"
  value       = var.zone
}

# Ruta de Artifact Registry
output "artifact_registry_url" {
  description = "Ruta base para publicar imagenes Docker"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.repo.repository_id}"
}

# Comando para configurar kubectl
output "get_credentials_command" {
  description = "Comando para conectarse al cluster GKE"
  value       = "gcloud container clusters get-credentials ${google_container_cluster.primary.name} --zone ${var.zone} --project ${var.project_id}"
}

# Nombre del node pool
output "node_pool_name" {
  description = "Nombre del grupo de nodos Spot"
  value       = google_container_node_pool.spot.name
}
