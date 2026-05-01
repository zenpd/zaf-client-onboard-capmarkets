data "azurerm_resource_group" "rg" {
  name = var.resource_group_name
}

data "azurerm_virtual_network" "vnet" {
  name                = var.vnet_name
  resource_group_name = var.resource_group_name
}

data "azurerm_container_registry" "acr" {
  name                = var.acr_name
  resource_group_name = var.resource_group_name
}

data "azurerm_user_assigned_identity" "aca_identity" {
  name                = var.user_assigned_identity_name
  resource_group_name = var.resource_group_name
}

data "azurerm_log_analytics_workspace" "log" {
  name                = var.log_analytics_workspace_name
  resource_group_name = var.resource_group_name
}

#############################################
# ACA Subnet
#############################################
resource "azurerm_subnet" "aca_subnet" {
  name                 = var.subnet_name
  resource_group_name  = var.resource_group_name
  virtual_network_name = var.vnet_name
  address_prefixes     = [var.subnet_cidr]

  delegation {
    name = "aca-delegation"
    service_delegation {
      name    = "Microsoft.App/environments"
      actions = ["Microsoft.Network/virtualNetworks/subnets/action"]
    }
  }
}

#############################################
# Optional: ACR Private Endpoint
#############################################
resource "azurerm_private_dns_zone" "acr_pl" {
  count               = var.enable_acr_private_endpoint ? 1 : 0
  name                = "privatelink.azurecr.io"
  resource_group_name = var.resource_group_name
}

resource "azurerm_private_dns_zone_virtual_network_link" "acr_pl_link" {
  count                 = var.enable_acr_private_endpoint ? 1 : 0
  name                  = "${var.vnet_name}-acr-pl-link-capmarkets"
  resource_group_name   = var.resource_group_name
  private_dns_zone_name = azurerm_private_dns_zone.acr_pl[0].name
  virtual_network_id    = data.azurerm_virtual_network.vnet.id
  registration_enabled  = false
}

data "azurerm_subnet" "pe_subnet" {
  count                = var.enable_acr_private_endpoint ? 1 : 0
  name                 = var.pe_subnet_name
  resource_group_name  = var.resource_group_name
  virtual_network_name = var.vnet_name
}

resource "azurerm_private_endpoint" "acr_pe" {
  count               = var.enable_acr_private_endpoint ? 1 : 0
  name                = "${var.acr_name}-pe-capmarkets"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = data.azurerm_subnet.pe_subnet[0].id

  private_service_connection {
    name                           = "${var.acr_name}-pe-conn-capmarkets"
    private_connection_resource_id = data.azurerm_container_registry.acr.id
    is_manual_connection           = false
    subresource_names              = ["registry"]
  }

  private_dns_zone_group {
    name                 = "acr-pl-zone-group"
    private_dns_zone_ids = [azurerm_private_dns_zone.acr_pl[0].id]
  }
}

#############################################
# ACA Environment (reuse existing or create)
#############################################
resource "azurerm_container_app_environment" "env" {
  name                = var.container_env_name
  location            = var.location
  resource_group_name = var.resource_group_name

  log_analytics_workspace_id = data.azurerm_log_analytics_workspace.log.id
  infrastructure_subnet_id   = azurerm_subnet.aca_subnet.id
}

#############################################
# Frontend Container App
#############################################
resource "azurerm_container_app" "frontend" {
  name                         = var.frontend_app_name
  resource_group_name          = var.resource_group_name
  container_app_environment_id = azurerm_container_app_environment.env.id
  revision_mode                = "Single"

  identity {
    type         = "UserAssigned"
    identity_ids = [data.azurerm_user_assigned_identity.aca_identity.id]
  }

  template {
    container {
      name   = "frontend"
      image  = "${var.acr_name}.azurecr.io/${var.frontend_image}:${var.image_tag}"
      cpu    = var.cpu
      memory = var.memory
    }
  }

  ingress {
    external_enabled = true
    target_port      = 80
    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  registry {
    server   = "${var.acr_name}.azurecr.io"
    identity = data.azurerm_user_assigned_identity.aca_identity.id
  }
}

#############################################
# Backend Container App
#############################################
resource "azurerm_container_app" "backend" {
  name                         = var.backend_app_name
  resource_group_name          = var.resource_group_name
  container_app_environment_id = azurerm_container_app_environment.env.id
  revision_mode                = "Single"

  identity {
    type         = "UserAssigned"
    identity_ids = [data.azurerm_user_assigned_identity.aca_identity.id]
  }

  template {
    container {
      name   = "backend"
      image  = "${var.acr_name}.azurecr.io/${var.backend_image}:${var.image_tag}"
      cpu    = var.cpu
      memory = var.memory

      env {
        name  = "APP_ENV"
        value = "production"
      }
      env {
        name  = "TEMPORAL_NAMESPACE"
        value = var.temporal_namespace
      }
      env {
        name  = "TEMPORAL_HOST"
        value = var.temporal_host
      }
      env {
        name  = "PHOENIX_COLLECTOR_ENDPOINT"
        value = "https://zaf-phoenix.bravesky-d9f9eeb7.eastus2.azurecontainerapps.io"
      }
      env {
        name  = "PHOENIX_PROJECT_NAME"
        value = "capmarkets-onboarding"
      }
    }
  }

  ingress {
    external_enabled = false
    target_port      = 8002
    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  registry {
    server   = "${var.acr_name}.azurecr.io"
    identity = data.azurerm_user_assigned_identity.aca_identity.id
  }
}

#############################################
# Temporal Worker Container App
# Same image as backend — CMD overridden to run the Temporal worker
#############################################
resource "azurerm_container_app" "worker" {
  name                         = var.worker_app_name
  resource_group_name          = var.resource_group_name
  container_app_environment_id = azurerm_container_app_environment.env.id
  revision_mode                = "Single"

  identity {
    type         = "UserAssigned"
    identity_ids = [data.azurerm_user_assigned_identity.aca_identity.id]
  }

  template {
    # min-replicas=1 so the worker always has one instance polling Temporal
    min_replicas = 1
    max_replicas = 3

    container {
      name    = "worker"
      image   = "${var.acr_name}.azurecr.io/${var.backend_image}:${var.image_tag}"
      cpu     = var.cpu
      memory  = var.memory
      command = ["python", "-m", "workers.temporal_worker"]

      env {
        name  = "APP_ENV"
        value = "production"
      }
      env {
        name  = "TEMPORAL_NAMESPACE"
        value = var.temporal_namespace
      }
      env {
        name  = "TEMPORAL_HOST"
        value = var.temporal_host
      }
      env {
        name  = "PHOENIX_COLLECTOR_ENDPOINT"
        value = "https://zaf-phoenix.bravesky-d9f9eeb7.eastus2.azurecontainerapps.io"
      }
      env {
        name  = "PHOENIX_PROJECT_NAME"
        value = "capmarkets-onboarding"
      }
    }
  }

  # No ingress — worker only polls Temporal, does not serve HTTP
  registry {
    server   = "${var.acr_name}.azurecr.io"
    identity = data.azurerm_user_assigned_identity.aca_identity.id
  }
}
