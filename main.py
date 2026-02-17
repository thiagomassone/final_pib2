from __future__ import annotations
import streamlit as st

from database.db import init_db
from app_pages.login import render_login
from app_pages.home import render_home
from app_pages.admin_users import render_admin_users
from app_pages.patients import render_patients
from app_pages.diagnosis import render_diagnosis
from app_pages.history import render_history



def _init_state() -> None:
    if "page" not in st.session_state:
        st.session_state["page"] = "login"


def _require_login() -> dict | None:
    user = st.session_state.get("user")
    if not user:
        st.session_state["page"] = "login"
        st.rerun()
    return user


def main() -> None:
    st.set_page_config(page_title="TP PIB - App Clínica", page_icon="🏥", layout="wide")

    init_db()
    _init_state()

    page = st.session_state["page"]

    if page == "login":
        render_login()
        return

    user = _require_login()

    if page == "home":
        render_home()
        return

    if page == "admin_users":
        if (user.get("role") or "").lower() != "admin":
            st.session_state["page"] = "home"
            st.rerun()
        render_admin_users()
        return

    if page == "patients":
        render_patients()
        return

    if page == "diagnosis":
        render_diagnosis()
        return

    if page == "history":
        render_history()
        return

    st.session_state["page"] = "home"
    st.rerun()




if __name__ == "__main__":
    main()
