import cv2
import numpy as np


def segment_lungs(img: np.ndarray) -> np.ndarray:
    pixel_values = img.reshape((-1, 1)).astype(np.float32)

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    k = 2
    _, labels, centers = cv2.kmeans(
        pixel_values, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS
    )

    centers = np.uint8(centers)
    mask = centers[labels.flatten()].reshape(img.shape)

    th = float(np.mean(centers))
    binary_mask = (mask < th).astype(np.uint8) * 255

    kernel = np.ones((5, 5), np.uint8)
    binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel)

    return binary_mask
