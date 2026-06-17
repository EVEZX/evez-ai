"""
LLM Cost Optimizer - CLI interface
"""
import json
import click
from pathlib import Path
from .analyzer import CostAnalyzer, UsageEntry, PRICING
from datetime import datetime
import random


@click.group()
def cli():
    """LLM Cost Optimizer — analyze and reduce your LLM API spending."""
    pass


@cli.command()
@click.option("--input", "input_path", required=True, type=click.Path(exists=True), help="Path to usage log JSON file or directory")
@click.option("--output", "output_path", type=click.Path(), help="Save report to file")
def analyze(input_path, output_path):
    """Analyze LLM usage and suggest cost optimizations."""
    analyzer = CostAnalyzer()
    p = Path(input_path)
    if p.is_dir():
        for f in p.glob("*.json"):
            analyzer.load_from_json(f)
    else:
        analyzer.load_from_json(p)

    report = analyzer.run_analysis()

    click.echo("\n💰 LLM Cost Analysis Report")
    click.echo("=" * 50)
    click.echo(f"Total entries: {report['total_entries']}")
    click.echo(f"Total cost: ${report['total_cost_usd']:.2f}")
    click.echo(f"Potential savings: ${report['total_potential_savings_usd']:.2f} ({report['total_potential_savings_pct']}%)")

    click.echo("\n📊 Cost by Model:")
    for model, cost in sorted(report["cost_by_model"].items(), key=lambda x: -x[1]):
        click.echo(f"  {model:40s} ${cost:>8.2f}")

    click.echo("\n📊 Cost by Task:")
    for task, cost in sorted(report["cost_by_task"].items(), key=lambda x: -x[1]):
        click.echo(f"  {task:20s} ${cost:>8.2f}")

    if report["optimizations"]:
        click.echo("\n🔧 Optimizations:")
        for i, opt in enumerate(report["optimizations"], 1):
            click.echo(f"  {i}. [{opt['type'].upper()}] {opt['description']}")
            click.echo(f"     Savings: ${opt['savings_usd']:.2f} ({opt['savings_pct']}%) | Confidence: {opt['confidence']*100:.0f}%")
            click.echo(f"     Action: {opt['action']}")

    if output_path:
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        click.echo(f"\n📄 Report saved to {output_path}")


@cli.command()
@click.option("--entries", default=100, help="Number of sample entries to generate")
@click.option("--output", "output_path", default="sample_usage.json", help="Output file")
def generate(entries, output_path):
    """Generate sample usage data for testing."""
    models = list(PRICING.keys())
    tasks = ["general", "coding", "classification", "extraction", "summary", "creative", "analysis"]
    data = []
    for i in range(entries):
        model = random.choice(models)
        task = random.choice(tasks)
        input_tokens = random.randint(50, 4000)
        output_tokens = random.randint(20, 3000) if task not in ("classification", "extraction") else random.randint(5, 300)
        data.append({
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "task_type": task,
            "session_id": f"sess_{random.randint(1, 20)}",
            "cached": random.random() < 0.1,
        })
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    click.echo(f"Generated {entries} entries → {output_path}")


@cli.command()
def models():
    """Show supported models and pricing."""
    click.echo("\n📋 Supported Models & Pricing (per 1M tokens)")
    click.echo("-" * 60)
    click.echo(f"{'Model':40s} {'Input':>8s} {'Output':>8s}")
    click.echo("-" * 60)
    for model, pricing in sorted(PRICING.items(), key=lambda x: x[1]["input"]):
        click.echo(f"{model:40s} ${pricing['input']:>6.2f} ${pricing['output']:>6.2f}")


if __name__ == "__main__":
    cli()
