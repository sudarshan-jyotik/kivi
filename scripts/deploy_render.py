import os
import httpx
import json
import sys

RENDER_API_KEY = os.getenv("RENDER_API_KEY", "")
OWNER_ID = os.getenv("RENDER_OWNER_ID", "")
REPO_URL = os.getenv("RENDER_REPO_URL", "https://github.com/sudarshan-jyotik/kivi")

headers = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Content-Type": "application/json"
}

# 1. Check if service already exists
r = httpx.get("https://api.render.com/v1/services", headers=headers)
services = r.json()

existing_service = None
for item in services:
    srv = item.get("service", {})
    if srv.get("name") == "ap-agent-backend" or "kivi" in srv.get("repo", ""):
        existing_service = srv
        break

if existing_service:
    print(f"Service already exists: {existing_service.get('id')} ({existing_service.get('name')})")
    print(f"URL: {existing_service.get('serviceDetails', {}).get('url')}")
    service_id = existing_service.get("id")
else:
    print("Creating new web service on Render...")
    payload = {
        "type": "web_service",
        "name": "ap-agent-backend",
        "ownerId": OWNER_ID,
        "repo": REPO_URL,
        "branch": "main",
        "rootDir": "backend",
        "autoDeploy": "yes",
        "serviceDetails": {
            "env": "docker",
            "plan": "free",
            "region": "oregon",
            "healthCheckPath": "/health",
            "envSpecificDetails": {
                "dockerfilePath": "./Dockerfile",
                "dockerContext": "."
            },
            "envVars": [
                {"key": "SARVAM_API_KEY", "value": "sk_5hd4kyr9_RfWd9jKKPJ2TgVxpMCS40atI"},
                {"key": "SARVAM_MODEL", "value": "sarvam-105b-conversations"},
                {"key": "SARVAM_BASE_URL", "value": "https://api.sarvam.ai/v1"},
                {"key": "DATABASE_URL", "value": "sqlite:///./data/ap_agent.db"},
                {"key": "ALLOWED_ORIGINS", "value": "http://localhost:5173,http://localhost:3000,*"}
            ]
        }
    }

    create_res = httpx.post("https://api.render.com/v1/services", headers=headers, json=payload, timeout=30.0)
    print("Create status:", create_res.status_code)
    try:
        created_data = create_res.json()
        print("Response:", json.dumps(created_data, indent=2))
        service_id = created_data.get("id")
    except Exception as e:
        print("Raw response:", create_res.text)
        sys.exit(1)

# Trigger a deploy
if service_id:
    print(f"Triggering deployment for service {service_id}...")
    deploy_res = httpx.post(f"https://api.render.com/v1/services/{service_id}/deploys", headers=headers, json={}, timeout=30.0)
    print("Deploy trigger status:", deploy_res.status_code)
    print(deploy_res.text)

