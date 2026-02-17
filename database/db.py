from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).parent / "app.db"


def get_connection() -> sqlite3.Connection:
    """
    Crea una conexión SQLite.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def _add_column_if_missing(cur: sqlite3.Cursor, table: str, column_def: str) -> None:
    """
    Agrega una columna si no existe.
    """
    col_name = column_def.split()[0]
    cur.execute(f"PRAGMA table_info({table});")
    cols = [r[1] for r in cur.fetchall()]  # r[1] = column name
    if col_name not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column_def};")


def init_db() -> None:
    conn = get_connection()
    cur = conn.cursor()

    # Persons
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS persons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dni TEXT UNIQUE,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            sex TEXT,
            date_of_birth TEXT NOT NULL,
            nationality TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )

    # Users
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL UNIQUE,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'doctor',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE
        );
        """
    )

    # Patients
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL UNIQUE,
            insurance_name TEXT,
            insurance_number TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE
        );
        """
    )

    # Studies (esquema "nuevo")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS studies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            image_path TEXT NOT NULL,
            model_label TEXT,
            model_score REAL,
            report_text TEXT,
            created_by_user_id INTEGER NOT NULL,
            updated_by_user_id INTEGER,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
            FOREIGN KEY (created_by_user_id) REFERENCES users(id),
            FOREIGN KEY (updated_by_user_id) REFERENCES users(id)
        );
        """
    )

    # Indexes
    cur.execute("CREATE INDEX IF NOT EXISTS idx_persons_dni ON persons(dni);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_persons_last_name ON persons(last_name);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_studies_patient_id ON studies(patient_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_studies_patient_created ON studies(patient_id, created_at);")

    _add_column_if_missing(cur, "studies", "created_by_user_id INTEGER")
    _add_column_if_missing(cur, "studies", "updated_by_user_id INTEGER")
    _add_column_if_missing(cur, "studies", "updated_at TEXT")

    cur.execute("SELECT id FROM users WHERE role = 'admin' ORDER BY id ASC LIMIT 1;")
    row = cur.fetchone()
    if row:
        fallback_user_id = int(row["id"])
    else:
        cur.execute("SELECT id FROM users ORDER BY id ASC LIMIT 1;")
        row2 = cur.fetchone()
        fallback_user_id = int(row2["id"]) if row2 else None

    if fallback_user_id is not None:
        cur.execute(
            """
            UPDATE studies
            SET created_by_user_id = ?
            WHERE created_by_user_id IS NULL;
            """,
            (fallback_user_id,),
        )

    conn.commit()
    conn.close()


# ======================================================
# Personas
# ======================================================

def create_person(
    dni: Optional[str],
    first_name: str,
    last_name: str,
    date_of_birth: str,
    sex: Optional[str] = None,
    nationality: Optional[str] = None,
) -> int:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO persons (dni, first_name, last_name, sex, date_of_birth, nationality)
        VALUES (?, ?, ?, ?, ?, ?);
        """,
        (
            dni.strip() if dni else None,
            first_name.strip(),
            last_name.strip(),
            sex.strip() if sex else None,
            date_of_birth,
            nationality.strip() if nationality else None,
        ),
    )

    conn.commit()
    person_id = cur.lastrowid
    conn.close()
    return int(person_id)


def get_person_by_id(person_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM persons WHERE id = ?;", (int(person_id),))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


# ======================================================
# Usuarios
# ======================================================

def create_user(person_id: int, username: str, password_hash: str, role: str = "doctor") -> int:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO users (person_id, username, password_hash, role)
        VALUES (?, ?, ?, ?);
        """,
        (int(person_id), username.strip(), password_hash, role.strip()),
    )

    conn.commit()
    user_id = cur.lastrowid
    conn.close()
    return int(user_id)


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT u.*, p.first_name, p.last_name
        FROM users u
        JOIN persons p ON p.id = u.person_id
        WHERE u.username = ?;
        """,
        (username.strip(),),
    )

    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def list_users(limit: int = 100) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT u.id, u.username, u.role, u.created_at, p.first_name, p.last_name
        FROM users u
        JOIN persons p ON p.id = u.person_id
        ORDER BY datetime(u.created_at) DESC
        LIMIT ?;
        """,
        (int(limit),),
    )

    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_user_password_hash(user_id: int, password_hash: str) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE users
        SET password_hash = ?
        WHERE id = ?;
        """,
        (password_hash, int(user_id)),
    )
    conn.commit()
    conn.close()

# ======================================================
# Pacientes
# ======================================================

def create_patient(person_id: int, insurance_name: Optional[str] = None, insurance_number: Optional[str] = None) -> int:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO patients (person_id, insurance_name, insurance_number)
        VALUES (?, ?, ?);
        """,
        (int(person_id), insurance_name, insurance_number),
    )

    conn.commit()
    patient_id = cur.lastrowid
    conn.close()
    return int(patient_id)


def search_patients(query: str, limit: int = 50) -> List[Dict[str, Any]]:
    q = f"%{query.strip()}%"
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            pa.id AS patient_id,
            p.id AS person_id,
            p.dni,
            p.first_name,
            p.last_name,
            p.date_of_birth,
            p.sex,
            p.nationality,
            pa.insurance_name,
            pa.insurance_number
        FROM patients pa
        JOIN persons p ON p.id = pa.person_id
        WHERE p.dni LIKE ?
           OR p.last_name LIKE ?
           OR p.first_name LIKE ?
        ORDER BY p.last_name, p.first_name
        LIMIT ?;
        """,
        (q, q, q, int(limit)),
    )

    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ======================================================
#  Estudios de Diagnostico
# ======================================================

def create_study(patient_id: int, image_path: str, created_by_user_id: int) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO studies (patient_id, image_path, created_by_user_id)
        VALUES (?, ?, ?);
        """,
        (int(patient_id), str(image_path), int(created_by_user_id)),
    )
    conn.commit()
    study_id = cur.lastrowid
    conn.close()
    return int(study_id)


def update_study_ml_result(
    study_id: int,
    model_label: str,
    model_score: Optional[float] = None,
    updated_by_user_id: Optional[int] = None,
) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE studies
        SET model_label = ?,
            model_score = ?,
            updated_at = datetime('now'),
            updated_by_user_id = COALESCE(?, updated_by_user_id)
        WHERE id = ?;
        """,
        (
            model_label,
            float(model_score) if model_score is not None else None,
            int(updated_by_user_id) if updated_by_user_id is not None else None,
            int(study_id),
        ),
    )
    conn.commit()
    conn.close()


def update_study_report(
    study_id: int,
    report_text: str,
    updated_by_user_id: Optional[int] = None,
) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE studies
        SET report_text = ?,
            updated_at = datetime('now'),
            updated_by_user_id = COALESCE(?, updated_by_user_id)
        WHERE id = ?;
        """,
        (
            report_text,
            int(updated_by_user_id) if updated_by_user_id is not None else None,
            int(study_id),
        ),
    )
    conn.commit()
    conn.close()

def update_study_image_path(
    study_id: int,
    image_path: str,
    updated_by_user_id: Optional[int] = None,
) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE studies
        SET image_path = ?,
            updated_at = datetime('now'),
            updated_by_user_id = COALESCE(?, updated_by_user_id)
        WHERE id = ?;
        """,
        (
            str(image_path),
            int(updated_by_user_id) if updated_by_user_id is not None else None,
            int(study_id),
        ),
    )
    conn.commit()
    conn.close()


def list_studies_by_patient(patient_id: int, limit: int = 200) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            s.id AS study_id,
            s.patient_id,
            s.image_path,
            s.model_label,
            s.model_score,
            s.report_text,
            s.created_at,
            s.updated_at
        FROM studies s
        WHERE s.patient_id = ?
        ORDER BY datetime(s.created_at) DESC, s.id DESC
        LIMIT ?;
        """,
        (int(patient_id), int(limit)),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_study_by_id(study_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            s.*,
            p.first_name,
            p.last_name,
            p.dni
        FROM studies s
        JOIN patients pa ON pa.id = s.patient_id
        JOIN persons p ON p.id = pa.person_id
        WHERE s.id = ?;
        """,
        (int(study_id),),
    )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None
