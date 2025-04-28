# DevSecOps TicTacToe Platform

A complete DevSecOps platform deploying a containerized React-FastAPI-Redis web application to Kubernetes, integrating security best practices, observability, and GitOps workflows.

---

## 📚 Project Overview

This project demonstrates a secure, production-grade DevSecOps workflow using Kubernetes (KIND), GitHub Actions, ArgoCD, Docker, Prometheus, Grafana, and Kubernetes security best practices (Secrets, RBAC, TLS, NetworkPolicies).

---

## 🛠 Architecture Overview

- **Frontend**: React app served via Ingress
- **Backend**: FastAPI with Redis state persistence, Prometheus metrics, and Unit Tests
- **State Management**: Redis database
- **CI/CD**: GitHub Actions pipelines with Unit Tests, Linting, and Trivy image scanning
- **Deployment**: GitOps using ArgoCD and Helm Charts
- **Security**: Calico CNI with NetworkPolicies for pod-to-pod access control, podSecurityContexts for container permissions, and RBAC for protecting Kubernetes Secrets
- **Monitoring**: Prometheus and Grafana served via Ingress

---

## 🔐 Security Best Practices Implemented

- HTTPS/TLS termination via Ingress Controller and Cert-Manager
- Kubernetes Secrets for sensitive environment variables (e.g., Redis password)
- Pod Security Contexts enforcing non-root users/groups and read-only root container filesystem
- ServiceAccounts with RBAC roles to restrict access to Kubernetes Secrets
- Calico NetworkPolicies enforcing least-privilege pod-to-pod access
- Secure CI/CD with Trivy scans during Docker image builds
- GitOps continuous deployment via ArgoCD with limited cluster permissions

---

## 🧰 Technologies Used

| Area | Tools |
|:---|:---|
| Containerization | Docker (Multi Stage, Distroless) |
| Orchestration | Kubernetes (KIND) |
| CI/CD | GitHub Actions |
| GitOps | ArgoCD |
| Monitoring | Prometheus, Grafana |
| Security | Trivy, Kubernetes Secrets, RBAC, Calico NetworkPolicies |
| Backend | FastAPI, Redis |
| Frontend | React (Vite) |
| Helm Charts | Custom application deployment |

## ⚙️ Setup Instructions

---

### 2. Install Calico CNI

```bash
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.26.0/manifests/tigera-operator.yaml
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.26.0/manifests/custom-resources.yaml
```

If Calico has issues, reapply:

kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.26.1/manifests/calico.yaml
kubectl apply -f calico-rbac.yaml
kubectl rollout restart daemonset calico-node -n calico-system
kubectl delete pod -n calico-system -l k8s-app=calico-node

### 3. Install Prometheus and Grafana (Monitoring Stack)

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install prometheus-stack prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace

### 4. Install ArgoCD (GitOps Controller)

kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

Port Forward ArgoCD UI:

kubectl port-forward svc/argocd-server 9000:80 -n argocd

Get ArgoCD Admin Password:

kubectl get secrets -n argocd
kubectl edit secret argocd-initial-admin-secret -n argocd
echo <password> | base64 --decode

Access ArgoCD at http://localhost:9000 (Username: admin, Password: decoded password)

### 5. Install Ingress Controller (NGINX)

helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install ingress-nginx ingress-nginx/ingress-nginx --namespace ingress-nginx --create-namespace

Port Forward Ingress Controller:

kubectl port-forward -n ingress-nginx service/ingress-nginx-controller 8080:80

### 6. Configure Local DNS Resolution

Update your /etc/hosts file:

127.0.0.1 tic-tac-toe.local
127.0.0.1 grafana.local
127.0.0.1 prometheus.local

### 7. Install Cert-Manager for TLS Certificates

kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.17.2/cert-manager.yaml

Cert-Manager automates certificate management for your Ingresses.

### 8. Configure GitHub Container Registry Pull Secrets

Create a GitHub Personal Access Token with read:packages and write:packages permissions.

kubectl create secret docker-registry github-container-registry \
  --docker-server=ghcr.io \
  --docker-username=YOUR_GITHUB_USERNAME \
  --docker-password=YOUR_GITHUB_TOKEN \
  --docker-email=YOUR_EMAIL

## 🧪 Testing Network Policies

Test pod-to-pod connectivity restrictions:

1. Get frontend pod name:

kubectl get pods -l app=tic-tac-toe-frontend

2. Connect to the pod:

kubectl exec -it <frontend-pod-name> -- sh

3. Try curl to backend pod IP or Redis — verify traffic is correctly allowed or blocked based on NetworkPolicies.

## 📈 Monitoring and Observability

Access Grafana at http://grafana.local

Access Prometheus at http://prometheus.local

View Kubernetes, API, and application-level metrics on custom Grafana dashboards.

## 🚀 Future Improvements (Optional)

Enforce secrets encryption at rest using KMS

