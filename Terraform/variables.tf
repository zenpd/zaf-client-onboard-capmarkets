variable "resource_group_name"          { type = string }
variable "location"                     { type = string }
variable "vnet_name"                    { type = string }
variable "subnet_name"                  { type = string }
variable "subnet_cidr"                  { type = string }  # e.g. "10.2.0.0/24"

variable "acr_name"                     { type = string }  # e.g. "zafacr"
variable "user_assigned_identity_name"  { type = string }  # e.g. "aca-identity"
variable "log_analytics_workspace_name" { type = string }  # e.g. "zaf-aca-law"
variable "container_env_name"           { type = string }  # e.g. "zaf-aca-pvt-env"

variable "frontend_app_name"            { type = string }  # e.g. "capmarkets-onboard-fe"
variable "backend_app_name"             { type = string }  # e.g. "capmarkets-onboard-be"
variable "worker_app_name"              { type = string }  # e.g. "capmarkets-onboard-worker"
variable "frontend_image"               { type = string }
variable "backend_image"                { type = string }
variable "image_tag"                    { type = string }

variable "cpu"                          { type = number }
variable "memory"                       { type = string }

variable "enable_acr_private_endpoint" {
  description = "Create ACR Private Endpoint + DNS (set true if ACR is private-only)"
  type        = bool
  default     = false
}

variable "pe_subnet_name" {
  description = "Subnet to host private endpoints (required when enable_acr_private_endpoint=true)"
  type        = string
  default     = ""
}

# Temporal shared cluster endpoint (used by worker)
variable "temporal_host" {
  type    = string
  default = ""
}

variable "temporal_namespace" {
  type    = string
  default = "capmarkets-onboarding"
}
