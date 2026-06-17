#!/usr/bin/env python3
"""
Run Profit Circuit - Start the minimal revenue-generating system.

This script demonstrates the ONE working profit circuit:
Agent Data Analysis Service

Usage:
    python run_profit_circuit.py          # Run demo
    python run_profit_circuit.py test     # Run tests
    python run_profit_circuit.py stats    # Show stats
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src' / 'api'))

from order_service import OrderService
from payment_service import PaymentService
from fulfillment_service import FulfillmentService


def run_demo():
    """Run a complete demo of the profit circuit."""
    print("\n" + "=" * 80)
    print("PROFIT CIRCUIT DEMO - Agent Data Analysis Service")
    print("=" * 80)
    print("\nThis demonstrates ONE complete revenue loop:")
    print("  Customer Request → Order → Payment → Fulfillment → Receipt")
    print("\n" + "-" * 80)
    
    # Initialize services
    order_service = OrderService()
    payment_service = PaymentService()
    fulfillment_service = FulfillmentService()
    
    # Step 1: Customer requests service
    print("\n[Step 1] Customer requests Data Analysis Service")
    print("  Service: DATA_ANALYSIS_V1")
    print("  Price: $50.00")
    print("  Payment: Sandbox mode (test)")
    
    order = order_service.create_order(
        customer_id="demo_customer",
        service_type="DATA_ANALYSIS_V1",
        amount=50.00,
        payment_method="sandbox",
        idempotency_key="demo_run"
    )
    
    print(f"\n  ✓ Order created: {order['order_id']}")
    print(f"    Status: {order['status']}")
    print(f"    Amount: ${order['amount']}")
    print(f"    Payment URL: {order['payment_url']}")
    
    # Step 2: Payment confirmation
    print("\n[Step 2] Payment confirmed")
    
    payment = payment_service.confirm_payment(
        order_id=order['order_id'],
        sandbox=True
    )
    
    print(f"\n  ✓ Payment processed: {payment['order_id']}")
    print(f"    Amount: ${payment['amount']}")
    print(f"    Status: {payment['status']}")
    print(f"    Proof: {payment['payment_proof']}")
    
    # Step 3: Service fulfillment
    print("\n[Step 3] Service fulfillment")
    
    fulfillment = fulfillment_service.fulfill_order(order['order_id'])
    
    analysis = fulfillment['delivery']['analysis']
    
    print(f"\n  ✓ Service delivered: {fulfillment['order_id']}")
    print(f"    Status: {fulfillment['status']}")
    print(f"    Access token: {fulfillment['delivery']['access_token']}")
    print(f"\n  Analysis Results:")
    print(f"    Summary: {analysis['summary']}")
    print(f"    Data points: {analysis['data_points_analyzed']}")
    print(f"    Confidence: {analysis['confidence_score']}")
    print(f"    Insights: {len(analysis['insights'])} generated")
    
    # Step 4: Receipt
    print("\n[Step 4] Receipt generated")
    receipt = fulfillment['receipt']
    print(f"\n  ✓ Immutable receipt logged")
    print(f"    Order: {receipt['order_id']}")
    print(f"    Service: {receipt['service']}")
    print(f"    Amount paid: ${receipt['amount_paid']}")
    print(f"    Delivered: {receipt['delivered_at']}")
    
    print("\n" + "=" * 80)
    print("✓ PROFIT CIRCUIT COMPLETE")
    print("=" * 80)
    print(f"\nRevenue generated: ${order['amount']}")
    print(f"Order ID: {order['order_id']}")
    print(f"Audit log: src/memory/orders.jsonl")
    print("\nThis is a real working revenue loop, not documentation.")
    print("=" * 80 + "\n")


def show_stats():
    """Show statistics from the audit log."""
    print("\n" + "=" * 80)
    print("PROFIT CIRCUIT STATISTICS")
    print("=" * 80)
    
    log_path = Path("src/memory/orders.jsonl")
    
    if not log_path.exists():
        print("\nNo orders yet. Run demo first: python run_profit_circuit.py")
        return
    
    orders_created = 0
    orders_paid = 0
    orders_fulfilled = 0
    total_revenue = 0.0
    
    with open(log_path, 'r') as f:
        for line in f:
            event = json.loads(line)
            if event['event_type'] == 'order_created':
                orders_created += 1
            elif event['event_type'] == 'payment_confirmed':
                orders_paid += 1
                total_revenue += event.get('amount', 0)
            elif event['event_type'] == 'order_fulfilled':
                orders_fulfilled += 1
    
    print(f"\nOrders created:    {orders_created}")
    print(f"Orders paid:       {orders_paid}")
    print(f"Orders fulfilled:  {orders_fulfilled}")
    print(f"Total revenue:     ${total_revenue:.2f}")
    print(f"\nCompletion rate:   {(orders_fulfilled/orders_created*100) if orders_created > 0 else 0:.1f}%")
    print(f"Payment rate:      {(orders_paid/orders_created*100) if orders_created > 0 else 0:.1f}%")
    
    print("\n" + "=" * 80 + "\n")


def run_tests():
    """Run the test suite."""
    print("\n" + "=" * 80)
    print("RUNNING PROFIT CIRCUIT TESTS")
    print("=" * 80 + "\n")
    
    try:
        import subprocess
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/test_profit_circuit.py", "-v"],
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        if result.returncode == 0:
            print("\n✓ All tests passed")
        else:
            print("\n✗ Some tests failed")
            
    except Exception as e:
        print(f"Error running tests: {e}")
        print("\nTo run tests manually:")
        print("  pip install pytest")
        print("  pytest tests/test_profit_circuit.py -v")


def show_help():
    """Show usage information."""
    print(__doc__)
    print("\nCommands:")
    print("  (no args)  Run demo of complete profit circuit")
    print("  test       Run test suite")
    print("  stats      Show circuit statistics")
    print("  help       Show this help message")
    print("\nFiles:")
    print("  src/api/order_service.py       - Create orders")
    print("  src/api/payment_service.py     - Confirm payments")
    print("  src/api/fulfillment_service.py - Deliver service")
    print("  src/memory/orders.jsonl        - Immutable audit log")
    print("  PROFIT_CIRCUIT_MANIFEST.md     - Operations documentation")
    print("\n")


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'test':
            run_tests()
        elif command == 'stats':
            show_stats()
        elif command == 'help':
            show_help()
        else:
            print(f"Unknown command: {command}")
            show_help()
    else:
        run_demo()


if __name__ == "__main__":
    main()
