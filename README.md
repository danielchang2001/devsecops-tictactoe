## 📖 Table of Contents

- [⚙️ DevSecOps CI/CD Pipeline](#️-devsecops-cicd-pipeline)
- [🛠 TicTacToe DevSecOps Architecture](#-tictactoe-devsecops-architecture)
- [🔐 Security Best Practices Implemented](#-security-best-practices-implemented)
- [🧰 Tech Stack](#-tech-stack)
- [📊 Grafana Dashboards (Kubernetes, API, Application Metrics)](#-grafana-dashboards-kubernetes-api-application-metrics)
- [⚙️ Setup Instructions](#️-setup-instructions)
- [🧪 Testing Network Policies](#-testing-network-policies)
- [📈 Monitoring and Observability](#-monitoring-and-observability)
- [🚀 Future Improvements](#-future-improvements)
- [📚 References](#-references)

---

# DevSecOps Platform for TicTactoe

In this personal project, I transformed a simple TicTacToe React frontend into a full-fledged DevSecOps platform. I added a FastAPI backend and a Redis database to persist game state across load-balanced Kubernetes pods. Early on, I set up a CI/CD pipeline using GitHub Actions to automate builds, tests, and deployments — dramatically improving development speed by letting me test changes on a live Kubernetes cluster in seconds.

The pipeline runs unit tests, linters, and Trivy scans on every push. It then builds secure multi-stage distroless Docker images, pushes them to GitHub Container Registry, and programmatically updates Helm image tags using yq. This change is committed back to the repo, triggering ArgoCD to sync and deploy the updated application — completing the GitOps loop.

Security is enforced through HTTPS/TLS termination with NGINX Ingress and Cert-Manager, Kubernetes Secrets protected by RBAC-bound ServiceAccounts, PodSecurityContexts for non-root containers, and Calico NetworkPolicies to restrict pod-to-pod traffic by default.

For observability, I exposed custom /metrics endpoints in the backend and integrated Prometheus and Grafana to visualize key metrics like win ratios, fairness scores, invalid moves, API performance, and cluster resource usage — simulating real-world SRE monitoring workflows.

Frontend: ![TicTacToe](https://github.com/user-attachments/assets/893c2d7b-bbf1-4178-87b3-7ec82785288d)

---

## ⚙️ DevSecOps CI/CD Pipeline

![CI/CD Pipeline](https://github.com/user-attachments/assets/ed3452f3-0619-4edd-9570-0fed39cc3c1f)

- GitHub Actions runs unit tests, linters, and vulnerability scans (via Trivy) on every push.
- If checks pass, secure multi-stage distroless Docker images are built using the Dockerfiles I wrote for the frontend and backend.
- Images are pushed to GitHub Container Registry (GHCR).
- A script updates the Helm values.yaml file with the new image tags using yq and commits the change.
- ArgoCD detects the change and automatically syncs the updated manifests to the local Kubernetes (KIND) cluster.

---

## 🛠 TicTacToe DevSecOps Architecture

![Architecture Diagram](https://github.com/user-attachments/assets/6a1ac8b5-6fad-4294-99c0-ed88b41db614)

- All user traffic enters through an NGINX Ingress Controller with HTTPS/TLS termination (via Cert-Manager).
- Prometheus and Grafana are served to monitoring admins using their own respective NGINX Ingress Controllers.
- The FastAPI backend exposes "/api" endpoints for the frontend and a "/metrics" endpoint for Prometheus.
- Backend pods communicate with redis pods to store and load game state.
- Kubernetes Secrets store sensitive environment variables like Redis host name and password.
- RBAC and PodSecurityContexts limit pod access and enforce non-root containers with read-only filesystems.

---

## 🔐 Security Best Practices Implemented

- HTTPS/TLS termination with NGINX Ingress and Cert-Manager to encrypt traffic in transit.
- Kubernetes Secrets used to manage sensitive values like the Redis password.
- PodSecurityContexts enforce non-root containers and read-only root container filesystems.
- RBAC roles bound to ServiceAccounts restrict pod access to Secrets and other resources.
- Calico NetworkPolicies control pod-to-pod network communication using least-privilege principles.
- Trivy image scans integrated into the CI/CD pipeline to detect vulnerabilities before deployment.
- ArgoCD GitOps model with limited cluster permissions ensures secure and auditable deployments.

---

## 🧰 Tech Stack

| Area           | Tools/Tech Used                            |
|----------------|---------------------------------------------|
| Containerization | Docker (multi-stage builds, distroless images) |
| Orchestration  | Kubernetes (local setup via KIND)           |
| CI/CD          | GitHub Actions                              |
| GitOps         | ArgoCD for declarative deployments          |
| Monitoring     | Prometheus & Grafana                        |
| Security       | Trivy, K8s Secrets, RBAC, Calico NetworkPolicies |
| Backend        | FastAPI (Python), Redis for state management|
| Frontend       | React (Vite)                                |
| Packaging      | Helm charts (custom deployment config)      |


---

## 📊 Grafana Dashboards (Kubernetes, API, Application Metrics)

Prometheus scrapes metrics from both the Kubernetes cluster and the application. Grafana uses those metrics to populate custom dashboards that provide real-time observability.

**📦 Infrastructure Metrics**

![image](https://github.com/user-attachments/assets/0909f021-0859-4f65-9a85-196b7f091f11)

- Monitors:
  - Pod-level CPU and memory usage
  - Node-level resource consumption (CPU & RAM)
  - Pod uptime and restart counts
  
**🔌 API Metrics**

![image](https://github.com/user-attachments/assets/f93108f3-3f5d-4dab-9ac8-93ff9cfc038b)

- Monitors:
  - API request volume and latency
  - Error rates, including invalid moves and 5xx responses
  - Payload size trends across requests and responses

**🎮 App Metrics**

![image](https://github.com/user-attachments/assets/43890586-8dbd-4360-9ce9-a7b1eb0bbe98)

- Monitors:
  - Win/draw ratios to measure gameplay outcomes
  - Fairness indicator, monitoring imbalance between players over time
  - Game reset frequency, useful for detecting user frustration or abuse
  - Invalid move attempts (e.g., /api/move/99) for bug detection and potential exploit attempts
  - Total games played, providing insight into app engagement and volume

---

## ⚙️ Setup Instructions

This project runs locally on a Kubernetes cluster using KIND (Kubernetes IN Docker). It includes a fully integrated DevSecOps pipeline with Calico CNI, GitOps via ArgoCD, TLS with Cert-Manager, and observability via Prometheus + Grafana.

### 1. Create a KIND Cluster with Calico Networking

From the project root:

```bash
kind create cluster --config kind-calico.yaml --name devsecops-webapp
```

Your kind-calico.yaml file must configure the cluster to use the Calico CNI plugin for enforcing Kubernetes Network Policies, as KIND doesn't provide this by default.


### 2. Install Calico CNI (NetworkPolicy Enforcement)

```bash
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.26.0/manifests/tigera-operator.yaml
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.26.0/manifests/custom-resources.yaml
```

If Calico fails or pods are not scheduling properly, try:

```bash
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.26.1/manifests/calico.yaml
kubectl apply -f calico-rbac.yaml
kubectl rollout restart daemonset calico-node -n calico-system
kubectl delete pod -n calico-system -l k8s-app=calico-node
```


### 3. Deploy Monitoring Stack (Prometheus + Grafana)

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install prometheus-stack prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace
```

This sets up full observability for both application and Kubernetes-level metrics.

### 4. Install ArgoCD (GitOps Deployment Controller)

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

Port-forward ArgoCD for local use:

```bash
kubectl port-forward svc/argocd-server 9000:80 -n argocd
```

Retrieve login credentials:

```bash
kubectl get secrets -n argocd
kubectl edit secret argocd-initial-admin-secret -n argocd
echo <password> | base64 --decode
```

Access ArgoCD at http://localhost:9000 (Username: admin, Password: decoded password)


### 5. Install NGINX Ingress Controller

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install ingress-nginx ingress-nginx/ingress-nginx --namespace ingress-nginx --create-namespace
```

Port-forward the ingress controller for local use:

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

This enables automated TLS certificate issuance for ingress routes.


### 8. Configure GitHub Container Registry Pull Secrets

Generate a GitHub Personal Access Token (PAT) with read:packages and write:packages scope.

```bash
kubectl create secret docker-registry github-container-registry \
  --docker-server=ghcr.io \
  --docker-username=YOUR_GITHUB_USERNAME \
  --docker-password=YOUR_GITHUB_TOKEN \
  --docker-email=YOUR_EMAIL
```

This secret allows Kubernetes to pull container images from ghcr.io.

---

## 🧪 Testing Network Policies

This test demonstrates that frontend pods are restricted from accessing backend pods directly, validating that network policies are in effect.

1. Get frontend pod names:

```bash
kubectl get pods -l app=tic-tac-toe-frontend
```


2. Exec into a frontend pod:

```bash
kubectl exec -it <frontend-pod-name> -- sh
```

3. Get backend pod ip:

```bash
kubectl get pods -o wide
```

4. Try curl to backend pod and google.com (external site to test egress):

```bash
curl <backend-pod-ip:port>
curl google.com
```

✅ A failed connection to the backend to Google confirms that ingress to the backend is restricted and egress to the internet from the frontend pod is blocked.

---


## 📈 Monitoring and Observability

Grafana visualizes application, API, and Kubernetes metrics collected by Prometheus.

- Access Grafana at http://grafana.local
- Access Prometheus at http://prometheus.local

- Open the Grafana UI.
- Import the Grafana dashboard json file in the Grafana web UI.
- View real-time data for infrastructure, API usage, and game statistics.

Custom dashboards include:

- Kubernetes pod/node resource metrics
- API performance and error tracking
- Game fairness, resets, and user activity insights

---

## 🚀 Future Improvements

Planned enhancements to further align with production-grade DevSecOps practices:

- Encrypt Kubernetes Secrets at rest using a secrets manager such as:
  - HashiCorp Vault
  - AWS/GCP KMS (Key Management Services)

These improvements would strengthen secret handling beyond base64-encoded Kubernetes Secrets.

---

## 📚 References

This project was originally based on the [DevSecOps CI/CD Pipeline Implementation](https://www.youtube.com/watch?v=Ke_Wr5zPE0A&list=PLdpzxOOAlwvLm5lWlYctUnwaFRIO2Io_5&index=7) YouTube tutorial, which provided the frontend and basic CI/CD structure.

It was significantly expanded to include:

- A full backend API with FastAPI and Redis for state management
    - Secure Docker builds using multi-stage and distroless images
    - CI/CD via GitHub Actions, including:
        - Static code analysis
        - Unit tests
        - Trivy security scans
    - Kubernetes manifests refactored into Helm charts and deployed via ArgoCD
    - Security hardening with:
        - HTTPS/TLS
        - RBAC
        - Kubernetes Secrets
        - Pod Security Contexts
        - Calico Network Policies
    - Full-stack observability with Prometheus and Grafana
  
---


