from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import secrets
import string
from dotenv import load_dotenv
from firebase import create_user, verify_token, get_user_profile, update_user_profile, store_vercel_project, get_vercel_projects, delete_vercel_project
from vercel import create_deployment, delete_project

load_dotenv()

app = Flask(__name__, static_folder='../static', template_folder='../templates')
CORS(app) # Mengizinkan request dari domain lain (frontend)

# --- Rute untuk Halaman Utama ---
@app.route('/')
def index():
    # Kirim Web API Key ke template
    return render_template('index.html', firebase_web_api_key=os.getenv('FIREBASE_WEB_API_KEY'))

# --- Rute Autentikasi ---
@app.route('/api/register', methods=['POST'])
def register():
    """Endpoint ini hanya untuk digunakan oleh Telegram Bot."""
    secret_key = request.headers.get('X-Bot-Secret-Key')
    if secret_key != os.getenv('BOT_SECRET_KEY'):
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    data = request.json
    email = data.get('email')
    
    if not email:
        return jsonify({"success": False, "error": "Email is required"}), 400

    # Generate username dan password acak
    username = 'user_' + ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))
    password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))

    result = create_user(email, password, username)
    
    if result['success']:
        return jsonify({
            "success": True,
            "username": username,
            "password": password
        })
    else:
        return jsonify(result), 400

@app.route('/api/user/profile', methods=['GET'])
def get_profile():
    """Mendapatkan profil user yang sedang login."""
    id_token = request.headers.get('Authorization').split('Bearer ')[-1]
    token_result = verify_token(id_token)
    
    if not token_result['success']:
        return jsonify(token_result), 401
        
    uid = token_result['uid']
    profile = get_user_profile(uid)
    
    if profile['success']:
        return jsonify(profile)
    else:
        return jsonify(profile), 404

@app.route('/api/user/profile', methods=['PUT'])
def update_profile():
    """Memperbarui profil user."""
    id_token = request.headers.get('Authorization').split('Bearer ')[-1]
    token_result = verify_token(id_token)
    
    if not token_result['success']:
        return jsonify(token_result), 401
        
    uid = token_result['uid']
    data = request.json
    update_result = update_user_profile(uid, data)
    
    if update_result['success']:
        return jsonify(update_result)
    else:
        return jsonify(update_result), 400

# --- Rute Deployment ---
@app.route('/api/deploy/vercel', methods=['POST'])
def deploy_to_vercel():
    """Endpoint untuk deploy ke Vercel."""
    id_token = request.headers.get('Authorization').split('Bearer ')[-1]
    token_result = verify_token(id_token)
    
    if not token_result['success']:
        return jsonify(token_result), 401
        
    uid = token_result['uid']
    
    project_name = request.form.get('domain')
    file = request.files.get('file')
    
    if not project_name or not file:
        return jsonify({"success": False, "error": "Project name and file are required"}), 400

    # Baca konten file
    try:
        file_content = file.read().decode('utf-8')
        files = [{"file": file.filename, "data": file_content}]
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to read file: {str(e)}"}), 400

    # Proses deployment
    deploy_result = create_deployment(project_name, files)
    
    if deploy_result['success']:
        # Simpan info proyek ke database
        store_vercel_project(
            uid, 
            deploy_result.get('id', project_name), # Gunakan ID dari Vercel jika ada
            project_name, 
            deploy_result['url']
        )
        return jsonify(deploy_result)
    else:
        return jsonify(deploy_result), 500

@app.route('/api/deploy/gocloud', methods=['POST'])
def deploy_to_gocloud():
    """Endpoint untuk deploy ke GoCloud (logika asli dari JS)."""
    # Anda bisa menambahkan verifikasi token di sini juga jika diperlukan
    # Untuk sekarang, kita biarkan seperti aslinya (tanpa autentikasi user)
    
    project_name = request.form.get('subdomain')
    file = request.files.get('file')
    
    if not project_name or not file:
        return jsonify({"success": False, "error": "Project name and file are required"}), 400

    # Kirim request ke API GoCloud
    gocloud_url = 'https://www.gocloud.web.id/deploy'
    files = {'file': (file.filename, file.stream, file.content_type)}
    data = {'subdomain': project_name}
    
    response = requests.post(gocloud_url, files=files, data=data)
    
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({"success": False, "error": "Failed to deploy to GoCloud"}), 500

# --- Rute Manajemen Proyek Vercel ---
@app.route('/api/vercel/projects', methods=['GET'])
def list_vercel_projects():
    """Mendapatkan daftar proyek Vercel milik user."""
    id_token = request.headers.get('Authorization').split('Bearer ')[-1]
    token_result = verify_token(id_token)
    
    if not token_result['success']:
        return jsonify(token_result), 401
        
    uid = token_result['uid']
    projects = get_vercel_projects(uid)
    
    if projects['success']:
        return jsonify(projects)
    else:
        return jsonify(projects), 404

@app.route('/api/vercel/projects/<project_id>', methods=['DELETE'])
def delete_vercel_project_route(project_id):
    """Menghapus referensi proyek Vercel dari database user."""
    id_token = request.headers.get('Authorization').split('Bearer ')[-1]
    token_result = verify_token(id_token)
    
    if not token_result['success']:
        return jsonify(token_result), 401
        
    uid = token_result['uid']
    
    # Hapus dari database kita
    db_result = delete_vercel_project(uid, project_id)
    
    if db_result['success']:
        # Opsional: Anda bisa juga memanggil API Vercel untuk menghapus deployment di sini
        # delete_result = delete_project(project_id) # Fungsi ini belum sempurna
        return jsonify(db_result)
    else:
        return jsonify(db_result), 404

if __name__ == '__main__':
    app.run(debug=True)