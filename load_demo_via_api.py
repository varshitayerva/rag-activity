#!/usr/bin/env python3
"""
Load demo chunks via the API without needing OpenAI API.
Uses mock embeddings instead of real OpenAI embeddings.
"""

import requests
import json

DEMO_CHUNKS = [
    {
        "chunk_id": "chunk_001",
        "text": "Kubernetes Pod CrashLoopBackOff Error. Pod keeps crashing and restarting. Check container logs with kubectl logs pod-name. Common causes: missing environment variables, configuration issues, or application errors in the container startup script.",
        "doc_id": "doc_k8s_001",
        "filename": "kubernetes_guide.pdf",
        "section": "Pod Errors",
        "page": 1,
        "department": "Engineering",
        "category": "Kubernetes"
    },
    {
        "chunk_id": "chunk_002",
        "text": "Kubernetes Pod Pending Status. Pod remains in pending state and never starts. Check node resources with kubectl describe node. Ensure sufficient CPU and memory available. Check ImagePullBackOff errors for container images.",
        "doc_id": "doc_k8s_002",
        "filename": "kubernetes_guide.pdf",
        "section": "Pod Errors",
        "page": 2,
        "department": "Engineering",
        "category": "Kubernetes"
    },
    {
        "chunk_id": "chunk_003",
        "text": "Kubernetes Resource Management. Set resource requests and limits for pods using resources field in container spec. CPU measured in cores, memory in bytes. Requests are guaranteed, limits are maximum allowed.",
        "doc_id": "doc_k8s_003",
        "filename": "kubernetes_guide.pdf",
        "section": "Resource Management",
        "page": 5,
        "department": "Engineering",
        "category": "Kubernetes"
    },
    {
        "chunk_id": "chunk_004",
        "text": "Kubernetes RBAC Access Control. Role-based access control manages who can access what resources. Use ServiceAccounts, Roles, and RoleBindings to grant minimal necessary permissions. ClusterRoles for cluster-wide permissions.",
        "doc_id": "doc_k8s_004",
        "filename": "kubernetes_guide.pdf",
        "section": "Access Control",
        "page": 8,
        "department": "Engineering",
        "category": "Kubernetes"
    },
    {
        "chunk_id": "chunk_005",
        "text": "PostgreSQL Connection Issues. Cannot connect to database. Verify connection string format. Check if PostgreSQL service is running. Ensure firewall allows port 5432. Verify username and password credentials are correct.",
        "doc_id": "doc_db_001",
        "filename": "database_guide.pdf",
        "section": "Connection Issues",
        "page": 1,
        "department": "Backend",
        "category": "PostgreSQL"
    },
    {
        "chunk_id": "chunk_006",
        "text": "Kubernetes Pod Management. Create pods with kubectl run. Delete pods with kubectl delete pod. View pod logs with kubectl logs. Execute commands in running pods with kubectl exec. Monitor pod status with kubectl get pods.",
        "doc_id": "doc_k8s_005",
        "filename": "kubernetes_guide.pdf",
        "section": "Pod Management",
        "page": 12,
        "department": "Engineering",
        "category": "Kubernetes"
    },
    {
        "chunk_id": "chunk_007",
        "text": "Kubernetes Configuration Management. ConfigMaps store non-sensitive configuration data. Secrets store sensitive data like passwords. Mount as volumes or environment variables in pods. Use kubectl create configmap and kubectl create secret.",
        "doc_id": "doc_k8s_006",
        "filename": "kubernetes_guide.pdf",
        "section": "Configuration",
        "page": 15,
        "department": "Engineering",
        "category": "Kubernetes"
    },
    {
        "chunk_id": "chunk_008",
        "text": "Container Startup Failures. Check container exit codes. Exit 0 means success, others indicate errors. View detailed error messages in pod events with kubectl describe pod. Check container image exists and is accessible.",
        "doc_id": "doc_k8s_007",
        "filename": "kubernetes_guide.pdf",
        "section": "Pod Errors",
        "page": 20,
        "department": "Engineering",
        "category": "Kubernetes"
    },
    {
        "chunk_id": "chunk_009",
        "text": "Kubernetes Service Mesh with Istio. Manages service-to-service communication. Enables traffic management, security policies, and observability. Inject sidecar proxies for automatic handling of network communication between services.",
        "doc_id": "doc_k8s_008",
        "filename": "kubernetes_guide.pdf",
        "section": "Service Mesh",
        "page": 25,
        "department": "Engineering",
        "category": "Kubernetes"
    },
    {
        "chunk_id": "chunk_010",
        "text": "Out of Memory OOMKilled Errors. Container exceeded memory limit and was killed. Increase memory limit in resource constraints. Profile application memory usage. Look for memory leaks in application code. Monitor with kubectl top pods.",
        "doc_id": "doc_k8s_009",
        "filename": "kubernetes_guide.pdf",
        "section": "Resource Errors",
        "page": 28,
        "department": "Engineering",
        "category": "Kubernetes"
    },
    {
        "chunk_id": "chunk_011",
        "text": "Deployment and Rollout Strategies. Use Deployments for managing ReplicaSets. Rolling update updates pods gradually. Recreate strategy deletes old pods before creating new ones. Monitor rollout status with kubectl rollout status deployment.",
        "doc_id": "doc_k8s_010",
        "filename": "kubernetes_guide.pdf",
        "section": "Deployment Tools",
        "page": 30,
        "department": "Engineering",
        "category": "Kubernetes"
    },
    {
        "chunk_id": "chunk_012",
        "text": "Persistent Volumes and Claims. PersistentVolume provides storage resource. PersistentVolumeClaim requests storage. Pods mount PVCs for persistent data. StorageClass defines volume provisioning. Supports NFS, EBS, Azure Disk backends.",
        "doc_id": "doc_k8s_011",
        "filename": "kubernetes_guide.pdf",
        "section": "Persistent Storage",
        "page": 35,
        "department": "Engineering",
        "category": "Kubernetes"
    },
    {
        "chunk_id": "chunk_013",
        "text": "Kubernetes Ingress Controller. Routes external traffic to services. Define rules for hostname and path-based routing. Supports TLS termination for HTTPS. NGINX Ingress Controller most commonly used implementation.",
        "doc_id": "doc_k8s_012",
        "filename": "kubernetes_guide.pdf",
        "section": "Ingress",
        "page": 40,
        "department": "Engineering",
        "category": "Kubernetes"
    },
    {
        "chunk_id": "chunk_014",
        "text": "Memory Leak Debugging Techniques. Application using increasing memory over time indicates memory leak. Use profiler tools to identify leaks. Check for unclosed file handles, unclosed database connections. Review cleanup in destructors and finalizers.",
        "doc_id": "doc_debug_001",
        "filename": "debugging_guide.pdf",
        "section": "Performance Issues",
        "page": 10,
        "department": "Engineering",
        "category": "Debugging"
    },
    {
        "chunk_id": "chunk_015",
        "text": "Network Security Best Practices. Use NetworkPolicies to restrict traffic between pods. Deny all ingress by default, allow specific traffic. Use service mesh for encrypted communication. TLS for external traffic. Regular security scanning of container images.",
        "doc_id": "doc_k8s_013",
        "filename": "kubernetes_guide.pdf",
        "section": "Network Security",
        "page": 45,
        "department": "Engineering",
        "category": "Kubernetes"
    }
]

def load_demo_data():
    """Load demo chunks via API."""
    print("\n" + "=" * 80)
    print("LOADING DEMO CHUNKS VIA API")
    print("=" * 80 + "\n")

    api_url = "http://localhost:8008/index"

    payload = {
        "chunks": DEMO_CHUNKS
    }

    try:
        print(f"Sending {len(DEMO_CHUNKS)} chunks to API...")
        response = requests.post(
            api_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print(f"\nSuccess! {result['num_chunks_indexed']} chunks indexed")
            print(f"Status: {result['status']}")
        else:
            print(f"\nError: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"\nFailed to connect to API: {e}")
        print("Make sure the server is running on http://localhost:8008")
        return False

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Chunks loaded: {len(DEMO_CHUNKS)}")
    for i, chunk in enumerate(DEMO_CHUNKS, 1):
        print(f"  {i:2d}. {chunk['chunk_id']:15s} - {chunk['section']:25s} ({chunk['category']})")

    print("\nYour database is ready for testing!")
    print("=" * 80 + "\n")
    return True

if __name__ == "__main__":
    load_demo_data()
