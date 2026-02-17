from typing import Dict, Optional
import numpy as np
from scipy.stats import skew, kurtosis
from skimage.feature import graycomatrix, graycoprops


def _entropy_shannon_from_pixels(pixels: np.ndarray) -> float:
    hist, _ = np.histogram(pixels, bins=256, range=(1, 255))
    prob = hist / np.sum(hist)
    prob = prob[prob > 0]
    return float(-np.sum(prob * np.log2(prob)))


def extract_features(img_roi: np.ndarray) -> Optional[Dict[str, float]]:
    pixels = img_roi[img_roi > 0]
    if pixels.size == 0:
        return None

    entropy_val = _entropy_shannon_from_pixels(pixels)

    hist_feats = {
        "mean": float(np.mean(pixels)),
        "std": float(np.std(pixels)),
        "skew": float(skew(pixels)),
        "kurtosis": float(kurtosis(pixels)),
        "entropy": float(entropy_val),
        "max": float(np.max(pixels)),
        "min": float(np.min(pixels)),
    }

    levels = 32
    scale = 256 // levels
    img_binned = (img_roi // scale).astype(np.uint8)

    glcm = graycomatrix(
        img_binned,
        distances=[1],
        angles=[0, np.pi / 4, np.pi / 2, 3 * np.pi / 4],
        levels=levels,
        symmetric=True,
        normed=True,
    )

    glcm_feats = {
        "contrast": float(graycoprops(glcm, "contrast").mean()),
        "dissimilarity": float(graycoprops(glcm, "dissimilarity").mean()),
        "homogeneity": float(graycoprops(glcm, "homogeneity").mean()),
        "energy": float(graycoprops(glcm, "energy").mean()),
        "correlation": float(graycoprops(glcm, "correlation").mean()),
        "asm": float(graycoprops(glcm, "ASM").mean()),
    }

    return {**hist_feats, **glcm_feats}
