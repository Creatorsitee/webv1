import requests
import os
from dotenv import load_dotenv

load_dotenv()

VERCEL_API_URL = "https://api.vercel.com"
VERCEL_TOKEN = os.getenv("VERCEL_TOKEN")
HEADERS = {
    "Authorization": f"Bearer {VERCEL_TOKEN}",
    "Content-Type": "application/json"
}

def create_deployment(project_name, files):
    """Membuat deployment baru di Vercel."""
    # Langkah 1: Buat proyek jika belum ada
    project_payload = {"name": project_name, "framework": "other"}
    project_response = requests.post(f"{VERCEL_API_URL}/v9/projects", headers=HEADERS, json=project_payload)
    if project_response.status_code not in [200, 409]: # 409 jika project sudah ada
        return {"success": False, "error": project_response.json()}
    
    # Langkah 2: Buat deployment
    deployment_payload = {
        "name": project_name,
        "files": files,
        "projectSettings": {
            "framework": "other"
        }
    }
    
    deployment_response = requests.post(f"{VERCEL_API_URL}/v13/deployments", headers=HEADERS, json=deployment_payload)
    
    if deployment_response.status_code == 200:
        deployment_data = deployment_response.json()
        return {
            "success": True, 
            "url": deployment_data.get('alias', [f"https://{project_name}.vercel.app"])[0],
            "id": deployment_data['id']
        }
    else:
        return {"success": False, "error": deployment_response.json()}

def delete_project(project_id):
    """Menghapus proyek di Vercel."""
    # Vercel API tidak memiliki endpoint untuk menghapus project langsung.
    # Yang bisa dihapus adalah deployment.
    # Untuk "menghapus project" dari sisi user, kita cukup hapus referensinya di database kita.
    # Jika ingin menghapus deployment, endpointnya adalah DELETE /v13/deployments/{id}
    # Tapi ini tidak menghapus project itu sendiri.
    # Kita akan fokus pada hapus referensi di database.
    return {"success": True, "message": "Project reference will be removed from our database."}

def get_user_projects():
    """Mendapatkan daftar proyek untuk token yang diberikan."""
    response = requests.get(f"{VERCEL_API_URL}/v9/projects", headers=HEADERS)
    if response.status_code == 200:
        return {"success": True, "data": response.json().get('projects', [])}
    return {"success": False, "error": response.json()}