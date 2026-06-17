"""
tracker.py — polymarket-speedrun
Append-only P&L ledger. Persists every trade to trades.jsonl.
Computes running P&L, win rate, average hold time.
Emails daily summary to rubikspubes69@gmail.com.
Resolves: polymarket-speedrun#1 Phase 1

Usage:
  from tracker import record_trade, get_summary, email_daily_summary
"""

import json
import os
import smtplib
from pathlib import Path
from datetime import datetime, timezone
from email.mime.text import MIMEText

TRADES_LOG   = Path(os.environ.get("TRADES_LOG", "trades.jsonl"))
NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", "rubikspubes69@gmail.com")
GMAIL_USER   = os.environ.get("GMAIL_USER", "")
GMAIL_PASS   = os.environ.get("GMAIL_PASS", "")


def record_trade(
    market: str,
    outcome: str,
    amount_usd: float,
    result: str,          # "win" | "loss" | "push"
    pnl: float,
    hold_seconds: float = 0.0,
) -> dict:
    summary = get_summary()
    pnl_running = round(summary["total_pnl"] + pnl, 4)
    entry = {
        "ts":          datetime.now(timezone.utc).isoformat(),
        "market":      market,
        "outcome":     outcome,
        "amount_usd":  amount_usd,
        "result":      result,
        "pnl":         round(pnl, 4),
        "pnl_running": pnl_running,
        "hold_s":      round(hold_seconds, 1),
    }
    with open(TRADES_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"[tracker] Trade recorded: {result} | pnl={pnl:+.4f} | running={pnl_running:+.4f}")
    return entry


def get_summary() -> dict:
    if not TRADES_LOG.exists():
        return {"total_trades": 0, "wins": 0, "losses": 0, "win_rate": 0.0,
                "total_pnl": 0.0, "avg_hold_s": 0.0, "last_trades": []}
    entries, wins, losses, total_pnl, hold_total = [], 0, 0, 0.0, 0.0
    with open(TRADES_LOG) as f:
        for line in f:
            try:
                e = json.loads(line)
                entries.append(e)
                total_pnl += float(e.get("pnl", 0))
                hold_total += float(e.get("hold_s", 0))
                if e.get("result") == "win":  wins += 1
                elif e.get("result") == "loss": losses += 1
            except Exception:
                pass
    n = len(entries)
    return {
        "total_trades": n,
        "wins":         wins,
        "losses":       losses,
        "win_rate":     round(wins / n, 4) if n else 0.0,
        "total_pnl":    round(total_pnl, 4),
        "avg_hold_s":   round(hold_total / n, 1) if n else 0.0,
        "last_trades":  entries[-10:],
    }


def email_daily_summary():
    s = get_summary()
    subject = f"[Polymarket] Daily P&L | {datetime.now(timezone.utc).date()} | {s['total_pnl']:+.4f} USD"
    body = (
        f"Polymarket Speedrun — Daily P&L Summary\n"
        f"{'='*45}\n"
        f"Total trades  : {s['total_trades']}\n"
        f"Wins / Losses : {s['wins']} / {s['losses']}\n"
        f"Win rate      : {s['win_rate']*100:.1f}%\n"
        f"Total P&L     : {s['total_pnl']:+.4f} USD\n"
        f"Avg hold time : {s['avg_hold_s']:.0f}s\n\n"
        f"Last 10 trades:\n"
        + "\n".join(
            f"  [{e['ts'][:16]}] {e['market']} → {e['result']} | {e['pnl']:+.4f}"
            for e in s["last_trades"]
        )
    )
    if not GMAIL_USER or not GMAIL_PASS:
        print(f"[tracker] EMAIL SKIP:\n{body}")
        return
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = GMAIL_USER
        msg["To"]   = NOTIFY_EMAIL
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL_USER, GMAIL_PASS)
            smtp.sendmail(GMAIL_USER, NOTIFY_EMAIL, msg.as_string())
        print(f"[tracker] Daily summary email sent.")
    except Exception as e:
        print(f"[tracker] Email error: {e}")
