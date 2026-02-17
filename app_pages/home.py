from __future__ import annotations

import streamlit as st


def render_home() -> None:
    user = st.session_state.get("user")
    if not user:
        st.session_state["page"] = "login"
        st.rerun()

    role = (user.get("role") or "").lower()
    full_name = f"{user.get('first_name','')} {user.get('last_name','')}".strip()

    top_l, top_r = st.columns([8, 2])
    with top_l:
        st.title("🏥 TP Final PIB – RIS FET")
        st.caption(f"Sesión iniciada como **{user.get('username')}** · Rol: **{role}** · {full_name}")

    with top_r:
        st.write("")
        st.write("")
        if st.button("🚪 Cerrar sesión", key="logout_top", use_container_width=True):
            st.session_state.pop("user", None)
            st.session_state["page"] = "login"
            st.rerun()

    st.divider()
    st.subheader("Aplicaciones disponibles")

    cols = st.columns(3)

    # --- Diagnóstico ---
    with cols[0]:
        with st.container(border=True):
            st.markdown("### 🩻 Diagnóstico por imágenes")
            st.write("Cargar RX de tórax, ejecutar el modelo y generar informe.")
            if st.button("Abrir", use_container_width=True, key="open_diagnosis"):
                st.session_state["page"] = "diagnosis"
                st.rerun()

    # --- Pacientes ---
    with cols[1]:
        with st.container(border=True):
            st.markdown("### 👤 Pacientes")
            st.write("Buscar, crear, ver historia clinica y gestionar pacientes.")
            if st.button("Abrir", use_container_width=True, key="open_patients"):
                st.session_state["page"] = "patients"
                st.rerun()

            if st.button("Ver historia clínica", use_container_width=True, key="open_history"):
                st.session_state["page"] = "history"
                st.rerun()

    # --- Admin Users (solo admin) ---
    with cols[2]:
        with st.container(border=True):
            st.markdown("### 🛠️ Administración de usuarios")
            st.write("Crear y gestionar usuarios del sistema.")
            disabled = role != "admin"
            if st.button("Abrir", use_container_width=True, disabled=disabled, key="open_admin_users"):
                st.session_state["page"] = "admin_users"
                st.rerun()

    st.divider()
