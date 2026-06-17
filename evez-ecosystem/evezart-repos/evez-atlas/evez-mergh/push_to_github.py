"""Push evez-merch to GitHub via Composio"""
from composio import Composio
import os

composio = Composio(api_key="COMPOSIO_KEY_REDACTED")

# List connected accounts
accounts = composio.connected_accounts.get()
for acc in accounts:
    print(f"Connected: {acc.id} ({acc.appName})")
