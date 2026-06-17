"""
Speed-Run Bot Configuration
Loads .env and provides typed config access.
"""
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

@dataclass
class WalletConfig:
    private_key: str = os.getenv("PRIVATE_KEY", "")
    address: str = os.getenv("WALLET_ADDRESS", "")

@dataclass
class PolyConfig:
    api_key: str = os.getenv("POLY_API_KEY", "")
    api_secret: str = os.getenv("POLY_API_SECRET", "")
    passphrase: str = os.getenv("POLY_API_PASSPHRASE", "")
    clob_url: str = "https://clob.polymarket.com"
    gamma_url: str = "https://gamma-api.polymarket.com"

@dataclass
class StrategyConfig:
    max_bet_size: float = float(os.getenv("MAX_BET_SIZE", "2.00"))
    total_budget: float = float(os.getenv("TOTAL_BUDGET", "10.00"))
    min_score: float = float(os.getenv("MIN_SCORE_THRESHOLD", "65"))
    min_payoff: float = float(os.getenv("MIN_PAYOFF_MULTIPLIER", "2.0"))
    max_days: int = int(os.getenv("MAX_DAYS_TO_RESOLVE", "14"))

@dataclass
class Config:
    wallet: WalletConfig = field(default_factory=WalletConfig)
    poly: PolyConfig = field(default_factory=PolyConfig)
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    mode: str = os.getenv("MODE", "dry_run")
    scan_interval: int = int(os.getenv("SCAN_INTERVAL", "60"))

config = Config()
