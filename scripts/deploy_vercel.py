import os
import httpx
import json
import sys

VERCEL_TOKEN = os.getenv("VERCEL_TOKEN", "")
TEAM_ID = os.getenv("VERCEL_TEAM_ID", "")
BACKEND_URL = os.getenv("BACKEND_URL", "https://ap-agent-backend-bblt.onrender.com")

headers = {
    "Authorization": f"Bearer {VERCEL_TOKEN}",
    "Content-Type": "application/json"
}

params = {"teamId": TEAM_ID}

# 1. Create or get Project
project_name = "ap-agent"
print(f"Creating project '{project_name}' on Vercel...")

payload = {
    "name": project_name,
    "framework": "vite",
    "rootDirectory": "frontend",
    "gitRepository": {
        "type": "github",
        "repo": "sudarshan-jyotik/kivi"
    },
    "environmentVariables": [
        {
            "key": "VITE_API_URL",
            "value": BACKEND_URL,
            "target": ["production", "preview", "development"],
            "type": "plain"
        }
    ]
}

create_res = httpx.post("https://api.vercel.com/v9/projects", headers=headers, params=params, json=payload, timeout=30.0)
print("Create project status:", create_res.status_code)

if create_res.status_code in [200, 201]:
    project_data = create_res.json()
    project_id = project_data["id"]
    print("Project created successfully:", project_id)
elif create_res.status_code == 409:
    print("Project already exists. Fetching existing project...")
    get_res = httpx.get(f"https://api.vercel.com/v9/projects/{project_name}", headers=headers, params=params)
    project_data = get_res.json()
    project_id = project_data["id"]
else:
    print("Error creating project:", create_res.text)
    # Retry with name ap-agent-frontend
    project_name = "ap-agent-frontend"
    payload["name"] = project_name
    retry_res = httpx.post("https://api.vercel.com/v9/projects", headers=headers, params=params, json=payload, timeout=30.0)
    print("Retry create status:", retry_res.status_code)
    project_data = retry_res.json()
    project_id = project_data.get("id")

print(f"Project ID: {project_id}, Name: {project_name}")

# 2. Trigger Deployment via Vercel Deployments API
print("Triggering deployment on Vercel...")
deploy_payload = {
    "name": project_name,
    "project": project_id,
    "target": "production",
    "gitSource": {
        "type": "github",
        "repo": "sudarshan-jyotik/kivi",
        "ref": "main"
    }
}

deploy_res = httpx.post("https://api.vercel.com/v13/deployments", headers=headers, params=params, json=deploy_payload, timeout=30.0)
print("Deploy API status:", deploy_res.status_code)
deploy_data = deploy_res.json()
print("Deploy Response:", json.dumps(deploy_data, indent=2))
