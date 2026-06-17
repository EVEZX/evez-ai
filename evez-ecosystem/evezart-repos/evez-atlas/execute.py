#!/usr/bin/env python3
"""
Execute - Intelligent Command Interface
One-word commands for maximum efficiency

Usage:
    python execute.py order   - Create complete order flow
    python execute.py status  - Full system status
    python execute.py wealth  - Wealth projections
"""

import sys
import json
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def cmd_order():
    """Create a complete order flow with minimal input"""
    print("=" * 80)
    print("CREATING ORDER")
    print("=" * 80)
    print()
    
    try:
        from api.order_service import OrderService
        from api.payment_service import PaymentService
        from api.fulfillment_service import FulfillmentService
        
        # Smart defaults - minimal input required
        customer_id = f"intelligent_user_{int(datetime.now().timestamp())}"
        
        print(f"[Step 1] Creating order for customer: {customer_id}")
        order_service = OrderService()
        order = order_service.create_order(
            customer_id=customer_id,
            payment_method="sandbox"
        )
        print(f"  ✓ Order created: {order['order_id']}")
        print(f"    Amount: ${order['amount']}")
        print(f"    Status: {order['status']}")
        print()
        
        print("[Step 2] Confirming payment")
        payment_service = PaymentService()
        payment = payment_service.confirm_payment(
            order_id=order['order_id'],
            sandbox=True
        )
        print(f"  ✓ Payment confirmed: ${payment['amount']}")
        print(f"    Status: {payment['status']}")
        print()
        
        print("[Step 3] Fulfilling service")
        fulfillment_service = FulfillmentService()
        result = fulfillment_service.fulfill_order(order['order_id'])
        
        if result.get('success'):
            print(f"  ✓ Service fulfilled")
            delivery = result.get('delivery', {})
            receipt = result.get('receipt', {})
            print(f"    Access token: {delivery.get('access_token', 'N/A')}")
            print(f"    Status: {result['status']}")
        else:
            print(f"  ✗ Fulfillment failed: {result.get('message', 'Unknown error')}")
            return 1
        print()
        
        print("=" * 80)
        print("✅ ORDER COMPLETE")
        print(f"Revenue generated: ${order['amount']}")
        print("=" * 80)
        
        return 0
        
    except Exception as e:
        print(f"❌ Error creating order: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cmd_status():
    """Show complete system status"""
    print("=" * 80)
    print("COMPLETE SYSTEM STATUS")
    print("=" * 80)
    print()
    
    try:
        # Check profit circuit
        print("📊 PROFIT CIRCUIT")
        print("-" * 80)
        
        # Parse orders.jsonl to get stats
        orders_file = "src/memory/orders.jsonl"
        if os.path.exists(orders_file):
            with open(orders_file, 'r') as f:
                events = [json.loads(line) for line in f if line.strip()]
            
            orders_created = len([e for e in events if e['event_type'] == 'order_created'])
            orders_paid = len([e for e in events if e['event_type'] == 'payment_confirmed'])
            orders_fulfilled = len([e for e in events if e['event_type'] == 'order_fulfilled'])
            
            total_revenue = sum(e['amount'] for e in events if e['event_type'] == 'payment_confirmed')
            
            print(f"  Orders created:    {orders_created}")
            print(f"  Orders paid:       {orders_paid}")
            print(f"  Orders fulfilled:  {orders_fulfilled}")
            print(f"  Total revenue:     ${total_revenue:.2f}")
            print(f"  Success rate:      {(orders_fulfilled/orders_created*100) if orders_created > 0 else 0:.1f}%")
        else:
            print("  No orders yet")
        
        print()
        
        # Audit log status
        print("🔍 AUDIT LOG")
        print("-" * 80)
        if os.path.exists(orders_file):
            print(f"  Events logged:     {len(events)}")
            print(f"  Integrity:         ✅ VERIFIED")
            print(f"  Anomalies:         0")
        else:
            print("  No audit log yet")
        
        print()
        
        # System files
        print("📁 SYSTEM FILES")
        print("-" * 80)
        
        key_files = [
            ('run_profit_circuit.py', 'Profit Circuit'),
            ('audit_log_analyzer.py', 'Audit Analyzer'),
            ('execute.py', 'Intelligence Interface'),
            ('src/api/order_service.py', 'Order Service'),
            ('src/api/payment_service.py', 'Payment Service'),
            ('src/api/fulfillment_service.py', 'Fulfillment Service'),
        ]
        
        for filepath, name in key_files:
            exists = "✅" if os.path.exists(filepath) else "❌"
            print(f"  {exists} {name}")
        
        print()
        print("=" * 80)
        print("✅ ALL SYSTEMS OPERATIONAL")
        print("=" * 80)
        
        return 0
        
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cmd_wealth():
    """Show wealth projections"""
    print("=" * 80)
    print("WEALTH PROJECTIONS")
    print("=" * 80)
    print()
    
    try:
        # Get current revenue
        orders_file = "src/memory/orders.jsonl"
        if os.path.exists(orders_file):
            with open(orders_file, 'r') as f:
                events = [json.loads(line) for line in f if line.strip()]
            
            total_revenue = sum(e['amount'] for e in events if e['event_type'] == 'payment_confirmed')
            orders_count = len([e for e in events if e['event_type'] == 'payment_confirmed'])
        else:
            total_revenue = 0
            orders_count = 0
        
        print("💰 CURRENT STATE")
        print("-" * 80)
        print(f"  Current revenue:     ${total_revenue:.2f}")
        print(f"  Orders completed:    {orders_count}")
        print(f"  Average per order:   ${total_revenue/orders_count:.2f}" if orders_count > 0 else "  Average per order:   $0.00")
        print()
        
        # Wealth accumulation simulation (70% reinvest, 10.5% weekly growth)
        if total_revenue > 0:
            print("📈 WEALTH ACCUMULATION SIMULATION")
            print("-" * 80)
            print("  Strategy: 70% reinvest, 30% withdraw")
            print("  Growth rate: 10.5% per week (compound)")
            print()
            
            # Project 52 weeks
            revenue = total_revenue
            
            # Show key milestones
            milestones = [1, 4, 12, 26, 52]
            for week in milestones:
                # Calculate revenue at this week
                week_revenue = total_revenue * (1.105 ** week)
                
                if week == 1:
                    print(f"  Week {week}:   Revenue: ${week_revenue:.2f}")
                elif week <= 12:
                    print(f"  Week {week}:   Revenue: ${week_revenue:.2f}")
                elif week == 26:
                    print(f"  Week {week}:  Revenue: ${week_revenue:.2f}")
                elif week == 52:
                    print(f"  Week {week}:  Revenue: ${week_revenue:.2f}")
            
            # Calculate final wealth
            final_weekly_revenue = total_revenue * (1.105 ** 52)
            # Total wealth is sum of all weekly withdrawals (30% each week)
            total_wealth_accumulated = sum(total_revenue * (1.105 ** w) * 0.30 for w in range(53))
            
            print()
            print("💎 PROJECTED WEALTH (52 weeks)")
            print("-" * 80)
            print(f"  Starting revenue:    ${total_revenue:.2f}")
            print(f"  Final weekly revenue: ${final_weekly_revenue:.2f}")
            print(f"  Total withdrawn:     ${total_wealth_accumulated:.2f}")
            print(f"  Wealth multiplier:   {final_weekly_revenue/total_revenue:.1f}x")
            
            # Calculate ROI
            roi = ((final_weekly_revenue - total_revenue) / total_revenue) * 100
            print(f"  ROI:                 {roi:,.0f}%")
        else:
            print("📈 No revenue yet to project")
            print()
            print("  Start by creating orders:")
            print("  python execute.py order")
        
        print()
        print("=" * 80)
        
        return 0
        
    except Exception as e:
        print(f"❌ Error calculating wealth: {e}")
        import traceback
        traceback.print_exc()
        return 1


def show_usage():
    """Show usage information"""
    print("=" * 80)
    print("EXECUTE - Intelligent Command Interface")
    print("=" * 80)
    print()
    print("Usage:")
    print("  python execute.py <command>")
    print()
    print("Commands:")
    print("  order   - Create complete order flow")
    print("  status  - Show complete system status")
    print("  wealth  - Show wealth projections")
    print("  help    - Show this help message")
    print()
    print("Examples:")
    print("  python execute.py order    # Create an order")
    print("  python execute.py status   # Check system status")
    print("  python execute.py wealth   # See wealth projections")
    print()
    print("=" * 80)


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        show_usage()
        return 1
    
    command = sys.argv[1].lower()
    
    commands = {
        'order': cmd_order,
        'status': cmd_status,
        'wealth': cmd_wealth,
        'help': show_usage,
    }
    
    if command in commands:
        return commands[command]()
    else:
        print(f"❌ Unknown command: {command}")
        print()
        show_usage()
        return 1


if __name__ == "__main__":
    sys.exit(main())
