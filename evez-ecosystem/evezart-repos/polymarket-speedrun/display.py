"""
Terminal Display — Rich-based dashboard for monitoring the bot.
"""
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich import box
from datetime import datetime, timezone

console = Console()


def print_banner():
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║     ⚡ POLYMARKET SPEED-RUN BOT v1.0 ⚡                      ║
║     Fastest flip. Evidence-driven. Zero bias.                ║
║     Built by SureThing × EVEZ                                ║
╚═══════════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")


def print_scan_results(scored_markets, evidence_count: int):
    """Display scored markets in a rich table."""
    table = Table(
        title="🔍 MARKET SCAN RESULTS",
        box=box.DOUBLE_EDGE,
        show_lines=True,
        title_style="bold yellow",
    )
    table.add_column("#", style="dim", width=3)
    table.add_column("Market", style="white", max_width=45)
    table.add_column("Side", style="bold", width=4)
    table.add_column("Price", style="cyan", width=7)
    table.add_column("Payoff", style="green", width=7)
    table.add_column("Days", style="yellow", width=6)
    table.add_column("Score", style="bold magenta", width=7)
    table.add_column("Size $", style="bold green", width=7)
    table.add_column("⚡SPD", style="dim", width=5)
    table.add_column("💰PAY", style="dim", width=5)
    table.add_column("🔬EVI", style="dim", width=5)
    table.add_column("📊VOL", style="dim", width=5)

    for i, sm in enumerate(scored_markets[:25], 1):
        m = sm.market

        # Color-code the score
        if sm.score >= 70:
            score_style = "bold green"
        elif sm.score >= 50:
            score_style = "bold yellow"
        else:
            score_style = "bold red"

        # Color-code the side
        side_style = "bold green" if sm.recommended_side == "YES" else "bold red"

        table.add_row(
            str(i),
            m.question[:45],
            Text(sm.recommended_side, style=side_style),
            f"${sm.market.best_price:.3f}",
            f"{m.best_payoff:.1f}x",
            f"{m.days_to_resolve:.1f}",
            Text(f"{sm.score:.1f}", style=score_style),
            f"${sm.recommended_size:.2f}",
            f"{sm.speed_score:.0f}",
            f"{sm.payoff_score:.0f}",
            f"{sm.evidence_score:.0f}",
            f"{sm.volume_score:.0f}",
        )

    console.print(table)
    console.print(
        f"  📡 Evidence points: {evidence_count} | "
        f"Scan time: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}",
        style="dim",
    )


def print_trade(trade):
    """Display a single trade execution."""
    if trade.status in ("filled", "simulated"):
        icon = "🟢" if trade.mode == "live" else "📝"
        style = "green"
    elif trade.status == "skipped":
        icon = "⏭️"
        style = "yellow"
    else:
        icon = "🔴"
        style = "red"

    mode_tag = "[LIVE]" if trade.mode == "live" else "[DRY]"

    console.print(
        f"  {icon} {mode_tag} {trade.side} "
        f"{trade.market_question[:50]}... "
        f"@ ${trade.price:.3f} | "
        f"${trade.size_usd:.2f} → ${trade.max_payoff:.2f} "
        f"({trade.multiplier:.1f}x) "
        f"[Score: {trade.score:.0f}]",
        style=style,
    )
    if trade.error:
        console.print(f"    ⚠️ {trade.error}", style="red dim")


def print_portfolio(summary):
    """Display portfolio summary."""
    panel_text = (
        f"Trades: {summary['total_trades']} | "
        f"Spent: ${summary['total_spent']:.2f} / "
        f"${summary['total_spent'] + summary['budget_remaining']:.2f} | "
        f"Remaining: ${summary['budget_remaining']:.2f}\n"
        f"Max Payoff: ${summary['total_max_payoff']:.2f} | "
        f"Avg Multiplier: {summary['avg_multiplier']:.1f}x"
    )
    console.print(
        Panel(panel_text, title="💼 PORTFOLIO", border_style="cyan", box=box.ROUNDED)
    )


def print_cycle_separator(cycle: int, interval: int):
    console.print(
        f"\n{'─'*60}\n"
        f"  ⏱️  Cycle #{cycle} complete. Next scan in {interval}s...\n"
        f"{'─'*60}",
        style="dim",
    )
