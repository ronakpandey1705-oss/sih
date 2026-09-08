import os
import cv2
import numpy as np
from typing import Tuple, Dict, Any, Optional


class ImagePreprocessor:
    """
    OpenCV-based image preprocessing pipeline designed for photographed
    packaged commodity labels to maximize PaddleOCR accuracy.
    """

    @staticmethod
    def read_image_safe(file_path: str) -> Optional[np.ndarray]:
        """Read image from path safely, handling Unicode/Windows path characters."""
        if not os.path.exists(file_path):
            return None
        # Use imdecode with fromfile to safely support paths with spaces or special characters on Windows
        try:
            with open(file_path, "rb") as f:
                bytes_arr = bytearray(f.read())
                np_arr = np.asarray(bytes_arr, dtype=np.uint8)
                img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                return img
        except Exception:
            return cv2.imread(file_path)

    @staticmethod
    def write_image_safe(file_path: str, img: np.ndarray) -> bool:
        """Write image to path safely, handling Unicode/Windows path characters."""
        try:
            ext = os.path.splitext(file_path)[1]
            if not ext:
                ext = ".png"
            success, encoded_img = cv2.imencode(ext, img)
            if success:
                with open(file_path, "wb") as f:
                    encoded_img.tofile(f)
                return True
        except Exception:
            return cv2.imwrite(file_path, img)
        return False

    @staticmethod
    def resize_for_ocr(image: np.ndarray, min_dimension: int = 640, max_dimension: int = 1280) -> Tuple[np.ndarray, float]:
        """
        Resize image so text is sufficiently large for OCR detection,
        without consuming excessive memory for ultra-high-resolution images.
        Constrained to max 1280px to stay well within 512MB RAM budgets.
        """
        h, w = image.shape[:2]
        max_side = max(h, w)
        min_side = min(h, w)
        scale = 1.0

        if min_side < min_dimension:
            scale = min_dimension / float(min_side)
        elif max_side > max_dimension:
            scale = max_dimension / float(max_side)

        if scale != 1.0:
            new_w = int(w * scale)
            new_h = int(h * scale)
            interpolation = cv2.INTER_CUBIC if scale > 1.0 else cv2.INTER_AREA
            resized = cv2.resize(image, (new_w, new_h), interpolation=interpolation)
            return resized, scale

        return image, scale

    @staticmethod
    def to_grayscale(image: np.ndarray) -> np.ndarray:
        """Convert BGR image to single channel grayscale."""
        if len(image.shape) == 2:
            return image
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    @staticmethod
    def denoise(gray_image: np.ndarray) -> np.ndarray:
        """Apply bilateral filter to smooth packaging noise while preserving sharp font edges."""
        return cv2.bilateralFilter(gray_image, d=7, sigmaColor=50, sigmaSpace=50)

    @staticmethod
    def enhance_contrast(gray_image: np.ndarray, clip_limit: float = 2.0, tile_size: int = 8) -> np.ndarray:
        """
        Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        to handle harsh shadows, reflections, and uneven phone flash lighting.
        """
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_size, tile_size))
        return clahe.apply(gray_image)

    @staticmethod
    def detect_skew_angle(gray_image: np.ndarray) -> float:
        """
        Estimate packaging text skew angle in degrees using thresholding and minimum area rect.
        Returns angle between -45 and 45 degrees.
        """
        try:
            # Invert and threshold to get text foreground
            thresh = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
            coords = np.column_stack(np.where(thresh > 0))
            if len(coords) < 100:
                return 0.0

            rect = cv2.minAreaRect(coords)
            angle = rect[-1]

            # Normalize angle to [-45, 45]
            if angle < -45:
                angle = -(90 + angle)
            elif angle > 45:
                angle = 90 - angle
            else:
                angle = -angle

            return float(angle)
        except Exception:
            return 0.0

    @staticmethod
    def rotate_image(image: np.ndarray, angle: float) -> np.ndarray:
        """Rotate image by specified angle degrees around center."""
        if abs(angle) < 0.5:
            return image

        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        rot_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Calculate new bounding dimensions
        cos = np.abs(rot_matrix[0, 0])
        sin = np.abs(rot_matrix[0, 1])
        new_w = int((h * sin) + (w * cos))
        new_h = int((h * cos) + (w * sin))

        rot_matrix[0, 2] += (new_w / 2) - center[0]
        rot_matrix[1, 2] += (new_h / 2) - center[1]

        rotated = cv2.warpAffine(
            image,
            rot_matrix,
            (new_w, new_h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )
        return rotated

    @staticmethod
    def adaptive_binarize(gray_image: np.ndarray) -> np.ndarray:
        """Binarize image with Gaussian adaptive thresholding."""
        return cv2.adaptiveThreshold(
            gray_image,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            15,
            5
        )

    @classmethod
    def process_pipeline(
        cls,
        image_path: str,
        output_path: Optional[str] = None,
        deskew: bool = True
    ) -> Dict[str, Any]:
        """
        Execute the complete packaging image enhancement pipeline.
        Original image is untouched.
        Returns preprocessed image path and execution metrics.
        """
        img = cls.read_image_safe(image_path)
        if img is None:
            raise FileNotFoundError(f"Could not read image at path: {image_path}")

        orig_h, orig_w = img.shape[:2]

        # 1. Resize for optimal OCR performance
        resized_img, scale_factor = cls.resize_for_ocr(img)

        # 2. Grayscale conversion
        gray = cls.to_grayscale(resized_img)

        # 3. Denoising
        denoised = cls.denoise(gray)

        # 4. CLAHE Contrast Enhancement
        enhanced = cls.enhance_contrast(denoised)

        # 5. Deskewing
        skew_angle = 0.0
        final_img = enhanced
        if deskew:
            detected_skew = cls.detect_skew_angle(enhanced)
            if 0.5 <= abs(detected_skew) <= 35.0:
                final_img = cls.rotate_image(enhanced, detected_skew)
                skew_angle = detected_skew

        # 6. Save preprocessed image
        if not output_path:
            dir_name = os.path.dirname(image_path)
            base_name, _ = os.path.splitext(os.path.basename(image_path))
            output_path = os.path.join(dir_name, f"{base_name}_preprocessed.png")

        cls.write_image_safe(output_path, final_img)

        proc_h, proc_w = final_img.shape[:2]
        del img, resized_img, gray, denoised, enhanced, final_img
        import gc
        gc.collect()

        return {
            "preprocessed_path": output_path,
            "original_dimensions": [orig_h, orig_w],
            "preprocessed_dimensions": [proc_h, proc_w],
            "scale_factor": scale_factor,
            "skew_angle_detected": skew_angle,
            "clahe_applied": True,
            "denoised": True
        }
