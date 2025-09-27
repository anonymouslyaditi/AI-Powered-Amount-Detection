import re


def normalize_token(token: str):
    """Attempt to correct common OCR digit/character confusions and parse float.

    Returns float or None if parsing fails.
    """
    corrections = {'O':'0','o':'0','l':'1','I':'1','S':'5','s':'5'}
    for k, v in corrections.items():
        token = token.replace(k, v)
    token = token.replace(',', '').strip()
    token_clean = token.replace('%', '')
    try:
        return float(token_clean)
    except Exception:
        return None


def extract_raw_tokens(texts):
    """Extract numeric-like tokens from list of OCR text lines."""
    raw_tokens = []
    for text in texts:
        matches = re.findall(r'\d+[,.]?\d*%?', text)
        for m in matches:
            raw_tokens.append(m)
    return raw_tokens


def extract_raw_tokens_from_ocr(ocr_results):
    """Extract raw numeric tokens from OCR results in dict form.

    ocr_results: list of dicts like {'text':..., 'conf':..., 'bbox':...}
    Returns list of token strings.
    """
    texts = [entry.get('text', '') for entry in ocr_results]
    return extract_raw_tokens(texts)


def normalize_amounts(raw_tokens):
    """Normalize a list of raw tokens into list of dicts and a confidence.

    Returns (normalized_list, confidence) where normalized_list is a list of
    {'value': float, 'raw': original_token}
    """
    normalized = []
    parsed = 0
    for token in raw_tokens:
        val = normalize_token(token)
        if val is not None:
            parsed += 1
            normalized.append({'value': val, 'raw': token})
    if not normalized:
        return None, 0.0
    confidence = parsed / len(raw_tokens) if raw_tokens else 0.0
    # clamp to [0.5, 0.95] as a heuristic
    confidence = max(0.5, min(0.95, confidence))
    return normalized, confidence


def classify_amounts(ocr_texts_or_results, normalized_amounts):
    """Classify normalized amounts using contextual keywords in OCR texts.

    ocr_texts_or_results: either list of text strings or list of ocr dicts
    normalized_amounts: list of dicts {'value':float,'raw':str}

    Returns (amounts_list, confidence)
    """
    # normalize input texts
    if not ocr_texts_or_results:
        return [], 0.0
    if isinstance(ocr_texts_or_results[0], dict):
        texts = [e.get('text','') for e in ocr_texts_or_results]
    else:
        texts = ocr_texts_or_results

    amounts = []
    context_keywords = {
        'total_bill': ['total','grand total','amount due','amount:','bill'],
        'paid': ['paid','payment','paid:'],
        'due': ['due','balance','amount due']
    }

    used_values = set()
    for text in texts:
        for label, keywords in context_keywords.items():
            for kw in keywords:
                if kw.lower() in text.lower():
                    matches = re.findall(r'\d+[,.]?\d*', text)
                    for m in matches:
                        try:
                            val = float(m.replace(',',''))
                        except Exception:
                            continue
                        # find matching normalized entry (by value)
                        for n in normalized_amounts:
                            if abs(n['value'] - val) < 0.001 and n['value'] not in used_values:
                                amounts.append({
                                    'type': label,
                                    'value': n['value'],
                                    'source': f"text: '{text}'",
                                })
                                used_values.add(n['value'])
                                break

    # Fallback: assign largest to total if no classification
    if not any(a['type']=='total_bill' for a in amounts) and normalized_amounts:
        largest = max(normalized_amounts, key=lambda x: x['value'])
        amounts.append({
            'type':'total_bill',
            'value': largest['value'],
            'source': f"raw: '{largest['raw']}'"
        })

    confidence = 0.75 if amounts else 0.0
    return amounts, confidence


def infer_currency(texts):
    for text in texts:
        if re.search(r'\u20b9|\bRs\b|\bINR\b', text, re.I):
            return 'INR'
        if re.search(r'\$', text):
            return 'USD'
    return 'INR'
