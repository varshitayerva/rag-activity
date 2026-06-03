"""
Demo chunks for RAG operations - Technical Support Knowledge Base
"""

DEMO_CHUNKS = [
    {
        'chunk_id': 'chunk_001',
        'text': 'ImagePullBackOff error occurs when a Kubernetes pod cannot pull its container image from the registry. This is one of the most common pod startup issues. Solutions: 1) Verify image name and tag are correct in pod spec. 2) Check image registry credentials and imagePullSecrets. 3) Ensure the image exists in the registry. 4) Check network connectivity to registry (firewall, DNS). 5) Check image size limits.',
        'doc_id': 'k8s-errors-guide',
        'filename': 'kubernetes-troubleshooting.md',
        'section': 'Pod Errors',
        'page': 1,
        'department': 'platform',
        'category': 'kubernetes',
        'uploaded_at': '2024-01-15'
    },
    {
        'chunk_id': 'chunk_002',
        'text': 'CrashLoopBackOff error means your pod is crashing and Kubernetes is restarting it in a loop. This indicates your application is failing immediately after startup. Debug steps: 1) Check pod logs with kubectl logs <pod-name>. 2) Look for application errors, null pointer exceptions, configuration issues. 3) Check resource limits (memory, CPU). 4) Verify environment variables are set. 5) Check startup probes and liveness probes configuration.',
        'doc_id': 'k8s-errors-guide',
        'filename': 'kubernetes-troubleshooting.md',
        'section': 'Pod Errors',
        'page': 2,
        'department': 'platform',
        'category': 'kubernetes',
        'uploaded_at': '2024-01-15'
    },
    {
        'chunk_id': 'chunk_003',
        'text': 'Pod eviction happens when a node runs out of resources (memory or disk) and Kubernetes needs to free up space. Evicted pods are automatically recreated on other nodes. Prevention: 1) Set resource requests and limits on all pods. 2) Monitor node resource usage. 3) Use pod disruption budgets for critical workloads. 4) Configure horizontal pod autoscaling. 5) Use node affinity to distribute load.',
        'doc_id': 'k8s-guide',
        'filename': 'kubernetes-operations.md',
        'section': 'Resource Management',
        'page': 5,
        'department': 'platform',
        'category': 'kubernetes',
        'uploaded_at': '2024-01-20'
    },
    {
        'chunk_id': 'chunk_004',
        'text': 'RBAC permission denied errors occur when your service account lacks the necessary permissions to access Kubernetes resources. Fix: 1) Create a Role or ClusterRole with required verbs (get, list, watch, create, delete). 2) Bind it to your service account using RoleBinding or ClusterRoleBinding. 3) Verify with kubectl auth can-i check. 4) Use kubectl get role and kubectl get rolebinding to debug.',
        'doc_id': 'k8s-security-guide',
        'filename': 'kubernetes-security.md',
        'section': 'Access Control',
        'page': 8,
        'department': 'security',
        'category': 'kubernetes',
        'uploaded_at': '2024-01-18'
    },
    {
        'chunk_id': 'chunk_005',
        'text': 'Database connection timeout issues usually mean your application cannot establish a connection to the database within the timeout period. Common causes: 1) Database service is not running or reachable. 2) Network connectivity issues (firewall rules, DNS resolution). 3) Incorrect connection string or credentials. 4) Database is overloaded and not accepting connections. 5) Connection pool is exhausted. Solution: Increase timeout, check logs, verify service endpoints.',
        'doc_id': 'db-troubleshooting',
        'filename': 'database-guide.md',
        'section': 'Connection Issues',
        'page': 12,
        'department': 'database',
        'category': 'postgresql',
        'uploaded_at': '2024-02-01'
    },
    {
        'chunk_id': 'chunk_006',
        'text': 'Restarting a pod is useful for applying configuration changes or recovering from transient issues. Methods: 1) kubectl rollout restart deployment/<name> - Restarts all pods in deployment. 2) kubectl delete pod <pod-name> - Deletes the pod, which is recreated by controller. 3) kubectl patch pod - Modifies pod spec to trigger restart. 4) For StatefulSets use kubectl rollout restart statefulset/<name>. Note: Always use deployment/statefulset restart for managed pods.',
        'doc_id': 'k8s-operations',
        'filename': 'kubernetes-operations.md',
        'section': 'Pod Management',
        'page': 3,
        'department': 'platform',
        'category': 'kubernetes',
        'uploaded_at': '2024-01-16'
    },
    {
        'chunk_id': 'chunk_007',
        'text': 'ConfigMap is a Kubernetes object for storing non-sensitive configuration data as key-value pairs. Usage: 1) Create with kubectl create configmap <name> --from-literal=key=value. 2) Mount as files in volumes. 3) Expose as environment variables. 4) Update with kubectl patch configmap. 5) Reference from deployments using envFrom or volumeMounts. Example: env: [{name: DB_HOST, valueFrom: {configMapKeyRef: {name: db-config, key: host}}}]',
        'doc_id': 'k8s-guide',
        'filename': 'kubernetes-configuration.md',
        'section': 'Configuration',
        'page': 15,
        'department': 'platform',
        'category': 'kubernetes',
        'uploaded_at': '2024-02-03'
    },
    {
        'chunk_id': 'chunk_008',
        'text': 'Pending pod status means the pod is waiting for a resource to become available before it can be scheduled. Common reasons: 1) Insufficient CPU or memory on nodes. 2) Pod affinity/anti-affinity constraints cannot be satisfied. 3) Persistent volume not available. 4) Image pull secret missing. Debugging: kubectl describe pod <name> shows events explaining why pod is pending.',
        'doc_id': 'k8s-errors-guide',
        'filename': 'kubernetes-troubleshooting.md',
        'section': 'Pod Errors',
        'page': 4,
        'department': 'platform',
        'category': 'kubernetes',
        'uploaded_at': '2024-01-17'
    },
    {
        'chunk_id': 'chunk_009',
        'text': 'Service mesh with Istio provides advanced traffic management, security policies, and observability for microservices. Setup: 1) Install Istio on your cluster. 2) Enable sidecar injection with kubectl label namespace default istio-injection=enabled. 3) Create VirtualService and DestinationRule for traffic management. 4) Use AuthorizationPolicy for service-to-service authentication. 5) Monitor with Kiali, Prometheus, and Jaeger integrations.',
        'doc_id': 'k8s-advanced',
        'filename': 'kubernetes-advanced-networking.md',
        'section': 'Service Mesh',
        'page': 20,
        'department': 'platform',
        'category': 'kubernetes',
        'uploaded_at': '2024-02-05'
    },
    {
        'chunk_id': 'chunk_010',
        'text': 'OOMKilled (Out of Memory) error indicates your container exceeded its memory limit. Solutions: 1) Increase memory limit in pod spec (resources.limits.memory). 2) Optimize application to use less memory (memory leaks, inefficient algorithms). 3) Add memory requests for proper scheduling (resources.requests.memory). 4) Use horizontal pod autoscaling to distribute load. 5) Implement memory profiling and monitoring with Prometheus.',
        'doc_id': 'k8s-troubleshooting',
        'filename': 'kubernetes-troubleshooting.md',
        'section': 'Resource Errors',
        'page': 6,
        'department': 'platform',
        'category': 'kubernetes',
        'uploaded_at': '2024-01-22'
    },
    {
        'chunk_id': 'chunk_011',
        'text': 'Helm is a package manager for Kubernetes that helps manage complex applications using charts. Basic commands: 1) helm install <release> <chart> - Deploy application. 2) helm upgrade <release> <chart> - Update application. 3) helm rollback <release> <revision> - Revert to previous version. 4) helm values <chart> - View default values. 5) helm dependency update - Update chart dependencies. Charts are reusable and support parameterization.',
        'doc_id': 'k8s-deploy-guide',
        'filename': 'kubernetes-deployment.md',
        'section': 'Deployment Tools',
        'page': 18,
        'department': 'devops',
        'category': 'kubernetes',
        'uploaded_at': '2024-02-02'
    },
    {
        'chunk_id': 'chunk_012',
        'text': 'Persistent Volume (PV) and Persistent Volume Claim (PVC) provide durable storage for pods. Workflow: 1) Admin creates PV with storage capacity and access mode. 2) Developer creates PVC requesting storage. 3) Kubernetes binds PVC to suitable PV. 4) Pod mounts PVC as volume. Access modes: ReadWriteOnce, ReadOnlyMany, ReadWriteMany. Storage classes automate PV provisioning with different performance tiers.',
        'doc_id': 'k8s-storage',
        'filename': 'kubernetes-storage.md',
        'section': 'Persistent Storage',
        'page': 10,
        'department': 'platform',
        'category': 'kubernetes',
        'uploaded_at': '2024-01-25'
    },
    {
        'chunk_id': 'chunk_013',
        'text': 'Ingress controller manages external HTTP/HTTPS access to services in Kubernetes. Setup: 1) Install ingress controller (nginx, traefik, aws-alb). 2) Create Ingress resource defining routes and TLS. 3) Map domain names to services. 4) Configure SSL/TLS certificates. 5) Set up rate limiting, authentication, and traffic management. Example: apiVersion: networking.k8s.io/v1, kind: Ingress, spec: rules with hosts and paths.',
        'doc_id': 'k8s-networking',
        'filename': 'kubernetes-networking.md',
        'section': 'Ingress',
        'page': 14,
        'department': 'platform',
        'category': 'kubernetes',
        'uploaded_at': '2024-01-28'
    },
    {
        'chunk_id': 'chunk_014',
        'text': 'Memory leak in application causes gradual increase in memory usage until OOMKilled. Detection: 1) Monitor memory metrics in Prometheus. 2) Use kubectl top pod to see current memory. 3) Generate heap dumps from container. 4) Analyze with profiling tools. Common causes: 1) Unbounded caches. 2) Circular references preventing garbage collection. 3) Event listeners not unregistered. 4) Stream resources not closed. Fix by code review and testing.',
        'doc_id': 'troubleshooting-guide',
        'filename': 'debugging-guide.md',
        'section': 'Performance Issues',
        'page': 22,
        'department': 'engineering',
        'category': 'debugging',
        'uploaded_at': '2024-02-04'
    },
    {
        'chunk_id': 'chunk_015',
        'text': 'Network policy in Kubernetes restricts traffic between pods and external endpoints. Implementation: 1) Create NetworkPolicy object specifying podSelector, policyTypes (Ingress/Egress). 2) Define rules with allowed sources/destinations. 3) Use namespaceSelector for cross-namespace rules. 4) Default deny-all then allow specific traffic. 5) Monitor with network plugins that support policies (Calico, Cilium). Helps implement zero-trust security.',
        'doc_id': 'k8s-security',
        'filename': 'kubernetes-security.md',
        'section': 'Network Security',
        'page': 11,
        'department': 'security',
        'category': 'kubernetes',
        'uploaded_at': '2024-01-30'
    }
]

def get_demo_chunks():
    """Return demo chunks for testing and development."""
    return DEMO_CHUNKS
