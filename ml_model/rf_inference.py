from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import cv2
import joblib
import numpy as np
import pandas as pd

from image_processing.preprocess import preprocess_rx
from image_processing.segmentation import segment_lungs
from image_processing.features import extract_features

# Diccionario de clases
CLASES: Dict[int, str] = {
    0: "Normal",
    1: "Procesos Inflamatorios (Neumonía)",
    2: "Mayor Densidad (Derrame/Consolidación)",
    3: "Menor Densidad (Neumotórax)",
    4: "Obstructivas (EPOC)",
    5: "Infecciosas Degenerativas (TBC/Fibrosis)",
    6: "Lesiones Encapsuladas (Nódulos)",
    7: "Alteraciones Mediastino",
    8: "Alteraciones Tórax",
}


@dataclass(frozen=True)
class RFResult:
    pred_idx: int
    label: str
    score: float
    proba: np.ndarray
    top3: List[Tuple[str, float]]
    img_original: np.ndarray
    img_prep: np.ndarray
    mask: np.ndarray
    img_roi: np.ndarray


def load_rf_model(model_path: Path):
    return joblib.load(str(model_path))


def predict_from_image_path_with_model(image_path: Path, clf) -> RFResult:
    img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"No se pudo leer la imagen: {image_path}")

    img_prep = preprocess_rx(img)
    mask = segment_lungs(img_prep)

    img_roi = img_prep.copy()
    img_roi[mask == 0] = 0

    feats = extract_features(img_roi)
    if feats is None:
        raise ValueError("La segmentación falló: ROI vacía.")

    df = pd.DataFrame([feats])

    if hasattr(clf, "feature_names_in_"):
        df = df.reindex(columns=list(clf.feature_names_in_), fill_value=0)

    pred_idx = int(clf.predict(df)[0])
    proba = clf.predict_proba(df)[0].astype(float)

    label = CLASES.get(pred_idx, "Desconocido")
    score = float(proba[pred_idx])

    top_idx = np.argsort(proba)[::-1][:3]
    top3 = [(CLASES.get(int(i), f"Clase {int(i)}"), float(proba[i])) for i in top_idx]

    return RFResult(
        pred_idx=pred_idx,
        label=label,
        score=score,
        proba=proba,
        top3=top3,
        img_original=img,
        img_prep=img_prep,
        mask=mask,
        img_roi=img_roi,
    )


def predict_from_image_path(image_path: Path, model_path: Path) -> RFResult:
    clf = load_rf_model(model_path)
    return predict_from_image_path_with_model(image_path, clf)