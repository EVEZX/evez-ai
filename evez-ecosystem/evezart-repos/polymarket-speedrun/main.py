#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════╗
║  POLYMARKET SPEED-RUN BOT v1.0                               ║
║  Fastest flip. Evidence-driven. Zero bias.                   ║
║  Built by SureThing × EVEZ                                   ║
╚═══════════════════════════════════════════════════════════════╝

Usage:
    python main.py              # Run bot (uses .env config)
    python main.py --live       # Override to live mode
    python main.py --dry-run    # Override to dry-run mode
    python main.py --once       # Single scan + execute, then exit
    python main.py --scan-only  # Scan + score only, no trades
"""
import sys
import time
import signal
import argparse
from datetime import datetime, timezone

from config import config
from scanner import PolymarketScanner, EvidenceEngine, ScoringEngine
from executor import TradeExecutor
from display import (
    console, print_banner, print_scan_results,
    print_trade, print_portfolio, print_cycle_separator
)


# ─── Graceful Shutdown ───────────────────────────────────────

running = True

def shutdown_handler(signum, frame):
    global running
    console.print("\n\n🛑 Shutting down gracefully...", style="bold red")
    running = False

signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)


# ─── Main Loop ───────────────────────────────────────────────

def main():
    global running

    parser = argparse.ArgumentParser(description="Polymarket Speed-Run Bot")
    parser.add_argument("--live", action="store_true", help="Force live trading mode")
    parser.add_argument("--dry-run", action="store_true", help="Force dry-run mode")
    parser.add_argument("--once", action="store_true", help="Run one cycle then exit")
    parser.add_argument("--scan-only", action="store_true", help="Scan only, no execution")
    parser.add_argument("--budget", type=float, help="Override total budget")
    parser.add_argument("--max-bet", type=float, help="Override max bet size")
    parser.add_argument("--interval", type=int, help="Override scan interval (seconds)")
    parser.add_argument("--max-days", type=int, help="Override max days to resolve")
    args = parser.parse_args()

    # Apply overrides
    if args.live:
        config.mode = "live"
    elif args.dry_run:
        config.mode = "dry_run"
    if args.budget:
        config.strategy.total_budget = args.budget
    if args.max_bet:
        config.strategy.max_bet_size = args.max_bet
    if args.interval:
        config.scan_interval = args.interval
    if args.max_days:
        config.strategy.max_days = args.max_days

    # ── Initialize ──
    print_banner()

    console.print(f"  Mode:        [bold]{'🔴 LIVE' if config.mode == 'live' else '📝 DRY RUN'}[/bold]")
    console.print(f"  Budget:      [bold green]${config.strategy.total_budget:.2f}[/bold green]")
    console.print(f"  Max Bet:     [bold]${config.strategy.max_bet_size:.2f}[/bold]")
    console.print(f"  Min Score:   [bold]{config.strategy.min_score}[/bold]")
    console.print(f"  Min Payoff:  [bold]{config.strategy.min_payoff}x[/bold]")
    console.print(f"  Max Days:    [bold]{config.strategy.max_days}d[/bold]")
    console.print(f"  Scan Every:  [bold]{config.scan_interval}s[/bold]")
    console.print()

    if config.mode == "live":
        console.print(
            "  ⚠️  LIVE MODE — Real money will be spent!",
            style="bold red blink",
        )
        console.print("  Press Ctrl+C within 5 seconds to abort...")
        time.sleep(5)
        if not running:
            return

    scanner = PolymarketScanner()
    evidence_engine = EvidenceEngine()
    scoring_engine = ScoringEngine()
    executor = TradeExecutor()

    cycle = 0

    while running:
        cycle += 1
        console.rule(f"[bold cyan]CYCLE #{cycle} — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}[/bold cyan]")

        # ── Step 1: Scan Markets ──
        console.print("\n  📡 Scanning Polymarket...", style="dim")
        all_markets = scanner.fetch_all_markets(limit=500)
        console.print(f"  Found {len(all_markets)} total markets", style="dim")

        fast_markets = scanner.filter_speed_markets(all_markets)
        console.print(f"  Filtered to {len(fast_markets)} speed markets (<{config.strategy.max_days}d, >{config.strategy.min_payoff}x)", style="dim")

        if not fast_markets:
            console.print("  ⚠️ No markets match filters. Waiting...", style="yellow")
            if args.once:
                break
            time.sleep(config.scan_interval)
            continue

        # ── Step 2: Gather Evidence ──
        console.print("  🔬 Collecting evidence...", style="dim")
        evidence = evidence_engine.collect_all_evidence()
        console.print(f"  Gathered {len(evidence)} evidence points", style="dim")

        # ── Step 3: Score All Markets ──
        console.print("  🎯 Scoring markets...", style="dim")
        scored = []
        for m in fast_markets:
            sm = scoring_engine.score_market(m, evidence)
            scored.append(sm)

        scored.sort(key=lambda s: s.score, reverse=True)
        print_scan_results(scored, len(evidence))

        # ── Step 4: Execute Trades ──
        if not args.scan_only:
            console.print("\n  ⚡ Executing trades above threshold...\n", style="bold")

            qualified = [s for s in scored if s.score >= config.strategy.min_score]

            if not qualified:
                console.print(f"  No markets above score threshold ({config.strategy.min_score})", style="yellow")
            else:
                for sm in qualified:
                    if not running:
                        break
                    if not executor.can_afford(0.01):
                        console.print("  💰 Budget exhausted. Stopping execution.", style="yellow")
                        break

                    trade = executor.execute(sm)
                    print_trade(trade)

            # Portfolio summary
            console.print()
            print_portfolio(executor.get_portfolio_summary())

            # Save trades
            executor.save_trades_log(f"trades_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

        # ── Loop Control ──
        if args.once or args.scan_only:
            break

        if not executor.can_afford(0.01):
            console.print("\n  🏁 Budget fully deployed. Bot complete.", style="bold green")
            break

        print_cycle_separator(cycle, config.scan_interval)

        # Sleep with interrupt check
        for _ in range(config.scan_interval):
            if not running:
                break
            time.sleep(1)

    # ── Shutdown ──
    console.print("\n  📊 Final Portfolio:", style="bold")
    print_portfolio(executor.get_portfolio_summary())
    executor.save_trades_log("trades_final.json")
    console.print("\n  👋 Speed-Run Bot shutdown complete.\n", style="bold cyan")


if __name__ == "__main__":
    main()
