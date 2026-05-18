terraform {
  required_version = ">=1.0"

  required_providers {

    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~>2.23"
    }

  }

  backend "local" {
   path = "/Users/sumedharaghu/.terraform-state/autodevops/terraform.tfstate"
  }
}


provider "kubernetes" {
  config_path    = "~/.kube/config"
  config_context = "docker-desktop"
}