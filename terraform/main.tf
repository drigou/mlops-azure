terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0" # or the latest major version
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "azurerm" {
  features {}
}

data "azurerm_client_config" "current" {}

resource "azurerm_resource_group" "rg-az-ml" {
  name     = "rg-az-ml"
  location = "westeurope"
}

# Storage account and key vault names must be globally unique across Azure,
# so a short random suffix is appended to avoid naming collisions.
resource "random_string" "az_ml_suffix" {
  length  = 6
  special = false
  upper   = false
}

resource "azurerm_storage_account" "st-az-ml" {
  name                     = "stazml${random_string.az_ml_suffix.result}"
  resource_group_name      = azurerm_resource_group.rg-az-ml.name
  location                 = azurerm_resource_group.rg-az-ml.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_key_vault" "kv-az-ml" {
  name                     = "kv-az-ml-${random_string.az_ml_suffix.result}"
  resource_group_name      = azurerm_resource_group.rg-az-ml.name
  location                 = azurerm_resource_group.rg-az-ml.location
  tenant_id                = data.azurerm_client_config.current.tenant_id
  sku_name                 = "standard"
  purge_protection_enabled = false
}

resource "azurerm_application_insights" "appi-az-ml" {
  name                = "appi-az-ml"
  resource_group_name = azurerm_resource_group.rg-az-ml.name
  location            = azurerm_resource_group.rg-az-ml.location
  application_type    = "web"
}

resource "azurerm_machine_learning_workspace" "mlw-az-ml" {
  name                    = "mlw-az-ml"
  resource_group_name     = azurerm_resource_group.rg-az-ml.name
  location                = azurerm_resource_group.rg-az-ml.location
  storage_account_id      = azurerm_storage_account.st-az-ml.id
  key_vault_id            = azurerm_key_vault.kv-az-ml.id
  application_insights_id = azurerm_application_insights.appi-az-ml.id

  identity {
    type = "SystemAssigned"
  }
}