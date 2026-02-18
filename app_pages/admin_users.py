from __future__ import annotations

from datetime import date

import streamlit as st

from database.db import list_users
from security.auth import register_user, set_user_password


def render_admin_users() -> None:
    st.title("🛠️ Administración de usuarios")

    # ---- login ----
    user = st.session_state.get("user")
    if not user:
        st.session_state["page"] = "login"
        st.rerun()

    # ---- admin ----
    if (user.get("role") or "").lower() != "admin":
        st.session_state["page"] = "home"
        st.rerun()

    # ---- Botón volver ----
    if st.button("⬅️ Home", key="admin_back_home"):
        st.session_state["page"] = "home"
        st.rerun()

    st.divider()

    # -------------------------
    # Crear usuario
    # -------------------------
    st.subheader("Crear nuevo usuario")

    with st.form("create_user_form", clear_on_submit=True):
        username = st.text_input("Username", key="au_username")
        password = st.text_input("Password", type="password", key="au_password")
        role_new = st.selectbox("Rol", ["doctor", "admin"], index=0)

        st.caption("Datos personales")
        first_name = st.text_input("Nombre", key="au_first_name")
        last_name = st.text_input("Apellido", key="au_last_name")
        date_of_birth = st.date_input(
            "Fecha de nacimiento",
            min_value=date(1900, 1, 1),
            max_value=date.today(),
            key="au_dob",
        )

        dni = st.text_input("DNI (opcional)", key="au_dni")
        sex = st.selectbox("Sexo (opcional)", ["", "M", "F", "X"], index=0)
        nationality = st.text_input("Nacionalidad (opcional)", key="au_nat")

        submitted = st.form_submit_button("Crear usuario")

    if submitted:
        if not username.strip() or not password:
            st.error("Username y password son obligatorios.")
        elif not first_name.strip() or not last_name.strip():
            st.error("Nombre y apellido son obligatorios.")
        elif date_of_birth is None:
            st.error("Fecha de nacimiento es obligatoria.")
        else:
            try:
                register_user(
                    username=username.strip(),
                    password=password,
                    first_name=first_name.strip(),
                    last_name=last_name.strip(),
                    date_of_birth=date_of_birth.isoformat(),
                    role=role_new,
                    dni=dni.strip() if dni.strip() else None,
                    sex=sex if sex else None,
                    nationality=nationality.strip() if nationality.strip() else None,
                )

                st.session_state["au_user_created_ok"] = True
                st.rerun()

            except Exception as e:
                msg = str(e)

                if "UNIQUE constraint failed" in msg and "users.username" in msg:
                    st.error("Ese username ya existe. Elija otro.")
                elif "UNIQUE constraint failed" in msg and "persons.dni" in msg:
                    st.error("Ese DNI ya existe en el sistema. Revise los datos.")
                else:
                    st.error(f"No se pudo crear el usuario: {e}")
    
    # Mostrar mensaje de éxito debajo del formulario
    if st.session_state.pop("au_user_created_ok", False):
        st.success("✅ Usuario creado correctamente.")

    st.divider()

    # -------------------------
    # Cambiar contraseña
    # -------------------------
    st.subheader("Cambiar contraseña")

    users_for_pw = list_users(limit=500)
    if not users_for_pw:
        st.info("No hay usuarios para actualizar.")
    else:
        options = {
            f"{u['username']} (id={u['id']}, {u.get('first_name','')} {u.get('last_name','')})": u["id"]
            for u in users_for_pw
        }

        with st.form("change_password_form", clear_on_submit=True):
            selected_label = st.selectbox("Usuario", list(options.keys()))
            new_pw = st.text_input("Nueva contraseña", type="password")
            new_pw2 = st.text_input("Repetir nueva contraseña", type="password")
            submitted_pw = st.form_submit_button("Actualizar contraseña")

        if submitted_pw:
            if not new_pw or len(new_pw) < 4:
                st.error("La contraseña debe tener al menos 4 caracteres.")
            elif new_pw != new_pw2:
                st.error("Las contraseñas no coinciden.")
            else:
                try:
                    target_user_id = int(options[selected_label])
                    set_user_password(user_id=target_user_id, new_password=new_pw)
                    st.success("✅ Contraseña actualizada correctamente.")
                except Exception as e:
                    st.error(f"No se pudo actualizar la contraseña: {e}")

    st.divider()

    # -------------------------
    # Listado de usuarios
    # -------------------------
    st.subheader("Usuarios existentes")
    users = list_users(limit=200)

    if not users:
        st.info("No hay usuarios cargados.")
        return

    st.dataframe(users, use_container_width=True)
