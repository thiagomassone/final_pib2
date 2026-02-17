from __future__ import annotations

import streamlit as st
from security.auth import authenticate_user


def render_login() -> None:
    st.title("🔐 Login")

    # Si ya está logueado, redirecciona al home
    if st.session_state.get("user"):
        st.session_state["page"] = "home"
        st.stop()

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Usuario", key="login_username")
        password = st.text_input("Contraseña", type="password", key="login_password")
        submitted = st.form_submit_button("Ingresar")

    if submitted:
        user = authenticate_user(username=username, password=password)

        if not user:
            st.error("Usuario o contraseña incorrectos.")
            return

        # guardar sesión
        st.session_state["user"] = user

        # navegar al home
        st.session_state["page"] = "home"

        st.stop()
