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

resource "azurerm_resource_group" "rg-dg-foundry" {
  name     = "rg-dg-foundry"
  location = "westeurope"
}

# The custom subdomain of a Foundry resource must be globally unique across
# Azure, so a short random suffix is appended to avoid naming collisions.
resource "random_string" "foundry_suffix" {
  length  = 6
  special = false
  upper   = false
}

# Microsoft Foundry resource (Azure AI Services account with project management enabled)
resource "azurerm_cognitive_account" "foundry-dg" {
  name                  = "foundry-dg-${random_string.foundry_suffix.result}"
  resource_group_name   = azurerm_resource_group.rg-dg-foundry.name
  location              = azurerm_resource_group.rg-dg-foundry.location
  kind                  = "AIServices"
  sku_name              = "S0"
  custom_subdomain_name = "foundry-dg-${random_string.foundry_suffix.result}"

  project_management_enabled = true

  identity {
    type = "SystemAssigned"
  }
}

# A Foundry project is a logical container for deployments and agents. It is created under a Foundry resource.
resource "azurerm_cognitive_account_project" "proj-dg-foundry" {
  name                 = "proj-dg-foundry"
  cognitive_account_id = azurerm_cognitive_account.foundry-dg.id
  location             = azurerm_resource_group.rg-dg-foundry.location

  identity {
    type = "SystemAssigned"
  }
}

# Deployments fall under the Foundry resource, and are used to host models for inference.
resource "azurerm_cognitive_deployment" "gpt5mini" {
  name                 = "gpt-5-mini"
  cognitive_account_id = azurerm_cognitive_account.foundry-dg.id

  model {
    format = "OpenAI"
    name   = "gpt-5-mini"
  }

  sku {
    name     = "GlobalStandard"   # or "DataZoneStandard" for EU processing
    capacity = 10
  }
}