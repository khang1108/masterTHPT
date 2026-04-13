import cv2
import numpy as np


def convert_to_gray(image: np.ndarray) -> np.ndarray:
    """Chuyển ảnh BGR sang Grayscale."""
    if len(image.shape) == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image


def enhance_contrast(image: np.ndarray, clip_limit: float = 1.5, tile_size: int = 8) -> np.ndarray:
    """
    Tăng độ tương phản nhẹ bằng CLAHE.
    Với PDF sạch, clip_limit để thấp (1.5) để không làm gắt nét chữ, 
    nhưng đủ để chữ đen đậm hơn và nền trắng chuẩn hơn.
    """
    gray = convert_to_gray(image)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_size, tile_size))
    return clahe.apply(gray)


def preprocess_image(image: np.ndarray) -> np.ndarray:

    # 1. Chuyển xám và tăng tương phản
    enhanced = enhance_contrast(image)

    # 2. Chuyển lại 3 kênh để tương thích với PaddleOCR (yêu cầu BGR format)
    return cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
