import firebase_admin
from firebase_admin import credentials, auth, firestore
import os
from dotenv import load_dotenv

load_dotenv()

# Inisialisasi Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.Certificate(os.path.join(os.path.dirname(__file__), 'serviceAccountKey.json'))
    firebase_admin.initialize_app(cred, {
        'projectId': os.getenv('FIREBASE_PROJECT_ID'),
    })

db = firestore.client()

def create_user(email, password, username):
    """Membuat pengguna baru di Firebase Authentication dan Firestore."""
    try:
        # Buat user di Authentication
        user = auth.create_user(
            email=email,
            password=password
        )
        
        # Simpan data tambahan di Firestore
        db.collection('users').document(user.uid).set({
            'username': username,
            'email': email,
            'createdAt': firestore.SERVER_TIMESTAMP
        })
        
        return {"success": True, "uid": user.uid}
    except auth.EmailAlreadyExistsError:
        return {"success": False, "error": "Email already exists"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def authenticate_user(email_or_username, password):
    """Mengautentikasi pengguna dengan email atau username."""
    try:
        # Coba login dengan email
        user = auth.get_user_by_email(email_or_username)
    except auth.UserNotFoundError:
        # Jika gagal, cari user berdasarkan username di Firestore
        users_ref = db.collection('users').where('username', '==', email_or_username).limit(1).get()
        if not users_ref:
            return {"success": False, "error": "Invalid credentials"}
        user_doc = users_ref[0]
        user = auth.get_user(user_doc.id)
        email_or_username = user.email # Gunakan email untuk login selanjutnya

    # Verifikasi password (perlu library tambahan atau cara khusus, 
    # namun Firebase Admin SDK tidak memiliki fungsi verifikasi password langsung.
    # Solusinya adalah dengan menggunakan Firebase REST API untuk login.
    # Untuk kesederhanaan, kita asumsikan login berhasil jika user ditemukan.
    # Implementasi yang lebih robust akan memanggil endpoint `verifyPassword` dari Firebase REST API.
    # Tapi untuk kasus ini, kita akan membuat token kustom setelah verifikasi manual.
    
    # Karena kita tidak bisa verifikasi password langsung di server, kita akan menggunakan strategi lain.
    # Kita akan meminta client untuk login dan kita hanya memvalidasi token JWT yang diberikan client.
    # Fungsi ini akan diubah fungsinya untuk mendapatkan data user saja.
    
    # --- PERUBAHAN STRATEGI ---
    # Fungsi ini akan digunakan oleh bot untuk membuat user.
    # Login akan ditangani oleh client menggunakan Firebase Web SDK dan token JWT-nya akan diverifikasi di server.
    # Mari kita buat fungsi untuk verifikasi token.
    return {"success": False, "error": "This function is deprecated. Use verify_token instead."}


def verify_token(id_token):
    """Memverifikasi token JWT dari client."""
    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        return {"success": True, "uid": uid}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_user_profile(uid):
    """Mendapatkan profil pengguna dari Firestore."""
    try:
        user_doc = db.collection('users').document(uid).get()
        if user_doc.exists:
            return {"success": True, "data": user_doc.to_dict()}
        return {"success": False, "error": "User not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_user_profile(uid, data):
    """Memperbarui profil pengguna."""
    try:
        db.collection('users').document(uid).update(data)
        # Jika username diubah, update juga di Authentication (ini tidak bisa langsung)
        # Update email/password harus melalui client SDK atau proses yang lebih kompleks.
        # Untuk sekarang, kita hanya update di Firestore.
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

def store_vercel_project(uid, project_id, project_name, project_url):
    """Menyimpan proyek Vercel yang dimiliki oleh user."""
    try:
        db.collection('users').document(uid).collection('vercel_projects').document(project_id).set({
            'name': project_name,
            'url': project_url,
            'createdAt': firestore.SERVER_TIMESTAMP
        })
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_vercel_projects(uid):
    """Mendapatkan semua proyek Vercel milik user."""
    try:
        projects_ref = db.collection('users').document(uid).collection('vercel_projects').order_by('createdAt', direction=firestore.Query.DESCENDING).stream()
        projects = [doc.to_dict() | {'id': doc.id} for doc in projects_ref]
        return {"success": True, "data": projects}
    except Exception as e:
        return {"success": False, "error": str(e)}

def delete_vercel_project(uid, project_id):
    """Menghapus proyek Vercel dari database."""
    try:
        db.collection('users').document(uid).collection('vercel_projects').document(project_id).delete()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}