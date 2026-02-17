from typing import Tuple
import cv2
import numpy as np


def preprocess_rx(img: np.ndarray, size: Tuple[int, int] = (512, 512)) -> np.ndarray:
    img_resized = cv2.resize(img, size, interpolation=cv2.INTER_AREA)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(img_resized)
