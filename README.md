# DevSecOps Platform for TicTactoe

I transformed a TicTacToe frontend app into a complete DevSecOps platform. Starting with a React frontend, I added a FastAPI backend and Redis database to persist game state across load-balanced Kubernetes pods. I built a CI/CD pipeline using GitHub Actions to automate builds, tests, and deployments, using secure multi-stage distroless Docker images for both services. Setting up CI/CD early on dramatically improved my local development experience as I could test my changes almost immediately.

The pipeline runs unit tests, linters, and Trivy scans before pushing Docker images to GitHub Container Registry. It then programmatically updates the image tags in the Helm values.yaml file using yq, commits the change back to the repository, and triggers ArgoCD to deploy the updated images — completing the GitOps loop. Helm charts were used to enable modular, reusable infrastructure definitions.

Security was enforced through HTTPS/TLS termination via NGINX Ingress and Cert-Manager, Secrets and RBAC-controlled ServiceAccounts, PodSecurityContexts for non-root containers, and Calico NetworkPolicies for least-privilege, pod-level communication.

For observability, I integrated Prometheus and Grafana, exposing custom /metrics from the backend API. Dashboards visualize app-level stats (win rates, fairness, invalid moves), infrastructure usage (CPU/memory), and API performance — emulating real-world SRE practices.

![TicTacToe](https://github.com/user-attachments/assets/893c2d7b-bbf1-4178-87b3-7ec82785288d)

---

## 📚 Project Overview

This project demonstrates a secure, production-grade DevSecOps workflow using Kubernetes (KIND), GitHub Actions, ArgoCD, Docker, Prometheus, Grafana, and Kubernetes security best practices (Secrets, RBAC, TLS, NetworkPolicies).

- **Frontend**: React app served via Ingress
- **Backend**: FastAPI with Redis state persistence, Prometheus metrics, and Unit Tests
- **State Management**: Redis database
- **CI/CD**: GitHub Actions pipelines with unit tests, static code analysis, and Trivy image scanning
- **Deployment**: GitOps using ArgoCD and Helm Charts
- **Security**: Calico CNI with NetworkPolicies for pod-to-pod access control, podSecurityContexts for container permissions, and RBAC for protecting Kubernetes Secrets
- **Monitoring**: Prometheus and Grafana served via Ingress

---

## ⚙️ DevSecOps CI/CD Pipeline

![CI/CD Pipeline](https://github.com/user-attachments/assets/ed3452f3-0619-4edd-9570-0fed39cc3c1f)

**CI/CD Flow:**
1. **GitHub Actions CI/CD** runs tests and linters on every push.
2. Docker images are built and scanned using **Trivy** for vulnerabilities.
3. Images are pushed to a private **GitHub Container Registry (GHCR)**.
4. The Helm `values.yaml` file is updated with new image tags stored in GHCR.
5. **ArgoCD** detects changes to values.yaml and deploys K8s manifests to a local (KIND) cluster using GitOps.

---

## 🛠 TicTacToe DevSecOps Architecture

![Architecture Diagram](https://github.com/user-attachments/assets/6a1ac8b5-6fad-4294-99c0-ed88b41db614)


**Key Highlights:**
- Traffic flows from users through an NGINX Ingress Controller with TLS termination.
- Backend services expose Prometheus `/metrics`, scraped for observability.
- Secure pod-to-pod communication is enforced via Kubernetes Network Policies (Calico).
- Sensitive environment variables are injected via Kubernetes Secrets.
- RBAC and PodSecurityContext restrict pod access and enforce non-root containers.


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


---

## 📊 Grafana Dashboards (Kubernetes, API, Application Metrics)

Prometheus collects metrics from the application and Kubernetes cluster. Grafana visualizes those metrics using custom dashboards.

**📦 Infrastructure Metrics**

![image](https://github.com/user-attachments/assets/0909f021-0859-4f65-9a85-196b7f091f11)

Monitors:
- Pod-level CPU and memory usage
- Pod restarts and uptime
- Node-level CPU and memory usage

**🔌 API Metrics**

![image](https://github.com/user-attachments/assets/f93108f3-3f5d-4dab-9ac8-93ff9cfc038b)

Monitors:
- API request volume and latency
- Errors (invalid moves, 5xx)
- Payload size

**🎮 App Metrics**

![image](https://github.com/user-attachments/assets/43890586-8dbd-4360-9ce9-a7b1eb0bbe98)

Monitors:
- Win/draw ratios
- Fairness indicator (tracks imbalance over time)
- Game reset frequency (can flag user frustration or abuse)
- Invalid moves (e.g., /api/move/99) for bug tracking or exploit attempts
- Total games played

---

## ⚙️ Setup Instructions


### 1. Create a KIND cluster with Calico

Run at project root dir:

```bash
kind create cluster --config kind-calico.yaml --name devsecops-webapp
```

kind-calico.yaml must configure Calico CNI.


### 2. Install Calico CNI

```bash
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.26.0/manifests/tigera-operator.yaml
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.26.0/manifests/custom-resources.yaml
```

If Calico has issues, reapply:

```bash
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.26.1/manifests/calico.yaml
kubectl apply -f calico-rbac.yaml
kubectl rollout restart daemonset calico-node -n calico-system
kubectl delete pod -n calico-system -l k8s-app=calico-node
```


### 3. Install Prometheus and Grafana (Monitoring Stack)

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install prometheus-stack prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace
```


### 4. Install ArgoCD (GitOps Controller)

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

Port Forward ArgoCD UI:

```bash
kubectl port-forward svc/argocd-server 9000:80 -n argocd
```

Get ArgoCD Admin Password:

```bash
kubectl get secrets -n argocd
kubectl edit secret argocd-initial-admin-secret -n argocd
echo <password> | base64 --decode
```

Access ArgoCD at http://localhost:9000 (Username: admin, Password: decoded password)


### 5. Install Ingress Controller (NGINX)

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install ingress-nginx ingress-nginx/ingress-nginx --namespace ingress-nginx --create-namespace
```

Port Forward Ingress Controller:

```bash
kubectl port-forward -n ingress-nginx service/ingress-nginx-controller 8080:80
```


### 6. Configure Local DNS Resolution

Update your /etc/hosts file:

```bash
127.0.0.1 tic-tac-toe.local
127.0.0.1 grafana.local
127.0.0.1 prometheus.local
```


### 7. Install Cert-Manager for TLS Certificates

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.17.2/cert-manager.yaml
```

Cert-Manager automates certificate management for your Ingresses.


### 8. Configure GitHub Container Registry Pull Secrets

Create a GitHub Personal Access Token with read:packages and write:packages permissions.

```bash
kubectl create secret docker-registry github-container-registry \
  --docker-server=ghcr.io \
  --docker-username=YOUR_GITHUB_USERNAME \
  --docker-password=YOUR_GITHUB_TOKEN \
  --docker-email=YOUR_EMAIL
```


---

## 🧪 Testing Network Policies

Test pod-to-pod connectivity restrictions, below example should not be allowed since ingress controller serves backend, not the frontend (frontend -> backend traffic not allowed).


1. Get frontend pod name:

```bash
kubectl get pods -l app=tic-tac-toe-frontend
```


2. Connect to the pod:

```bash
kubectl exec -it <frontend-pod-name> -- sh
```

1. Get backend pod ip:

```bash
kubectl get pods -o wide
```


3. Try curl to backend pod and google.com 

```bash
curl <backend-pod-ip:port>
curl google.com
```

---


## 📈 Monitoring and Observability

Import the Grafana dashboard json file in the Grafana web UI.

Access Grafana at http://grafana.local

Access Prometheus at http://prometheus.local

View Kubernetes, API, and application-level metrics on custom Grafana dashboards.


---

## 🚀 Future Improvements

Enforce secrets encryption at rest using a secrets manager like Hashicorp Vault or KMS


---

## 📚 References

This project was initially inspired by the [DevSecOps CI/CD Pipeline Implementation](https://www.youtube.com/watch?v=Ke_Wr5zPE0A&list=PLdpzxOOAlwvLm5lWlYctUnwaFRIO2Io_5&index=7) tutorial for basic frontend and CI/CD pipeline setup.

The project was significantly expanded to include:

- Backend development (FastAPI + Redis)
- Secure multi-stage distroless Docker builds
- GitHub Actions CI/CD pipeline (static code analysis, unit tests, Trivy scans)
- Kubernetes manifests with Helm templating and ArgoCD
- Secure workload hardening (HTTPS/TLS, RBAC, Secrets, Pod Security Contexts, Network Policies)
- Observability stack with Prometheus and Grafana

---


