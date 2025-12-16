resource "kubernetes_deployment" "autodevops" {
    metadata {
      name = "autodevops"
      namespace =  kubernetes_namespace.autodevops.metadata[0].name
      labels = {
        app = "autodevops"
        }
    }
    spec {
        replicas = 2

        selector {
            match_labels = {
                app = "autodevops"
            }
        }
        template {
            metadata {
                labels = {
                    app = "autodevops"
                }
            } 
            spec {
                container {
                    name = "autodevops"
                    image = "autodevops:latest"
                    image_pull_policy = "IfNotPresent"
                    port{
                        container_port = 8080
                        name = "http"
                    }
                    resources {
                    limits = {
                    cpu    = "500m"
                    memory = "512Mi"
                    }
                    requests = {
                    cpu    = "100m"
                    memory = "128Mi"
                    }
                    }
                }
            }
        }
    }
}