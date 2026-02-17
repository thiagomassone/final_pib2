from __future__ import annotations

import streamlit as st
import datetime as dt
from database.db import create_person, create_patient, search_patients

def format_date_ddmmyyyy(date_str: str | None) -> str:
    if not date_str:
        return "-"
    try:
        d = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
        return d.strftime("%d/%m/%Y")
    except Exception:
        return date_str

def render_patient_search(prefix: str = "patients") -> None:

    st.subheader("Buscar paciente")
    q = st.text_input(
        "Buscar por DNI / apellido / nombre",
        key=f"{prefix}_search_q",
    )

    if not q.strip():
        return

    results = search_patients(q.strip(), limit=50)
    st.caption(f"Resultados: {len(results)}")

    if not results:
        st.info("No se encontraron pacientes.")
        return

    for r in results:
        sex = r.get("sex") or "-"
        nat = r.get("nationality") or "-"
        ins = r.get("insurance_name") or "-"
        insn = r.get("insurance_number") or "-"

        label = (
            f"**{r.get('last_name','')} {r.get('first_name','')}** · "
            f"DNI: **{r.get('dni') or '-'}** · "
            f"Nac: **{format_date_ddmmyyyy(r.get('date_of_birth'))}** · "
            f"Sexo: **{sex}** · "
            f"Nacionalidad: **{nat}** · "
            f"Obra Social: **{ins}** · "
            f"N° Afiliado: **{insn}**"
        )

        cols = st.columns([6, 2])
        cols[0].markdown(label)

        if cols[1].button("Seleccionar", key=f"{prefix}_sel_{r['patient_id']}"):
            st.session_state["selected_patient"] = r
            st.success("Paciente seleccionado.")
            st.rerun()

def render_patients() -> None:
    st.title("👤 Pacientes")

    user = st.session_state.get("user")
    if not user:
        st.session_state["page"] = "login"
        st.rerun()

    top = st.columns([1, 8])
    with top[0]:
        if st.button("⬅️ Home", key="patients_back_home"):
            st.session_state["page"] = "home"
            st.rerun()

    st.divider()

    # =========================
    # Buscar pacientes
    # =========================
    render_patient_search(prefix="patients")
    st.divider()

    # =========================
    # Paciente seleccionado
    # =========================
    selected = st.session_state.get("selected_patient")
    if selected:
        st.subheader("Paciente seleccionado")

        cA, cB, cC = st.columns(3)

        with cA:
            st.markdown(f"**Apellido:** {selected.get('last_name','-')}")
            st.markdown(f"**Nombre:** {selected.get('first_name','-')}")
            st.markdown(f"**DNI:** {selected.get('dni') or '-'}")

        with cB:
            st.markdown(f"**Fecha de Nacimiento:** {format_date_ddmmyyyy(selected.get('date_of_birth'))}")
            st.markdown(f"**Sexo:** {selected.get('sex') or '-'}")
            st.markdown(f"**Nacionalidad:** {selected.get('nationality') or '-'}")

        with cC:
            st.markdown(f"**Obra social:** {selected.get('insurance_name') or '-'}")
            st.markdown(f"**N° afiliado:** {selected.get('insurance_number') or '-'}")

        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("🩻 Ir a Diagnóstico (subir estudio)", key="go_diag_from_patient"):
                st.session_state["page"] = "diagnosis"
                st.rerun()
        with c2:
            if st.button("🧹 Limpiar selección", key="clear_selected_patient"):
                st.session_state.pop("selected_patient", None)
                st.rerun()

        st.divider()

    # =========================
    # Crear paciente
    # =========================
    st.subheader("Crear nuevo paciente")

    with st.form("create_patient_form", clear_on_submit=True):
        dni = st.text_input("DNI (opcional)", key="cp_dni")
        first_name = st.text_input("Nombre", key="cp_first_name")
        last_name = st.text_input("Apellido", key="cp_last_name")
        date_of_birth = st.date_input(
            "Fecha de nacimiento",
            min_value=dt.date(1900, 1, 1),
            max_value=dt.date.today(),
            key="cp_dob"
        )
        sex = st.selectbox("Sexo (opcional)", ["", "M", "F", "X"], index=0, key="cp_sex")
        nationality = st.text_input("Nacionalidad (opcional)", key="cp_nat")

        st.caption("Datos de cobertura (opcional)")
        insurance_name = st.text_input("Obra social", key="cp_ins_name")
        insurance_number = st.text_input("N° afiliado", key="cp_ins_num")

        submitted = st.form_submit_button("Crear paciente")

    if submitted:
        if not first_name.strip() or not last_name.strip():
            st.error("Nombre y apellido son obligatorios.")
            return
        if date_of_birth is None:
            st.error("Fecha de nacimiento es obligatoria.")
            return

        try:
            person_id = create_person(
                dni=dni.strip() if dni.strip() else None,
                first_name=first_name.strip(),
                last_name=last_name.strip(),
                date_of_birth=date_of_birth.isoformat(),
                sex=sex if sex else None,
                nationality=nationality.strip() if nationality.strip() else None,
            )

            patient_id = create_patient(
                person_id=person_id,
                insurance_name=insurance_name.strip() if insurance_name.strip() else None,
                insurance_number=insurance_number.strip() if insurance_number.strip() else None,
            )

            st.success(f"✅ Paciente creado (patient_id={patient_id}).")
        except Exception as e:
            st.error(f"No se pudo crear el paciente: {e}")

