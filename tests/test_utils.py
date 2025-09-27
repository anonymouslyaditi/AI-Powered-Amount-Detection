from medical_bill import utils


def test_normalize_and_classify_basic():
    # synthetic OCR results similar to sample
    ocr_results = [
        {'text': 'Total: INR 1200', 'conf': 0.95, 'bbox': None},
        {'text': 'Paid: 1000', 'conf': 0.9, 'bbox': None},
        {'text': 'Due: 200', 'conf': 0.85, 'bbox': None},
    ]

    raw = utils.extract_raw_tokens_from_ocr(ocr_results)
    assert len(raw) >= 3

    normalized, conf = utils.normalize_amounts(raw)
    assert len(normalized) >= 3
    values = [e['value'] for e in normalized]
    assert 1200.0 in values
    assert 1000.0 in values
    assert 200.0 in values

    amounts, class_conf = utils.classify_amounts(ocr_results, normalized)
    types = {a['type'] for a in amounts}
    assert 'total_bill' in types
    assert 'paid' in types or 'due' in types
    