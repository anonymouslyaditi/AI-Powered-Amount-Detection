"""medical_bill package init

Public surface:
- ocr.read_image(file_path) -> (texts, confidences)
- utils.normalize_token, extract_raw_tokens, normalize_amounts, classify_amounts, infer_currency
"""

from .ocr import read_image
from . import utils

__all__ = ["read_image", "utils"]
