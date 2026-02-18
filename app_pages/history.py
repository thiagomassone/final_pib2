from __future__ import annotations

import datetime as dt
from pathlib import Path

import streamlit as st
from PIL import Image

from app_pages.patients import render_patient_search, format_date_ddmmyyyy
from database.db import list_studies_by_patient
from compression.huffman_codec import decompress_huf_file_to_image


def _fmt_datetime_sqlite(dt_str: str | None) -> str:
    if not dt_str:
        return "-"
    try:
        d = dt.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        return d.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return dt_str


def _render_study_image(img_path: str) -> None:
    """
    Renderiza la imagen del estudio.
    - Si es .huf: descomprime (Huffman) y muestra en escala de grises.
    - Si es JPG/PNG: abre con libreria PIL
    """
    p = Path(img_path) if img_path else None

    if not img_path or not p or not p.exists():
        st.warning("Imagen no disponible (path inexistente o vacío).")
        st.caption(f"Path: {img_path}")
        return

    try:
        if p.suffix.lower() == ".huf":
            img = decompress_huf_file_to_image(p)
            st.image(
                img,
                use_container_width=True,
                clamp=True,
                channels="GRAY",
            )
            st.caption(f"Imagen comprimida (Huffman .huf): {img_path}")
        else:
            img_pil = Image.open(p)
            st.image(img_pil, use_container_width=True)
            st.caption(f"Imagen: {img_path}")

    except Exception as e:
        st.warning(f"No se pudo abrir la imagen: {e}")
        st.caption(f"Path: {img_path}")


def render_history() -> None:
    st.title("📚 Historia clínica")

    user = st.session_state.get("user")
    if not user:
        st.session_state["page"] = "login"
        st.rerun()

    top = st.columns([1, 1, 6])
    with top[0]:
        if st.button("⬅️ Home", key="hist_back_home"):
            st.session_state["page"] = "home"
            st.rerun()

    with top[1]:
        if st.button("🩻 Volver a Diagnóstico", key="hist_back_diag"):
            st.session_state["page"] = "diagnosis"
            st.rerun()

    st.divider()

    selected = st.session_state.get("selected_patient")
    if not selected:
        st.info("Seleccione un paciente para ver su historia clínica.")
        render_patient_search(prefix="hist")
        st.stop()

    st.success(
        f"Paciente: **{selected.get('last_name','')} {selected.get('first_name','')}** "
        f"(DNI: {selected.get('dni') or '-'}) · "
        f"Nac: **{format_date_ddmmyyyy(selected.get('date_of_birth'))}**"
    )

    patient_id = int(selected["patient_id"])
    studies = list_studies_by_patient(patient_id=patient_id, limit=300)

    st.divider()

    if not studies:
        st.info("Este paciente todavía no tiene estudios guardados.")
        return

    st.caption(f"Estudios encontrados: **{len(studies)}**")

    for s in studies:
        study_id = s.get("study_id") or s.get("id")
        created_at = _fmt_datetime_sqlite(s.get("created_at"))
        label = s.get("model_label") or "-"
        score = s.get("model_score")
        score_txt = "-" if score is None else f"{float(score):.2f}"
        img_path = s.get("image_path") or ""
        report = s.get("report_text") or ""

        header = f"🗓️ {created_at} — Estudio #{study_id} — Resultado: {label} (score {score_txt})"

        with st.expander(header, expanded=False):
            c_img, c_info = st.columns([3, 2], gap="large")

            with c_img:
                _render_study_image(img_path)

            with c_info:
                st.markdown(f"**Fecha/hora:** {created_at}")
                st.markdown(f"**Model label:** {label}")
                st.markdown(f"**Model score:** {score_txt}")

                if report.strip():
                    st.markdown("**Informe:**")
                    st.write(report)
                else:
                    st.info("Sin informe guardado.")

    st.divider()
    if st.button("🧹 Limpiar selección de paciente", key="hist_clear_selected_patient"):
        st.session_state.pop("selected_patient", None)
        st.rerun()
