# Service to expose AutoDevOps
resource "kubernetes_service" "autodevops" {
  metadata {
    name      = "autodevops-svc"
    namespace = kubernetes_namespace.autodevops.metadata[0].name
  }

  spec {
    selector = {
      app = "autodevops"
    }

    port {
      port        = 80
      target_port = 8000
      node_port   = 30080
    }

    type = "NodePort"
  }
}