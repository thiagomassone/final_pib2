from security.auth import register_user
from database.db import init_db

def main():
    init_db()

    # Credenciales iniciales para el admin. Si ya existe, no se vuelve a crear.
    username = "admin"
    password = "admin1234"

    try:
        register_user(
            username=username,
            password=password,
            first_name="Admin",
            last_name="System",
            date_of_birth="1990-01-01",
            role="admin",
        )
        print("✅ Admin creado: admin / admin1234")
    except ValueError as e:
        print(f"ℹ️ No se creó admin (probablemente ya existe): {e}")

if __name__ == "__main__":
    main()
