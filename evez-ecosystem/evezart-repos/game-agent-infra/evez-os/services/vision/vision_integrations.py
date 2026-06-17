"""
vision_integrations.py — integration spec + priority map
All 13 confirmed 2026-02-23T09:39 PST by Steven Crawford-Maggard (EVEZ)

PIPELINE SLOT MAP:

  Hyperloop tick (pre-upload):
    8  → safe_search_gate           MANDATORY — account health gate
    9  → get_crop_bounds             cinematic framing before render
    1  → annotate_frame              spine labels → state[rN_result][vision_labels]
    2  → ocr_equation_validate       eq crystal OCR → formula integrity gate
    4  → extract_colors              dominant colors → VCL saliency_weights

  Post-tweet:
    3  → ingest_tweet_screenshot     web_entities confirms post live

  Agentnet loop:
    7  → polymarket_ocr              screenshot OCR → prob% (faster than browser-use)
    6  → enrich_scrape_result        CrawFather output → synthesis context

  Gumroad pre-publish:
    5  → audit_gumroad_thumbnail     logo+label+safe_search pass/fail

  On-demand:
    11 → geocode_origin_landmarks    Bullhead City → planetary mission coords
    12 → ocr_ctf_artifact            CTF L2-L6 PDF/image → solver input

  Future (infra not yet ready):
    10 → detect_face_in_frame        RTMP frames → layout switch via Ably
    13 → search_similar_products     VCL export → market scan (needs GCP catalog)

API KEY FIX REQUIRED:
    Composio connection ca_iECKFviBhGq3 has OAuth Client ID as key (invalid).
    Fix: GCP Console → APIs & Services → Credentials → Create API Key
         Restrict key to: Cloud Vision API only
         Then reconnect: COMPOSIO_MANAGE_CONNECTIONS(toolkit='google_cloud_vision',
                          action='connect', reinitiate=True,
                          parameters={'generic_api_key': '<new_key>'})
"""

INTEGRATION_PRIORITY = [
    # id, name, status, blocker
    (8,  'safe_search_gate',              'READY',   'api_key_fix'),
    (1,  'annotate_frame',                'READY',   'api_key_fix + workbench_recovery'),
    (2,  'ocr_equation_validate',         'READY',   'api_key_fix + workbench_recovery'),
    (4,  'extract_colors',                'READY',   'api_key_fix + workbench_recovery'),
    (3,  'ingest_tweet_screenshot',       'READY',   'api_key_fix'),
    (7,  'polymarket_ocr',                'READY',   'api_key_fix'),
    (5,  'audit_gumroad_thumbnail',       'READY',   'api_key_fix'),
    (9,  'get_crop_bounds',               'DESIGN',  'api_key_fix + workbench_recovery'),
    (6,  'enrich_scrape_result',          'DESIGN',  'api_key_fix + CrawFather_CI'),
    (11, 'geocode_origin_landmarks',      'READY',   'api_key_fix'),
    (12, 'ocr_ctf_artifact',              'PENDING', 'api_key_fix + CTF_L2_unlock'),
    (10, 'detect_face_in_frame',          'PENDING', 'RTMP_stream + Ably_key'),
    (13, 'search_similar_products',       'DESIGN',  'GCP_product_catalog_setup'),
]
