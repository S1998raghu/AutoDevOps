resource "kubernetes_namespace" "autodevops" {
    metadata {
         name = "autodevops" 
      labels={
        managed-by = "terraform"
        app = "autodevops"
      }
    }
}

