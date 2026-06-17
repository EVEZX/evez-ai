"""
config.py — API key loading from environment variables.
All keys loaded at runtime; never hardcoded.
"""
import os

class Config:
    GROQ_API_KEY              = os.environ["GROQ_API_KEY"]
    OPENAI_API_KEY            = os.environ["OPENAI_API_KEY"]
    PERPLEXITY_API_KEY        = os.environ["PERPLEXITY_API_KEY"]
    ALL_IMAGES_API_KEY        = os.environ["ALL_IMAGES_API_KEY"]
    ELEVENLABS_API_KEY        = os.environ["ELEVENLABS_API_KEY"]
    CLOUDCONVERT_API_KEY      = os.environ["CLOUDCONVERT_API_KEY"]
    CONVERTAPI_SECRET         = os.environ["CONVERTAPI_SECRET"]
    ALCHEMY_API_KEY           = os.environ["ALCHEMY_API_KEY"]
    ALCHEMY_ENTROPIC_CONTRACT = os.environ["ALCHEMY_ENTROPIC_CONTRACT"]
    ALCHEMY_VOID_CONTRACT     = os.environ["ALCHEMY_VOID_CONTRACT"]
    ALCHEMY_CHRONO_CONTRACT   = os.environ["ALCHEMY_CHRONO_CONTRACT"]
    STRIPE_SECRET_KEY         = os.environ["STRIPE_SECRET_KEY"]
    ABLY_API_KEY              = os.environ["ABLY_API_KEY"]
    CLARITY_PROJECT_ID        = os.environ["CLARITY_PROJECT_ID"]
    MEM0_API_KEY              = os.environ["MEM0_API_KEY"]
    GITHUB_TOKEN              = os.environ["GITHUB_TOKEN"]
    VERCEL_TOKEN              = os.environ["VERCEL_TOKEN"]
    EVEZ_BASE_URL             = os.environ.get("EVEZ_BASE_URL", "https://evez.art")
    MIRO_ACCESS_TOKEN         = os.environ["MIRO_ACCESS_TOKEN"]
    VAPI_API_KEY              = os.environ["VAPI_API_KEY"]
    DEEPGRAM_API_KEY          = os.environ["DEEPGRAM_API_KEY"]
    HYPERBROWSER_API_KEY      = os.environ["HYPERBROWSER_API_KEY"]
    AGENTMAIL_API_KEY         = os.environ["AGENTMAIL_API_KEY"]
