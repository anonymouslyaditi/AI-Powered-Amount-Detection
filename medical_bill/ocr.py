import easyocr

# Initialize a shared reader instance to avoid reloading models on every call
_reader = easyocr.Reader(['en'])


def read_image(file_path: str):
    """Read image at file_path using EasyOCR and return list of texts and confidences.

    Returns:
        texts: list of recognized text strings
        confidences: list of confidence floats matching texts
    """
    results = _reader.readtext(file_path)
    texts = [text for (_, text, _) in results]
    confidences = [conf for (_, _, conf) in results]
    return texts, confidences
