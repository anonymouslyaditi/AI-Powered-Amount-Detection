# Medical Bill Amount Extractor

This repository provides a small FastAPI service that extracts monetary amounts from medical bill images. It performs OCR, normalizes numeric tokens, classifies each amount by context (total/paid/due), and returns a final structured JSON with provenance.

## Repository layout

- `app.py` - FastAPI application / request routing
- `medical_bill/ocr.py` - EasyOCR wrapper (reads images)
- `medical_bill/utils.py` - normalization & classification helpers
- `scripts/run_demo.py` - helper to run uvicorn locally and optionally open an ngrok tunnel
- `sample_inputs/` - place sample images here (uploads are saved here by the server)

---

## Architecture (high-level)

1. Upload image -> `POST /extract/` (multipart/form-data, field name `file`).
2. Guardrail: quick blurriness check using OpenCV (Laplacian variance). If too blurry, the API immediately returns:

   {"status": "no_amounts_found", "reason": "document too noisy"}

3. OCR: `medical_bill.ocr.read_image()` (EasyOCR) returns recognized text lines + confidences.
4. Raw token extraction: `utils.extract_raw_tokens_from_ocr()` pulls numeric-like tokens from OCR output.
5. Normalization: `utils.normalize_amounts()` attempts to correct OCR digit confusions and parse numbers.
6. Classification: `utils.classify_amounts()` uses contextual keywords to label amounts (total/paid/due).
7. Final structured JSON is returned with currency, normalized values, classification, confidences, and provenance.

---

## Setup (Windows PowerShell)

1. (Recommended) Create & activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

Notes:
- `easyocr` and `torch` are heavy dependencies and can take several minutes to install. On Windows you may want to follow PyTorch's official install instructions to pick the correct wheel for your platform.
- `opencv-python-headless` is used for the blur guardrail. If you don't want OpenCV, the app will skip the blur check (but we recommend installing it for better guardrails).
- `pyngrok` is optional and only needed if you want to expose a public URL.

---

## Quick start / Demo

- Run locally (no ngrok):

```powershell
python .\scripts\run_demo.py --port 8000
```

- Run and expose the local server over an ngrok tunnel (requires `pyngrok` and optionally an ngrok auth token):

```powershell
python .\scripts\run_demo.py --port 8000 --ngrok
# If you have an ngrok authtoken, register it for more reliable tunnels:
# ngrok authtoken <YOUR_TOKEN>
```

When `--ngrok` is used the script prints a public URL you can use to call the API from remote clients.

---

## API usage

Endpoint: `POST /extract/`
- Content-Type: multipart/form-data
- Field name: `file` (the image file)

Examples

- Python (requests):

```python
import requests

url = 'http://127.0.0.1:8000/extract/'
files = {'file': open('sample_inputs/sample_receipt.png','rb')}
resp = requests.post(url, files=files)
print(resp.status_code, resp.json())
```

- Postman: create a POST request to `/extract/`, set body to `form-data`, add a key `file` of type File.

Responses (examples)

- Blurry / noisy image guardrail (early exit):

```json
{"status":"no_amounts_found","reason":"document too noisy"}
```

- Successful (example shape):

```json
{
  "currency": "INR",
  "raw_tokens": ["1200","1000","200","10%"],
  "confidence_raw": 0.74,
  "normalized_amounts": [1200, 1000, 200],
  "normalization_confidence": 0.82,
  "amounts": [
    {"type":"total_bill","value":1200,"source":"text: 'Total: INR 1200'"},
    {"type":"paid","value":1000,"source":"text: 'Paid: 1000'"},
    {"type":"due","value":200,"source":"text: 'Due: 200'"}
  ],
  "classification_confidence": 0.8,
  "status": "ok"
}
```

---

