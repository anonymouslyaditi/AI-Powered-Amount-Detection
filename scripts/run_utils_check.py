import sys
import os
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, repo_root)
from medical_bill import utils

def run_check():
    ocr_results = [
        {'text': 'Total: INR 1200', 'conf': 0.95, 'bbox': None},
        {'text': 'Paid: 1000', 'conf': 0.9, 'bbox': None},
        {'text': 'Due: 200', 'conf': 0.85, 'bbox': None},
    ]
    raw = utils.extract_raw_tokens_from_ocr(ocr_results)
    print('raw tokens:', raw)
    normalized, conf = utils.normalize_amounts(raw)
    print('normalized:', normalized, 'conf:', conf)
    values = [e['value'] for e in normalized]
    print('values set:', values)
    assert 1200.0 in values
    assert 1000.0 in values
    assert 200.0 in values
    amounts, class_conf = utils.classify_amounts(ocr_results, normalized)
    print('classified:', amounts, 'class_conf:', class_conf)
    types = {a['type'] for a in amounts}
    assert 'total_bill' in types
    assert 'paid' in types or 'due' in types
    print('All checks passed')

if __name__ == '__main__':
    run_check()
