# Task 2
## 1. Environment and Prerequisites

### 1.1 Create VMs
We will create Kubernetes cluster with one master and one worker with the below setup:

| Node Name     | CPU | RAM  | IP               | Role          |
| ------------- | --- | ---- | ---------------- | ------------- |
| k8s-master-01 | 2   | 2 GB | 192.168.8.200/24 | Control Plane |
| k8s-worker-01 | 2   | 2 GB | 192.168.8.201/24 | Worker Node   |
### 1.2 VMs configuration
On all VMs we need to run the below configuration.
1. Load necessary kernel modules:
   Enable `overlay` and `br_netfilter` modules:
   ```shell
	modprobe overlay
	modprobe br_netfilter
   ```
   Verify that module are loaded successfuly:
   ```shell
   lsmod | grep -E 'overlay|br_netfilter'
   ```
   Make it persist across reboot:
   ```shell
	cat <<EOF | tee /etc/modules-load.d/k8s.conf
	overlay
	br_netfilter
	EOF
   ```
   
2. Configure sysctl networking parameters:
   Enable `bridge-nf-call `and `ip_forward`:
   ```shell
   cat <<EOF | tee /etc/sysctl.d/k8s.conf
	net.bridge.bridge-nf-call-iptables = 1
	net.bridge.bridge-nf-call-ip6tables = 1
	net.ipv4.ip_forward = 1
	EOF
   ```
   Apply the configuration without rebooting:
   ```shell
   sudo sysctl --system
   ```
   Verify the configuration:
   ```shell
   sudo sysctl net.bridge.bridge-nf-call-iptables  --> net.bridge.bridge-nf-call-iptables = 1
   
   sudo sysctl net.ipv4.ip_forward  -->  net.ipv4.ip_forward = 1
   ```
   
1. Resolve nodes hostname:
   ```shell
   cat <<EOF >> /etc/hosts
   192.168.8.200 k8s-master-01
   192.168.8.201 k8s-worker-01
   EOF
   ```

## 2. Package Installation

### 2.1 Install `containerd`:
   ```shell
   sudo apt-get update
   sudo apt-get install -y containerd
   ```
   Configure containerd:
   ```shell
	# Create default configuration
	sudo mkdir -p /etc/containerd
	containerd config default | sudo tee /etc/containerd/config.toml
	
	# Enable systemd cgroup driver
	sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
	
	# Verify the change
	cat /etc/containerd/config.toml | grep -i systemdcgroup
   ```
   Start containerd:
   ```shell
   systemctl daemon-reload
   systemctl enable --now containerd
   systemctl status containerd --no-pager
   ```
### 2.2 Install `kubeadm`, `kubelet`, and `kubectl`:
  ```shell
# Update the apt index and install necessary transport tools
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl gpg

# Create the keyrings directory if it doesn't exist
sudo mkdir -p -m 755 /etc/apt/keyrings

# Download the official public signing key
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.34/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

# Add the appropriate Kubernetes apt repository 
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.34/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list

# Update the package index and install the binaries
sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl

# Hold the packages to prevent accidental updates
sudo apt-mark hold kubelet kubeadm kubectl

# Enable kubelet service
systemctl enable --now kubelet
  ```

## 3. Control Plane Initialization (kubeadm init)

### 3.1 Init Setup:
```shell
kubeadm init --apiserver-advertise-address=192.168.8.200 --pod-network-cidr=10.244.0.0/16 --service-cidr=10.96.0.0/12 --skip-phases=addon/kube-proxy --kubernetes-version=1.32.13
```

### 3.2 Post-Init Setup:
Copy `kubeconfig` file to access the cluster:
```shell
mkdir -p /root/.kube  
cp -i /etc/kubernetes/admin.conf /root/.kube/config  
chown $(id -u):$(id -g) /root/.kube/config
```

### 3.3 Verification
Get cluster info:
```shell
kubectl cluster-info
```

Get nodes info:
```shell
kubectl get nodes -owide 
```
Note: The node show NotReady as the CNI is not installed yet

## 4. CNI Installation

We will use cilium CNI.
### 4.1 Install Helm
```shell
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

### 4.2 Install Cilium CLI
```shell
CILIUM_CLI_VERSION=$(curl -s https://raw.githubusercontent.com/cilium/cilium-cli/main/stable.txt)
CLI_ARCH=amd64
if [ "$(uname -m)" = "aarch64" ]; then CLI_ARCH=arm64; fi
curl -L --fail --remote-name-all https://github.com/cilium/cilium-cli/releases/download/${CILIUM_CLI_VERSION}/cilium-linux-${CLI_ARCH}.tar.gz{,.sha256sum}
sha256sum --check cilium-linux-${CLI_ARCH}.tar.gz.sha256sum
sudo tar xzvfC cilium-linux-${CLI_ARCH}.tar.gz /usr/local/bin
rm cilium-linux-${CLI_ARCH}.tar.gz{,.sha256sum}
```

### 4.3 Install cilium
Create cilium config file:
```shell
cat << EOF > cilium-values.yaml
# Since we skipped kube-proxy, makes Cilium handle Kubernetes Service routing using eBPF.
kubeProxyReplacement: true

# Kubernetes API Server
k8sServiceHost: "192.168.8.200"
k8sServicePort: 6443

# Pod IP address allocation
ipam:
  mode: cluster-pool
  operator:
    clusterPoolIPv4PodCIDRList:
      - "10.244.0.0/16"
    clusterPoolIPv4MaskSize: 24
# Single-node cluster
operator:
  replicas: 1

# Enable local Layer 2 announcements
l2announcements:
  enabled: true

# API client limits for L2 announcement functionality
k8sClientRateLimit:
  qps: 20
  burst: 40
EOF
```

Setup Helm repository:
```helm
helm repo add cilium https://helm.cilium.io/
```

Deploy Cilium via Helm:
```helm
helm install cilium cilium/cilium --version 1.20.3 --namespace kube-system --values cilium-values.yaml
```

Validate the Installation:
```shell
# Manually verify:
kubectl -n kube-system get pods --watch

# Using Cilium CLI:
ciliuum status --wait
```

### 4.4 Configure LB IPAM
Create pool:
```shell
cat << EOF > lb-ip-pool.yaml
apiVersion: cilium.io/v2
kind: CiliumLoadBalancerIPPool
metadata:
  name: lab-pool
spec:
  blocks:
    - start: 192.168.8.210
      stop: 192.168.8.220
EOF

kubectl apply -f lb-ip-pool.yaml
```

Configure L2 announcements Policy:
```shell
cat << EOF > l2-policy.yaml
apiVersion: cilium.io/v2alpha1
kind: CiliumL2AnnouncementPolicy
metadata:
  name: ingress-l2-policy
spec:
  serviceSelector:
    matchLabels:
      exposure: l2
  interfaces:
    - ^enp2s0$
  externalIPs: false
  loadBalancerIPs: true
EOF

kubectl apply -f l2-policy.yaml
```

## 5. Join worker node to cluster
On the control node run the below to generate the join command:
```shell
sudo kubeadm token create --print-join-command
```

Take the output from the above command and run it on the worker node to joing: 
```shell
kubeadm join 192.168.8.200:6443 --token brwllv.k9b7ffe8iyjun98k --discovery-token-ca-cert-hash sha256:7a2a91a2e74373c96c40a634bbaf662d161739e87d738e81de534132294c9dde
```


## 6. Install Ingress-Nginx
Setup Helm repository:
```helm
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
```

Deploy ingress-nginx via Helm:
```helm
helm install ingress-nginx ingress-nginx/ingress-nginx --version 4.15.1 --namespace ingress-nginx --create-namespace
```

Expose ingress controller, so cilium will use announce its IP using `CiliumL2AnnouncementPolicy` policy.
```shell
kubectl label svc ingress-nginx-controller -n ingress-nginx exposure=l2
```

Get ingress controller IP:
```shell
kubectl get svc ingress-nginx-controller -n -ingress-nginx
```
This is the ingress controller IP that will be used to access any service/app behind the ingress

## 7. Deploy juice-shop app

Create `juice-shop.yaml` file with the below content:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: juice-shop
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: juice-shop
  namespace: juice-shop
spec:
  replicas: 1
  selector:
    matchLabels:
      app: juice-shop
  template:
    metadata:
      labels:
        app: juice-shop
    spec:
      containers:
        - name: juice-shop
          image: bkimminich/juice-shop:latest
          ports:
            - containerPort: 3000
          readinessProbe:
            httpGet:
              path: /
              port: 3000
            initialDelaySeconds: 10
            periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: juice-shop-svc
  namespace: juice-shop
spec:
  type: ClusterIP
  selector:
    app: juice-shop
  ports:
    - port: 3000
      targetPort: 3000
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: juice-shop
  namespace: juice-shop
spec:
  ingressClassName: nginx
  rules:
    - host: juice-shop.local
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: juice-shop-svc
                port:
                  number: 3000
```

