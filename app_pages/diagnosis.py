from __future__ import annotations

import hashlib
import tempfile
import uuid
from pathlib import Path

import cv2
import numpy as np
import streamlit as st
from PIL import Image

from app_pages.patients import render_patient_search
from database.db import (
    create_study,
    update_study_image_path,
    update_study_ml_result,
    update_study_report,
)
from ml_model.rf_inference import load_rf_model, predict_from_image_path_with_model

from compression.huffman_codec import compress_image_to_huf_file

from image_processing.preprocess import preprocess_rx
from image_processing.segmentation import segment_lungs

MODEL_PATH = Path("ml_model/modelo_random_forest_final.pkl")
OUTPUT_DIR = Path("outputs/images")


@st.cache_resource
def _get_rf_model():
    return load_rf_model(MODEL_PATH)


def _render_preview(pil_img: Image.Image, *, title: str = " ") -> None:
    if title.strip():
        st.caption(title)

    st.image(
        pil_img,
        use_container_width=True,
        clamp=False,
        output_format="PNG",
        channels="RGB",
    )

    st.markdown(
        """
        <style>
        img {
            max-height: 60vh;
            object-fit: contain;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_diagnosis() -> None:
    st.title("🩻 Diagnóstico por imágenes")

    user = st.session_state.get("user")
    if not user:
        st.session_state["page"] = "login"
        st.rerun()

    # Verificar que el modelo exista
    if not MODEL_PATH.exists():
        st.error(f"No se encuentra el modelo en: {MODEL_PATH}")
        st.stop()

    col1, col2, spacer = st.columns([1, 1, 8])

    with col1:
        if st.button("⬅️ Home", key="diag_back_home"):
            # Reset del flujo de Diagnóstico
            st.session_state.pop("current_study_id", None)
            st.session_state.pop("current_image_path", None)
            st.session_state.pop("last_rf_result", None)
            st.session_state.pop("proc_preview", None)
            st.session_state.pop("proc_preview_hash", None)
            st.session_state.pop("diag_report_text", None)
            st.session_state.pop("diag_patient_id", None)

            k = st.session_state.get("diag_uploader_key", "diag_uploader_0")
            try:
                n = int(str(k).split("_")[-1])
            except Exception:
                n = 0
            st.session_state["diag_uploader_key"] = f"diag_uploader_{n+1}"

            st.session_state.pop("selected_patient", None)

            st.session_state["page"] = "home"
            st.rerun()


    with col2:
        if st.button("📚 Historia clínica", key="diag_go_history"):
            st.session_state["page"] = "history"
            st.rerun()


    st.divider()

    selected = st.session_state.get("selected_patient")
    if not selected:
        st.info("Seleccioná un paciente para comenzar el diagnóstico.")
        render_patient_search(prefix="diag")
        st.stop()

    patient_id = int(selected["patient_id"])
    st.success(
        f"Paciente: **{selected.get('last_name','')} {selected.get('first_name','')}** "
        f"(DNI: {selected.get('dni') or '-'})"
    )
    prev_pid = st.session_state.get("diag_patient_id")
    if prev_pid is None:
        st.session_state["diag_patient_id"] = patient_id
    elif int(prev_pid) != int(patient_id):
        # limpiar todo lo asociado
        st.session_state.pop("current_study_id", None)
        st.session_state.pop("current_image_path", None)
        st.session_state.pop("last_rf_result", None)
        st.session_state.pop("proc_preview", None)
        st.session_state.pop("proc_preview_hash", None)
        st.session_state.pop("diag_report_text", None)

        k = st.session_state.get("diag_uploader_key", "diag_uploader_0")
        try:
            n = int(k.split("_")[-1])
        except Exception:
            n = 0
        st.session_state["diag_uploader_key"] = f"diag_uploader_{n+1}"


        st.session_state["diag_patient_id"] = patient_id
        
    c1, c2, _sp = st.columns([1, 1, 8])
    with c1:
        if st.button("🔄 Cambiar paciente", key="diag_change_patient"):
            st.session_state.pop("selected_patient", None)
            st.session_state.pop("current_study_id", None)
            st.session_state.pop("current_image_path", None)
            st.session_state.pop("last_rf_result", None)
            st.session_state.pop("proc_preview", None)
            st.session_state.pop("proc_preview_hash", None)
            st.session_state.pop("diag_patient_id", None)
            st.session_state.pop("diag_report_text", None)

            st.rerun()

    with c2:
        if st.button("🧹 Limpiar estudio actual", key="diag_clear_study"):
            st.session_state.pop("current_study_id", None)
            st.session_state.pop("current_image_path", None)
            st.session_state.pop("last_rf_result", None)
            st.session_state.pop("proc_preview", None)
            st.session_state.pop("proc_preview_hash", None)
            k = st.session_state.get("diag_uploader_key", "diag_uploader_0")
            n = int(k.split("_")[-1]) if "_" in k else 0
            st.session_state["diag_uploader_key"] = f"diag_uploader_{n+1}"
            st.rerun()

    st.divider()

    if "diag_uploader_key" not in st.session_state:
        st.session_state["diag_uploader_key"] = "diag_uploader_0"
        
    uploaded = st.file_uploader(
        "Subir radiografía (JPG/PNG)",
        type=["jpg", "jpeg", "png"],
        key=st.session_state["diag_uploader_key"],
    )

    # preview del procesamiento (preprocess + segmentation)

    if uploaded:
        file_bytes = uploaded.getvalue()
        file_hash = hashlib.md5(file_bytes).hexdigest()

        # Recalcular solo si cambió el archivo
        if st.session_state.get("proc_preview_hash") != file_hash:
            with st.spinner("Generando vista del procesamiento..."):
                suffix = Path(uploaded.name).suffix.lower() or ".jpg"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(file_bytes)
                    tmp_path = Path(tmp.name)

                # Cargar imagen a grayscale
                img_np = np.array(Image.open(tmp_path).convert("L"), dtype=np.uint8)

                img_prep = preprocess_rx(img_np)
                mask = segment_lungs(img_prep)
                img_roi = cv2.bitwise_and(img_prep, img_prep, mask=mask)

                st.session_state["proc_preview_hash"] = file_hash
                st.session_state["proc_preview"] = {
                    "img_prep": img_prep,
                    "mask": mask,
                    "img_roi": img_roi,
                }

    study_id = st.session_state.get("current_study_id")

    if not uploaded and not study_id:
        st.info("Suba una imagen para crear un estudio.")
        st.stop()

    col_img, col_actions = st.columns([3, 2], gap="large")

    with col_img:
        if uploaded:
            img = Image.open(uploaded)
            _render_preview(img, title=" ")

    with col_actions:
        st.subheader("Acciones")

        if uploaded and st.button("📌 Crear estudio", use_container_width=True, key="diag_create_study_btn"):
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

            ext = Path(uploaded.name).suffix.lower() or ".jpg"
            filename = f"patient_{patient_id}_{uuid.uuid4().hex}{ext}"
            save_path = OUTPUT_DIR / filename
            save_path.write_bytes(uploaded.getbuffer())

            new_study_id = create_study(
                patient_id=patient_id,
                image_path=str(save_path),
                created_by_user_id=int(user["id"]),
            )

            st.session_state["current_study_id"] = int(new_study_id)
            st.session_state["current_image_path"] = str(save_path)

            st.success(f"✅ Estudio creado (study_id={new_study_id}).")
            st.caption(f"Imagen guardada en: {save_path}")
            st.rerun()

        with st.expander("👁️ Ver imagen procesada", expanded=False):
            r = st.session_state.get("proc_preview")
            if not r:
                st.info("Suba una imagen para ver la vista del algoritmo (prep/mask/ROI).")
            else:
                st.image(
                    r["img_prep"],
                    caption="Preprocesada (CLAHE)",
                    clamp=True,
                    channels="GRAY",
                    use_container_width=True,
                )
                st.image(
                    r["mask"],
                    caption="KMeans",
                    clamp=True,
                    channels="GRAY",
                    use_container_width=True,
                )
                st.image(
                    r["img_roi"],
                    caption="ROI",
                    clamp=True,
                    channels="GRAY",
                    use_container_width=True,
                )

    st.divider()

    study_id = st.session_state.get("current_study_id")
    if not study_id:
        st.info("Cree el estudio para poder correr el modelo y guardar el informe.")
        st.stop()

    st.subheader("Modelo ML")

    if st.button("🤖 Ejecutar modelo (Random Forest)", key="diag_run_rf_model"):
        img_path_s = st.session_state.get("current_image_path")
        if not img_path_s:
            st.error("No hay imagen asociada al estudio actual.")
            st.stop()

        # El modelo trabaja con JPG/PNG; si ya se comprimió a .huf, no corre desde path.
        if str(img_path_s).lower().endswith(".huf"):
            st.error("Este estudio ya fue comprimido (.huf). No se puede correr el modelo desde un .huf.")
            st.stop()

        try:
            clf = _get_rf_model()
            result = predict_from_image_path_with_model(Path(img_path_s), clf)
        except Exception as e:
            st.error(f"Error en inferencia: {e}")
            st.stop()

        update_study_ml_result(
            study_id=int(study_id),
            model_label=result.label,
            model_score=result.score,
            updated_by_user_id=int(user["id"]),
        )

        st.success(f"✅ Resultado: **{result.label}** (score={result.score*100:.2f}%)")

        st.caption("Top-3 probabilidades")
        for name, p in result.top3:
            st.write(f"- {name}: {p*100:.1f}%")

        st.session_state["proc_preview"] = {
            "img_prep": result.img_prep,
            "mask": result.mask,
            "img_roi": result.img_roi,
        }

        st.session_state["last_rf_result"] = {
            "img_prep": result.img_prep,
            "mask": result.mask,
            "img_roi": result.img_roi,
        }

    st.divider()

    st.subheader("Informe médico")
    report = st.text_area("Escribir informe", height=180, key="diag_report_text")

    if st.button("💾 Guardar informe", key="diag_save_report_btn"):
        if not report.strip():
            st.error("El informe está vacío.")
            return

        # 1) Guardar texto del informe
        update_study_report(
            study_id=int(study_id),
            report_text=report.strip(),
            updated_by_user_id=int(user["id"]),
        )

        # 2) Al guardar: comprimir la imagen en Huffman (.huf) y actualizar image_path en DB
        img_path_s = st.session_state.get("current_image_path")

        if not img_path_s:
            st.warning("Informe guardado. No se encontró la imagen en sesión para comprimir.")
            st.success("✅ Informe guardado.")
            return

        img_path = Path(img_path_s)

        if not img_path.exists():
            st.warning("Informe guardado, pero el archivo de imagen no existe en disco.")
            st.caption(f"Path: {img_path}")
            st.success("✅ Informe guardado.")
            return

        # check si ya está comprimida
        if img_path.suffix.lower() == ".huf":
            st.success("✅ Informe guardado (la imagen ya estaba comprimida).")
            return

        try:
            out_huf = img_path.with_suffix(".huf")

            # Leer JPG/PNG y pasarlo a escala de grises
            img_np = np.array(Image.open(img_path).convert("L"), dtype=np.uint8)

            # Guardar .huf
            compress_image_to_huf_file(img_np, out_huf)

            # Actualizar DB para que historia clínica apunte al .huf
            update_study_image_path(
                study_id=int(study_id),
                image_path=str(out_huf),
                updated_by_user_id=int(user["id"]),
            )

            st.session_state["current_image_path"] = str(out_huf)

            st.success("✅ Informe guardado.")
            st.caption(f"Archivo comprimido: {out_huf}")

        except Exception as e:
            st.warning(f"Informe guardado, pero falló la compresión Huffman: {e}")
            st.caption(f"Imagen original: {img_path}")
            st.caption("El estudio seguirá apuntando al archivo original.")
            st.success("✅ Informe guardado.")
