from fastapi import FastAPI, UploadFile, File
try:
    import cv2
except Exception:
    cv2 = None

# Laplacian variance threshold for blur detection; images with variance below this
# are considered too noisy/blurred for reliable OCR
BLUR_THRESHOLD = 100.0
import shutil
import os

from medical_bill import ocr
from medical_bill import utils

# Ensure folders exist
if not os.path.exists("sample_inputs"):
    os.makedirs("sample_inputs")

# Initialize FastAPI app
app = FastAPI(title="Medical Bill Amount Extractor API")


@app.get("/")
def read_root():
    return {"message": "Medical Bill Amount Extractor API is running!"}


@app.post("/extract/")
async def extract_amounts(file: UploadFile = File(...)):
    # Save uploaded file
    file_path = f"sample_inputs/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Guardrail: check for blurriness and exit early if the image is too noisy
    if cv2 is not None:
        try:
            img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
            if img is not None:
                fm = cv2.Laplacian(img, cv2.CV_64F).var()
                # optional: log fm somewhere; for now we just check threshold
                if fm < BLUR_THRESHOLD:
                    return {"status": "no_amounts_found", "reason": "document too noisy"}
        except Exception:
            # If OpenCV fails for any reason, continue to OCR path rather than failing
            pass

    # Step 1: OCR (returns list of texts and confidences)
    extracted_texts, confidences = ocr.read_image(file_path)

    if not extracted_texts:
        # Guardrail for completely failed OCR: return standardized exit JSON
        return {"status": "no_amounts_found", "reason": "document too noisy"}

    # some utils helpers accept OCR-style dicts in tests; create a minimal OCR dict list
    ocr_results = [{'text': t, 'conf': c, 'bbox': None} for t, c in zip(extracted_texts, confidences)]

    raw_tokens = utils.extract_raw_tokens_from_ocr(ocr_results)
    currency_hint = utils.infer_currency(extracted_texts)
    confidence_step1 = sum(confidences) / len(confidences) if confidences else 0.7

    # Step 2: Normalize
    normalized_amounts, confidence_norm = utils.normalize_amounts(raw_tokens)
    if not normalized_amounts:
        # No numeric tokens survived normalization -> consider document too noisy
        return {"status": "no_amounts_found", "reason": "document too noisy"}

    # Step 3: Classification (utils expects ocr results or texts)
    classified_amounts, confidence_class = utils.classify_amounts(ocr_results, normalized_amounts)

    # Step 4: Final output
    return {
        "currency": currency_hint,
        "raw_tokens": raw_tokens,
        "confidence_raw": round(confidence_step1, 2),
        "normalized_amounts": [n['value'] for n in normalized_amounts],
        "normalization_confidence": round(confidence_norm, 2),
        "amounts": classified_amounts,
        "classification_confidence": round(confidence_class, 2),
        "status": "ok",
    }

