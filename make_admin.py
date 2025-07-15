import os
from app import app
from extensions import db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    # Try to find an existing user to make admin
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        # If 'admin' user doesn't exist, try to find any user
        admin_user = User.query.first()
        if admin_user:
            print(f"Pengguna 'admin' tidak ditemukan. Menggunakan pengguna pertama yang ditemukan: {admin_user.username}")
        else:
            # If no users exist, create a new admin user
            print("Tidak ada pengguna yang ditemukan. Membuat pengguna admin baru.")
            # IMPORTANT: This is a temporary password. User should change it immediately.
            temp_password = os.environ.get("TEMP_ADMIN_PASSWORD", "admin_password_123")
            admin_user = User(
                full_name='Admin User',
                username='admin',
                email='admin@example.com',
                whatsapp_number='1234567890',
                password=generate_password_hash(temp_password),
                role='admin'
            )
            db.session.add(admin_user)
            db.session.commit()
            print(f"Pengguna admin baru 'admin' dengan password sementara '{temp_password}' telah dibuat.")
            print("HARAP UBAH PASSWORD INI SEGERA SETELAH LOGIN PERTAMA.")
            
    if admin_user and admin_user.role != 'admin':
        admin_user.role = 'admin'
        db.session.commit()
        print(f"Pengguna {admin_user.username} sekarang adalah {admin_user.role}.")
    elif admin_user and admin_user.role == 'admin':
        print(f"Pengguna {admin_user.username} sudah menjadi admin.")
    else:
        print("Gagal membuat atau menemukan pengguna untuk dijadikan admin.")
