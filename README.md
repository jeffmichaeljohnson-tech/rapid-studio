# Rapid Studio

A Python-based microservices platform for rapid content generation and validation.

## Architecture

This project consists of several microservices:

- **Orchestrator**: Main API service for job management
- **Assets API**: File upload and management service  
- **Runner GPU**: GPU-based content generation worker
- **Validator Lite**: Lightweight validation service
- **Validator Full**: Comprehensive validation service
- **Nginx**: Reverse proxy and load balancer

## Quick Start

1. Start all services using Docker Compose:
   ```bash
   cd deploy/compose
   docker-compose up -d
   ```

2. Access the services:
   - Orchestrator API: http://localhost:8000
   - Assets API: http://localhost:8080
   - Grafana Dashboard: http://localhost:3000
   - Prometheus Metrics: http://localhost:9090

## Development

This is a Python project using FastAPI. The `package.json` file exists only to satisfy tools that expect Node.js project structure.

For Python development, use the `requirements.txt` file to install dependencies.
