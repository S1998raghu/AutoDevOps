resource "kubernetes_namespace" "autodevops" {
    metadata {
         name = "autodevops" 
      labels={
        managed-by = "terraform"
        app = "autodevops"
      }
    }
}

resource "kubernetes_pod" "test" {
    metadata {
      name = "nginx-test"
      namespace = kubernetes_namespace.autodevops.metadata[0].name
    }
    spec {
        container {
          name = "nginx"
          image = "nginx:latest"
        port{
            container_port = 80
        }
    }
}
}