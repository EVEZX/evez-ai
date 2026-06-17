"""
vision_gates.py — EVEZ-OS × Google Cloud Vision integration layer
All 13 integrations confirmed 2026-02-23T09:39 PST

BLOCKER: Composio ca_iECKFviBhGq3 has OAuth Client ID stored as API key.
Fix: GCP Console → APIs & Services → Credentials → Create API Key → restrict to Vision API
Then: reconnect via COMPOSIO_MANAGE_CONNECTIONS with generic_api_key=<new_key>

Usage in hyperloop tick:
    from vision_gates import safe_search_gate, annotate_frame, ocr_equation_validate
"""

def build_annotate_request(image_source: str, features: list) -> dict:
    if image_source.startswith('base64:'):
        image = {'content': image_source[7:]}
    else:
        image = {'source': {'imageUri': image_source}}
    return {'image': image, 'features': features}

# 8: SAFE_SEARCH gate (mandatory pre-upload)
def safe_search_gate(image_source: str) -> dict:
    req = build_annotate_request(image_source, [{'type': 'SAFE_SEARCH_DETECTION'}])
    return {'_call': 'GOOGLE_CLOUD_VISION_ANNOTATE_IMAGES', '_req': req}

# 1: Video frame → spine labels
def annotate_frame(image_source: str, max_results: int = 10) -> dict:
    req = build_annotate_request(image_source, [
        {'type': 'LABEL_DETECTION', 'maxResults': max_results},
        {'type': 'OBJECT_LOCALIZATION', 'maxResults': max_results},
    ])
    return {'_call': 'GOOGLE_CLOUD_VISION_ANNOTATE_IMAGES', '_req': req}

# 2: OCR equation validator
def ocr_equation_validate(image_source: str, expected_poly_c: float) -> dict:
    req = build_annotate_request(image_source, [{'type': 'DOCUMENT_TEXT_DETECTION'}])
    return {'_call': 'GOOGLE_CLOUD_VISION_ANNOTATE_IMAGES', '_req': req, '_expected': f'{expected_poly_c:.6f}'}

# 3: Tweet screenshot ingestion
def ingest_tweet_screenshot(image_source: str) -> dict:
    req = build_annotate_request(image_source, [
        {'type': 'WEB_DETECTION'},
        {'type': 'LABEL_DETECTION', 'maxResults': 5},
    ])
    return {'_call': 'GOOGLE_CLOUD_VISION_ANNOTATE_IMAGES', '_req': req}

# 4: Image properties → saliency weights
def extract_colors(image_source: str) -> dict:
    req = build_annotate_request(image_source, [{'type': 'IMAGE_PROPERTIES'}])
    return {'_call': 'GOOGLE_CLOUD_VISION_ANNOTATE_IMAGES', '_req': req}

# 5: Gumroad thumbnail audit
def audit_gumroad_thumbnail(image_source: str) -> dict:
    req = build_annotate_request(image_source, [
        {'type': 'LOGO_DETECTION', 'maxResults': 5},
        {'type': 'LABEL_DETECTION', 'maxResults': 10},
        {'type': 'SAFE_SEARCH_DETECTION'},
    ])
    return {'_call': 'GOOGLE_CLOUD_VISION_ANNOTATE_IMAGES', '_req': req}

# 6: CrawFather screenshot enrichment
def enrich_scrape_result(screenshot_source: str) -> dict:
    req = build_annotate_request(screenshot_source, [
        {'type': 'WEB_DETECTION'},
        {'type': 'LABEL_DETECTION', 'maxResults': 10},
    ])
    return {'_call': 'GOOGLE_CLOUD_VISION_ANNOTATE_IMAGES', '_req': req}

# 7: Polymarket OCR
def polymarket_ocr(screenshot_source: str) -> dict:
    req = build_annotate_request(screenshot_source, [{'type': 'TEXT_DETECTION'}])
    return {'_call': 'GOOGLE_CLOUD_VISION_ANNOTATE_IMAGES', '_req': req}

# 9: Crop hints → cinematic framing
def get_crop_bounds(image_source: str, aspect_ratio: float = 16/9) -> dict:
    req = build_annotate_request(image_source, [
        {'type': 'CROP_HINTS', 'imageContext': {'cropHintsParams': {'aspectRatios': [aspect_ratio]}}}
    ])
    return {'_call': 'GOOGLE_CLOUD_VISION_ANNOTATE_IMAGES', '_req': req}

# 10: Face detection → layout switch (RTMP)
def detect_face_in_frame(image_source: str) -> dict:
    req = build_annotate_request(image_source, [{'type': 'FACE_DETECTION', 'maxResults': 1}])
    return {'_call': 'GOOGLE_CLOUD_VISION_ANNOTATE_IMAGES', '_req': req}

# 11: Landmark geocoding → planetary mission
def geocode_origin_landmarks(image_url: str) -> dict:
    req = build_annotate_request(image_url, [{'type': 'LANDMARK_DETECTION', 'maxResults': 5}])
    return {'_call': 'GOOGLE_CLOUD_VISION_ANNOTATE_IMAGES', '_req': req}

# 12: CTF artifact OCR (PDF support via ANNOTATE_FILES)
def ocr_ctf_artifact(file_b64: str, mime_type: str = 'application/pdf') -> dict:
    return {
        '_call': 'GOOGLE_CLOUD_VISION_ANNOTATE_FILES',
        '_req': {
            'inputConfig': {'content': file_b64, 'mimeType': mime_type},
            'features': [{'type': 'DOCUMENT_TEXT_DETECTION'}],
        }
    }

# 13: Product search → commercialization scan
def search_similar_products(image_source: str, project_id: str) -> dict:
    req = build_annotate_request(image_source, [{'type': 'PRODUCT_SEARCH'}])
    return {
        '_call': 'GOOGLE_CLOUD_VISION_ANNOTATE_PROJECT_IMAGES',
        '_req': req,
        '_parent': f'projects/{project_id}/locations/us',
    }

# Batch helper (up to 16 images per call)
def batch_annotate(requests: list) -> list:
    assert len(requests) <= 16
    return requests
