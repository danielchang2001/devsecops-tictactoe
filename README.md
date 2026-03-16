# Overview
![Frontend](https://github.com/user-attachments/assets/893c2d7b-bbf1-4178-87b3-7ec82785288d)

This project demonstrates the implementation of a full-stack DevSecOps pipeline for a containerized application. It transforms a standard React-based game into a 3-tier architecture with state persistence, observability, and production-grade security controls.

Application Tiers:
- **Frontend**: React (Vite)
- **Backend**: FastAPI (Python)
- **Database**: Redis

After decoupling the application into these three tiers and verifying functionality using unit tests, I containerized the frontend and backend using multi-stage Docker builds and Distroless images to reduce image size and enhance container security.

Next, I implemented a CI/CD pipeline using GitHub Actions to automate testing, security scanning, and deployment. On every push:
- Unit tests and linting are run
- Docker images are built and scanned with Trivy
- Clean builds are published to GitHub Container Registry (GHCR)

A custom Bash script retrieves the updated image tags from GHCR and injects them into the Helm values.yaml file.

Using Helm, I templated Kubernetes manifests for consistency and maintainability. ArgoCD automatically detects changes to the Helm values, renders the manifests, and deploys the application to a local Kubernetes cluster (KIND).

Once the app was running in Kubernetes, I focused on networking and workload security:
- HTTPS/TLS termination for NGINX Ingress Controllers using Cert-Manager
- Kubernetes Secrets with RBAC-bound ServiceAccounts for credentials like Redis passwords
- PodSecurityContexts to enforce non-root container execution
- Calico NetworkPolicies for strict ingress/egress controls, enforcing least privilege between pods

To simulate real-world SRE workflows, I added full-stack observability:
- Custom app-level metrics exposed via a /metrics endpoint in the backend
- Prometheus configured with a ServiceMonitor to scrape those metrics
- Grafana dashboard visualizing:
  - Game stats (win ratios, fairness indicators, invalid moves)
  - API performance (latency, errors)
  - Kubernetes resource usage (CPU, memory, pod restarts)

This project simulates the tooling and workflows of a production-like DevSecOps pipeline, integrating CI/CD, GitOps, Kubernetes, securtiy, and observability.

---

## CI/CD

![CI/CD Pipeline](https://github.com/user-attachments/assets/ed3452f3-0619-4edd-9570-0fed39cc3c1f)

- GitHub Actions runs unit tests, linters, and vulnerability scans (via Trivy) on every push.
- If checks pass, secure multi-stage distroless Docker images are built using the Dockerfiles I wrote for the frontend and backend.
- Images are pushed to GitHub Container Registry (GHCR).
- A script updates the Helm values.yaml file with the new image tags using yq and commits the change.
- ArgoCD detects the change and automatically syncs the updated manifests to the local Kubernetes (KIND) cluster.

---

## Architecture

![Architecture Diagram](https://github.com/user-attachments/assets/6a1ac8b5-6fad-4294-99c0-ed88b41db614)

- All user traffic enters through an NGINX Ingress Controller with HTTPS/TLS termination (via Cert-Manager).
- Prometheus and Grafana are served to monitoring admins using their own respective NGINX Ingress Controllers.
- The FastAPI backend exposes "/api" endpoints for the frontend and a "/metrics" endpoint for Prometheus.
- Backend pods communicate with redis pods to store and load game state.
- Kubernetes Secrets store sensitive environment variables like Redis host name and password.
- RBAC and PodSecurityContexts limit pod access and enforce non-root containers with read-only filesystems.

---

## Security

- HTTPS/TLS termination with NGINX Ingress and Cert-Manager to encrypt traffic in transit.
- Kubernetes Secrets used to manage sensitive values like the Redis password.
- PodSecurityContexts enforce non-root containers and read-only root container filesystems.
- RBAC roles bound to ServiceAccounts restrict pod access to Secrets and other resources.
- Calico NetworkPolicies control pod-to-pod network communication using least-privilege principles.
- Trivy image scans integrated into the CI/CD pipeline to detect vulnerabilities before deployment.
- ArgoCD GitOps model with limited cluster permissions ensures secure deployments.

---

## Observability

Prometheus scrapes metrics from both the Kubernetes cluster and the application. Grafana uses those metrics to populate custom dashboards that provide real-time observability.

---

**Infrastructure Metrics**

![image](https://github.com/user-attachments/assets/0909f021-0859-4f65-9a85-196b7f091f11)

- Monitors:
  - Pod-level CPU and memory usage
  - Node-level resource consumption (CPU & RAM)
  - Pod uptime and restart counts

---

**API Metrics**

![image](https://github.com/user-attachments/assets/f93108f3-3f5d-4dab-9ac8-93ff9cfc038b)

- Monitors:
  - API request volume and latency
  - Error rates, including invalid moves and 5xx responses
  - Payload size trends across requests and responses

---

**App Metrics**

![image](https://github.com/user-attachments/assets/43890586-8dbd-4360-9ce9-a7b1eb0bbe98)

- Monitors:
  - Win/draw ratios to measure gameplay outcomes
  - Fairness indicator, monitoring imbalance between players over time
  - Game reset frequency, useful for detecting user frustration or abuse
  - Invalid move attempts (e.g., /api/move/99) for bug detection and potential exploit attempts
  - Total games played, providing insight into app engagement and volume

---

## Setup Instructions

This project runs locally on a Kubernetes cluster using KIND (Kubernetes IN Docker).

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

### 7. Access the Application 

- Access the application at https://tic-tac-toe.local

### 8. Access Monitoring Resources

- Access Grafana at https://grafana.local
- Access Prometheus at https://prometheus.local

1. Open the Grafana UI.
2. Import the Grafana dashboard json file (TicTacToe_Grafana.json) in the Grafana web UI.
3. View real-time data for infrastructure, API usage, and game statistics.

### 9. Install Cert-Manager for TLS Certificates

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.17.2/cert-manager.yaml
```

This enables automated TLS certificate issuance for ingress routes.


### 10. Configure GitHub Container Registry Pull Secrets

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

## Testing Network Policies

This test demonstrates that frontend pods are restricted from accessing the internet and backend pods directly, validating that network policies are in effect.

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

## Future Improvements
* **Provisioning:** Utilize Terraform for Infrastructure-as-Code (IaC) on cloud providers like AWS (EKS).
* **Secret Management:** Move from Kubernetes Secrets to external managers like HashiCorp Vault or AWS KMS for encryption at rest.

---

## Acknowledgements

This project expanded upon concepts from [DevSecOps CI/CD Pipeline Implementation](https://www.youtube.com/watch?v=Ke_Wr5zPE0A&list=PLdpzxOOAlwvLm5lWlYctUnwaFRIO2Io_5&index=7)

---


