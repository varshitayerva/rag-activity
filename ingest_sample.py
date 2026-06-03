#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Ingest sample documents."""

import os
import sys
from pathlib import Path
from typing import Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Fix encoding on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from backend.app.ingestion.ingest import DocumentIngester


def create_sample_docs():
    """Create sample documents for testing."""
    samples_dir = Path("sample_docs")
    samples_dir.mkdir(exist_ok=True)

    # Sample 1: Kubernetes Guide
    k8s_content = """Kubernetes Basics

What is Kubernetes?

Kubernetes (K8s) is an open-source orchestration platform for automating
the deployment, scaling, and management of containerized applications.

Key Concepts

Pods
A Pod is the smallest deployable unit in Kubernetes. It wraps one or more containers.

Services
Services provide stable network identities for Pods and enable load balancing.

Deployments
Deployments manage the creation and scaling of Pods.

How to Restart a Pod

To restart a pod in Kubernetes:

1. Get the pod name:
   kubectl get pods

2. Delete the pod:
   kubectl delete pod <pod-name>

3. The deployment will automatically create a new pod

Alternatively, use:
   kubectl rollout restart deployment/<deployment-name>

ConfigMaps and Secrets

ConfigMaps store configuration data as key-value pairs.
Secrets store sensitive data like passwords and API keys.

Namespaces

Namespaces provide virtual clusters within a single Kubernetes cluster.

List namespaces:
   kubectl get namespaces

Create a namespace:
   kubectl create namespace <name>

Common kubectl Commands

- kubectl apply -f <file>: Apply configuration
- kubectl get <resource>: List resources
- kubectl describe <resource> <name>: Show details
- kubectl logs <pod-name>: View pod logs
- kubectl exec -it <pod-name> -- /bin/bash: Enter pod shell
"""

    with open(samples_dir / "kubernetes_basics.txt", "w", encoding='utf-8') as f:
        f.write(k8s_content)

    # Sample 2: Docker Guide
    docker_content = """Docker Guide

What is Docker?

Docker is a containerization platform that packages applications and dependencies.

Docker Images

A Docker image is a lightweight, standalone executable package.

Build an image:
   docker build -t myapp:1.0 .

List images:
   docker images

Docker Containers

A container is a runtime instance of an image.

Run a container:
   docker run -d --name mycontainer myapp:1.0

View running containers:
   docker ps

Stop a container:
   docker stop mycontainer

Remove a container:
   docker rm mycontainer

Docker Networking

Containers communicate through networks.

Create a network:
   docker network create mynetwork

Connect a container to network:
   docker run --network mynetwork --name app myimage

Docker Volumes

Volumes persist data between container restarts.

Create a volume:
   docker volume create myvolume

Mount a volume:
   docker run -v myvolume:/data myimage

Dockerfile

A Dockerfile defines how to build an image.

Example:
   FROM python:3.9
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   CMD ["python", "app.py"]

Docker Compose

Docker Compose defines multi-container applications.

Run with Compose:
   docker-compose up -d

Stop:
   docker-compose down
"""

    with open(samples_dir / "docker_guide.txt", "w", encoding='utf-8') as f:
        f.write(docker_content)

    # Sample 3: Python Best Practices
    python_content = """Python Best Practices

Code Style

Follow PEP 8 guidelines:
- Use 4 spaces for indentation
- Maximum line length: 79 characters
- Two blank lines between top-level definitions
- One blank line between methods

Virtual Environments

Always use virtual environments:

   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate    # Windows

Dependencies

Use requirements.txt:

   pip freeze > requirements.txt
   pip install -r requirements.txt

Type Hints

Use type hints for clarity:

   def add(a: int, b: int) -> int:
       return a + b

Error Handling

Handle exceptions appropriately:

   try:
       result = risky_operation()
   except SpecificException as e:
       handle_error(e)
   finally:
       cleanup()

Testing

Write tests for your code:

   import pytest

   def test_add():
       assert add(2, 3) == 5

Run tests:

   pytest tests/

Documentation

Write docstrings:

   def calculate_total(items: list) -> float:
       Calculate total from list of items.

       Args:
           items: List of numbers

       Returns:
           Sum of all items

       return sum(items)

Logging

Use logging instead of print:

   import logging

   logging.info("Operation started")
   logging.error("Operation failed")

Performance

- Use list comprehensions
- Avoid global variables
- Cache expensive computations
- Use appropriate data structures
"""

    with open(samples_dir / "python_practices.txt", "w", encoding='utf-8') as f:
        f.write(python_content)

    print(f"Created sample documents in {samples_dir}/")
    return samples_dir


def main():
    """Ingest sample documents."""
    print("=" * 60)
    print("FDE RAG - Sample Document Ingestion")
    print("=" * 60)
    print()

    # Create sample documents
    print("[1/3] Creating sample documents...")
    samples_dir = create_sample_docs()
    print()

    # Initialize ingester
    print("[2/3] Initializing ingester...")
    ingester = DocumentIngester()
    print("Ingester ready")
    print()

    # Ingest documents
    print("[3/3] Ingesting documents...")
    result = ingester.ingest_directory(str(samples_dir))

    print()
    print("=" * 60)
    print("Ingestion Results")
    print("=" * 60)
    print(f"Total files: {result['total_files']}")
    print(f"Successful: {result['successful']}")
    print()

    for i, res in enumerate(result['results'], 1):
        if res.get('success'):
            print(f"{i}. {res['filename']}")
            print(f"   Document ID: {res['doc_id']}")
            print(f"   Chunks: {res['chunks_created']}")
            print(f"   Embeddings: {res['embeddings_created']}")
        else:
            print(f"{i}. {res['filename']}")
            print(f"   Error: {res.get('error')}")
        print()

    print("=" * 60)
    print("Ready to search!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Start backend: python -m uvicorn backend.main:app --reload")
    print("2. Test search: http://localhost:8000/docs")
    print("3. Start frontend: cd frontend && npm run dev")
    print()


if __name__ == "__main__":
    main()
