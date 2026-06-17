import sqlite3
import os
from cryptography.fernet import Fernet

# Generate or load a local key for encryption
key_file = 'nomad.key'
if not os.path.exists(key_file):
    key = Fernet.generate_key()
    with open(key_file, 'wb') as key_out:
        key_out.write(key)
else:
    with open(key_file, 'rb') as key_in:
        key = key_in.read()

cipher = Fernet(key)


def init_vault():
    conn = sqlite3.connect('evez_core.db')
    c = conn.cursor()
    # Table for persistent configuration (API Keys, Tokens)
    c.execute('''CREATE TABLE IF NOT EXISTS config (
                    key_name TEXT PRIMARY KEY,
                    encrypted_value TEXT)''')
    # Table for agent cognition context (last thoughts, current task)
    c.execute('''CREATE TABLE IF NOT EXISTS cognition_mesh (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    context_blob TEXT)''')
    conn.commit()
    conn.close()
    print(">> Vault Initialized: evez_core.db")


def save_config(key_name, value):
    conn = sqlite3.connect('evez_core.db')
    encrypted = cipher.encrypt(value.encode())
    conn.execute('REPLACE INTO config (key_name, encrypted_value) VALUES (?, ?)',
                 (key_name, encrypted))
    conn.commit()
    conn.close()


def load_config(key_name):
    conn = sqlite3.connect('evez_core.db')
    cursor = conn.execute('SELECT encrypted_value FROM config WHERE key_name=?', (key_name,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return cipher.decrypt(result[0]).decode()
    return None


if __name__ == "__main__":
    init_vault()
    # Run once to seed your keys (uncomment and fill in real values):
    # save_config('TELEGRAM_BOT_TOKEN', 'YOUR_ACTUAL_TOKEN_HERE')
    # save_config('OPENROUTER_API_KEY', 'YOUR_KEY_HERE')
    # save_config('GROQ_API_KEY', 'YOUR_KEY_HERE')
    # save_config('GITHUB_PAT', 'YOUR_PAT_HERE')
    print(">> To seed credentials, uncomment save_config lines above and re-run.")
