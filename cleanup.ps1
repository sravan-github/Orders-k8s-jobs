$ErrorActionPreference = "Continue"
kubectl delete namespace orders monitoring --ignore-not-found
kubectl delete clusterrolebinding kube-state-metrics --ignore-not-found
kubectl delete clusterrole kube-state-metrics --ignore-not-found
