---
title: Kubernetes Troubleshooting Guide
category: Troubleshooting
department: Platform
---

# Kubernetes Troubleshooting Guide

## Database Connection Timeout

### Step 1: Check Pod Status
Verify that the database pod is running using kubectl get pods command. Look for the pod name in the output.

### Step 2: Verify Database Service
Ensure the database service is accessible by checking the service endpoints. The service must be in the ACTIVE state.

### Step 3: Database Connection Configuration
Check the connection string in your application environment variables. Common mistakes include incorrect hostname, port, or credentials.

The connection string should follow this format: `postgres://user:password@hostname:5432/database_name`

## ImagePullBackOff Error

### Understanding the Error
ImagePullBackOff occurs when Kubernetes cannot pull the container image from the registry. This is a temporary error that Kubernetes will retry.

### Step 1: Verify Image Exists
Ensure the image exists in your container registry. Use docker pull to test accessibility from your machine.

### Step 2: Check Registry Credentials
If using a private registry, verify that the ImagePullSecret is properly configured in your pod specification.

### Step 3: Verify Image URL
Double-check the image URL in your deployment manifest. Common issues include typos in the image name or tag.

The image URL should be in format: `registry.example.com/namespace/image:tag`

### Step 4: Check Network Connectivity
Verify that your cluster has outbound network access to the image registry. Network policies may be blocking access.

## Pod CrashLoopBackOff

### Initial Diagnosis
When a pod enters CrashLoopBackOff, it means the container is continuously crashing and being restarted.

### Step 1: Check Pod Logs
Use `kubectl logs <pod-name>` to view the container logs. The logs will show why the container is crashing.

### Step 2: Check Pod Events
Use `kubectl describe pod <pod-name>` to see recent events and error messages.

### Step 3: Resource Constraints
Check if the pod has sufficient memory and CPU. Increase resource requests if needed.

### Step 4: Health Probes
Review liveness and readiness probe configurations. They might be failing immediately after startup.

## RBAC Permission Denied

### Understanding RBAC
Role-Based Access Control (RBAC) restricts what actions a service account can perform in the cluster.

### Step 1: Check Service Account
Verify the service account is correctly specified in the pod specification.

### Step 2: Review Role and RoleBinding
Check that the service account has the appropriate Role or ClusterRole assigned via RoleBinding.

### Step 3: Required Permissions
Ensure the role has all necessary permissions for your application. Common required permissions include:
- get, list, watch on pods
- get on services
- patch on deployments

### Step 4: Test Permissions
Use `kubectl auth can-i <verb> <resource>` to test if a service account can perform an action.

## Network Policy Issues

### Step 1: Verify Network Policies Exist
List all network policies in the namespace: `kubectl get networkpolicies`

### Step 2: Check Policy Rules
Review the network policy rules that might be blocking traffic between pods.

### Step 3: Allow Required Traffic
Add network policy rules to allow communication between pods that need to communicate.

### Step 4: DNS Resolution
Ensure pods can resolve service names using DNS. Test with `nslookup servicename.namespace`

## Performance and Resource Issues

### Step 1: Check Node Resources
Verify that cluster nodes have available CPU and memory.

### Step 2: Monitor Pod Resources
Use `kubectl top pods` to see current resource usage of your pods.

### Step 3: Adjust Resource Requests
If resource usage is consistently high, increase the resource requests and limits in your deployment.

### Step 4: Horizontal Pod Autoscaling
Consider enabling HPA (Horizontal Pod Autoscaler) for automatic scaling based on metrics.
