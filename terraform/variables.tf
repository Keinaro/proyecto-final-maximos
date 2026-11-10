
variable "project_id" {
  description = "ID del proyecto de Google Cloud"
  type        = string
}

variable "region" {
  description = "Region donde se crearan los recursos"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "Zona donde se creara el cluster GKE"
  type        = string
  default     = "us-central1-a"
}

variable "team_id" {
  description = "Identificador del equipo"
  type        = string
  default     = "maximos"
}

variable "cluster_name" {
  description = "Nombre del cluster GKE"
  type        = string
  default     = "gke-maximos"
}

variable "repo_name" {
  description = "Nombre del repositorio Artifact Registry"
  type        = string
  default     = "vet-repo"
}

variable "node_count" {
  description = "Cantidad de nodos del cluster"
  type        = number
  default     = 2

  validation {
    condition     = var.node_count == 2
    error_message = "El proyecto requiere exactamente 2 nodos."
  }
}
