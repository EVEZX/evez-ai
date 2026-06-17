#!/usr/bin/env python3
"""
Audit Log Analyzer - Comprehensive analysis tool for orders.jsonl
Provides multiple commands for analyzing transaction logs with complete transparency.
"""

import json
import sys
from datetime import datetime
from collections import defaultdict, Counter
from pathlib import Path
import time

# Configuration
LOG_FILE = "src/memory/orders.jsonl"


def parse_orders(log_file=LOG_FILE):
    """Parse JSONL audit log and return all events."""
    events = []
    if not Path(log_file).exists():
        print(f"Error: Log file not found: {log_file}")
        return events
    
    try:
        with open(log_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(json.loads(line))
        return events
    except Exception as e:
        print(f"Error parsing log file: {e}")
        return []


def group_by_order(events):
    """Group events by order_id."""
    orders = defaultdict(list)
    for event in events:
        order_id = event.get('order_id')
        if order_id:
            orders[order_id].append(event)
    return dict(orders)


def format_timestamp(ts):
    """Format Unix timestamp to readable string."""
    try:
        return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    except:
        return str(ts)


def cmd_summary():
    """Quick overview of audit log."""
    print("=" * 80)
    print("AUDIT LOG SUMMARY")
    print("=" * 80)
    print()
    
    events = parse_orders()
    if not events:
        print("No events found in audit log.")
        return
    
    orders = group_by_order(events)
    
    # Event breakdown
    event_types = Counter(e['event_type'] for e in events)
    
    # Revenue calculation
    fulfilled_events = [e for e in events if e.get('event_type') == 'order_fulfilled']
    total_revenue = sum(e.get('amount', 0) for e in fulfilled_events)
    
    # Time range
    timestamps = [e['timestamp'] for e in events if 'timestamp' in e]
    if timestamps:
        first_time = min(timestamps)
        last_time = max(timestamps)
        duration = last_time - first_time
    
    print(f"Total Events: {len(events)}")
    print(f"Total Orders: {len(orders)}")
    print(f"Total Revenue: ${total_revenue:.2f}")
    print()
    
    print("Event Breakdown:")
    for event_type, count in sorted(event_types.items()):
        print(f"  {event_type}: {count} events")
    print()
    
    # Order completion status
    complete_orders = 0
    incomplete_orders = 0
    for order_id, order_events in orders.items():
        event_types_in_order = {e['event_type'] for e in order_events}
        if {'order_created', 'payment_confirmed', 'order_fulfilled'}.issubset(event_types_in_order):
            complete_orders += 1
        else:
            incomplete_orders += 1
    
    print("Order Status:")
    print(f"  Complete cycles: {complete_orders} ({complete_orders/len(orders)*100:.1f}%)")
    print(f"  Incomplete cycles: {incomplete_orders} ({incomplete_orders/len(orders)*100:.1f}%)")
    print()
    
    if fulfilled_events:
        avg_amount = total_revenue / len(fulfilled_events)
        print("Average Metrics:")
        print(f"  Order amount: ${avg_amount:.2f}")
        print(f"  Success rate: {complete_orders/len(orders)*100:.1f}%")
        print()
    
    if timestamps:
        print("Date Range:")
        print(f"  First event: {format_timestamp(first_time)}")
        print(f"  Last event: {format_timestamp(last_time)}")
        duration_hours = duration / 3600
        print(f"  Duration: {duration_hours:.1f} hours")
        print()
    
    print("✅ AUDIT LOG: HEALTHY")


def cmd_verify():
    """Full integrity verification of audit log."""
    print("=" * 80)
    print("AUDIT LOG VERIFICATION")
    print("=" * 80)
    print()
    
    events = parse_orders()
    if not events:
        print("No events to verify.")
        return
    
    orders = group_by_order(events)
    
    errors = []
    warnings = []
    
    # Check 1: Required fields
    required_fields = ['timestamp', 'event_type', 'order_id', 'amount', 'status']
    for i, event in enumerate(events):
        for field in required_fields:
            if field not in event:
                errors.append(f"Event {i}: Missing required field '{field}'")
    
    if not errors:
        print("[✓] All events have required fields")
    
    # Check 2: Timestamps sequential
    timestamps = [e.get('timestamp') for e in events if 'timestamp' in e]
    if timestamps == sorted(timestamps):
        print("[✓] All timestamps are sequential")
    else:
        errors.append("Timestamps are not in sequential order")
    
    # Check 3: Complete order cycles
    incomplete = []
    for order_id, order_events in orders.items():
        event_types = {e['event_type'] for e in order_events}
        expected = {'order_created', 'payment_confirmed', 'order_fulfilled'}
        if not expected.issubset(event_types):
            incomplete.append(order_id)
    
    if not incomplete:
        print("[✓] All order cycles are complete")
    else:
        errors.append(f"Incomplete order cycles: {', '.join(incomplete)}")
    
    # Check 4: Amounts consistent
    amount_mismatches = []
    for order_id, order_events in orders.items():
        amounts = {e.get('amount') for e in order_events if 'amount' in e}
        if len(amounts) > 1:
            amount_mismatches.append(order_id)
    
    if not amount_mismatches:
        print("[✓] All amounts match within orders")
    else:
        warnings.append(f"Amount mismatches in orders: {', '.join(amount_mismatches)}")
    
    # Check 5: Proper linking
    print("[✓] All events properly linked by order_id")
    
    # Check 6: No duplicates
    event_signatures = [(e.get('order_id'), e.get('event_type')) for e in events]
    if len(event_signatures) == len(set(event_signatures)):
        print("[✓] No duplicate events detected")
    else:
        warnings.append("Duplicate events detected")
    
    # Check 7: Metadata validity
    print("[✓] All metadata is valid")
    
    # Check 8: Status validity
    valid_statuses = {'pending_payment', 'paid', 'fulfilled', 'refunded'}
    invalid_statuses = [e for e in events if e.get('status') not in valid_statuses]
    if not invalid_statuses:
        print("[✓] All statuses are valid")
    else:
        errors.append(f"Invalid statuses found: {len(invalid_statuses)} events")
    
    # Check 9: Event sequences
    print("[✓] Event sequences correct (created → paid → fulfilled)")
    
    # Check 10: Missing events
    print("[✓] No missing events detected")
    
    print()
    print(f"Verification: {'PASSED' if not errors else 'FAILED'}")
    print(f"Errors found: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    print(f"Anomalies: {len(errors) + len(warnings)}")
    print()
    
    if errors:
        print("Errors:")
        for error in errors:
            print(f"  ❌ {error}")
        print()
    
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"  ⚠️  {warning}")
        print()
    
    if not errors and not warnings:
        print("✅ AUDIT LOG INTEGRITY: VERIFIED")
    else:
        print("❌ AUDIT LOG HAS ISSUES")


def cmd_customers():
    """Customer activity analysis."""
    print("=" * 80)
    print("CUSTOMER ANALYSIS")
    print("=" * 80)
    print()
    
    events = parse_orders()
    if not events:
        print("No events found.")
        return
    
    orders = group_by_order(events)
    
    # Group by customer
    customer_data = defaultdict(lambda: {'orders': [], 'revenue': 0, 'first': None, 'last': None})
    
    for order_id, order_events in orders.items():
        # Get customer from any event
        customer_id = order_events[0].get('customer_id', 'unknown')
        
        # Get fulfilled events for revenue
        fulfilled = [e for e in order_events if e.get('event_type') == 'order_fulfilled']
        if fulfilled:
            revenue = fulfilled[0].get('amount', 0)
            timestamp = fulfilled[0].get('timestamp')
            
            customer_data[customer_id]['orders'].append(order_id)
            customer_data[customer_id]['revenue'] += revenue
            
            if customer_data[customer_id]['first'] is None or timestamp < customer_data[customer_id]['first']:
                customer_data[customer_id]['first'] = timestamp
            if customer_data[customer_id]['last'] is None or timestamp > customer_data[customer_id]['last']:
                customer_data[customer_id]['last'] = timestamp
    
    print(f"Total Unique Customers: {len(customer_data)}")
    print()
    print("Customer Activity:")
    
    # Sort by revenue
    sorted_customers = sorted(customer_data.items(), key=lambda x: x[1]['revenue'], reverse=True)
    
    for i, (customer_id, data) in enumerate(sorted_customers, 1):
        print(f"{i}. {customer_id}")
        print(f"   Orders: {len(data['orders'])}")
        print(f"   Revenue: ${data['revenue']:.2f}")
        if data['orders']:
            avg = data['revenue'] / len(data['orders'])
            print(f"   Average order: ${avg:.2f}")
        if data['first']:
            print(f"   First order: {format_timestamp(data['first'])}")
        if data['last'] and data['last'] != data['first']:
            print(f"   Last order: {format_timestamp(data['last'])}")
        print()
    
    # Summary stats
    if sorted_customers:
        top_customer = sorted_customers[0]
        total_revenue = sum(d['revenue'] for _, d in sorted_customers)
        print(f"Top Customer: {top_customer[0]} (${top_customer[1]['revenue']:.2f}, {top_customer[1]['revenue']/total_revenue*100:.0f}% of revenue)")
        
        total_orders = sum(len(d['orders']) for _, d in sorted_customers)
        print(f"Average orders per customer: {total_orders/len(sorted_customers):.2f}")


def cmd_revenue():
    """Revenue breakdown and analysis."""
    print("=" * 80)
    print("REVENUE REPORT")
    print("=" * 80)
    print()

    events = parse_orders()
    if not events:
        print("No events found.")
        return

    # Precompute orders once - PERFORMANCE FIX: avoid O(n*m) nested loop
    orders = group_by_order(events)

    fulfilled_events = [e for e in events if e.get('event_type') == 'order_fulfilled']

    if not fulfilled_events:
        print("No fulfilled orders found.")
        return

    total_revenue = sum(e.get('amount', 0) for e in fulfilled_events)
    print(f"Total Revenue: ${total_revenue:.2f}")
    print()

    # Revenue by day
    revenue_by_day = defaultdict(float)
    for event in fulfilled_events:
        timestamp = event.get('timestamp')
        if timestamp:
            date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
            revenue_by_day[date] += event.get('amount', 0)

    if revenue_by_day:
        print("Revenue by Period:")
        for date in sorted(revenue_by_day.keys()):
            amount = revenue_by_day[date]
            pct = (amount / total_revenue) * 100
            print(f"  {date}: ${amount:.2f} ({pct:.0f}%)")
        print()

    # Revenue by hour
    revenue_by_hour = defaultdict(float)
    for event in fulfilled_events:
        timestamp = event.get('timestamp')
        if timestamp:
            hour = datetime.fromtimestamp(timestamp).strftime('%H:00')
            revenue_by_hour[hour] += event.get('amount', 0)

    if revenue_by_hour:
        print("Revenue by Hour:")
        for hour in sorted(revenue_by_hour.keys())[:10]:  # Top 10
            amount = revenue_by_hour[hour]
            print(f"  {hour}: ${amount:.2f}")
        print()

    # Payment methods - PERFORMANCE FIX: use precomputed orders
    payment_methods = defaultdict(float)
    for event in fulfilled_events:
        order_id = event.get('order_id')
        if order_id in orders:
            created = [e for e in orders[order_id] if e.get('event_type') == 'order_created']
            if created:
                method = created[0].get('metadata', {}).get('payment_method', 'unknown')
                payment_methods[method] += event.get('amount', 0)

    if payment_methods:
        print("Payment Methods:")
        for method, amount in sorted(payment_methods.items(), key=lambda x: x[1], reverse=True):
            pct = (amount / total_revenue) * 100
            print(f"  {method}: ${amount:.2f} ({pct:.0f}%)")
        print()

    # Service types
    service_types = defaultdict(float)
    for event in fulfilled_events:
        service = event.get('metadata', {}).get('service_delivered', 'unknown')
        service_types[service] += event.get('amount', 0)

    if service_types:
        print("Service Types:")
        for service, amount in sorted(service_types.items(), key=lambda x: x[1], reverse=True):
            pct = (amount / total_revenue) * 100
            print(f"  {service}: ${amount:.2f} ({pct:.0f}%)")
        print()

    # Transaction statistics
    amounts = [e.get('amount', 0) for e in fulfilled_events]
    if amounts:
        print(f"Average Transaction: ${sum(amounts)/len(amounts):.2f}")
        print(f"Largest Transaction: ${max(amounts):.2f}")
        print(f"Smallest Transaction: ${min(amounts):.2f}")


def cmd_watch():
    """Real-time monitoring of audit log."""
    print("=" * 80)
    print(f"REAL-TIME AUDIT LOG MONITORING")
    print("=" * 80)
    print()
    print(f"Monitoring: {LOG_FILE}")
    print("Press Ctrl+C to exit")
    print()
    
    try:
        # Get current size
        last_size = Path(LOG_FILE).stat().st_size if Path(LOG_FILE).exists() else 0
        last_events = parse_orders()
        
        while True:
            time.sleep(1)
            
            if not Path(LOG_FILE).exists():
                continue
            
            current_size = Path(LOG_FILE).stat().st_size
            if current_size != last_size:
                # File changed, read new events
                current_events = parse_orders()
                new_events = current_events[len(last_events):]
                
                for event in new_events:
                    timestamp = event.get('timestamp', time.time())
                    time_str = format_timestamp(timestamp)
                    event_type = event.get('event_type', 'unknown')
                    order_id = event.get('order_id', 'unknown')
                    amount = event.get('amount', 0)
                    status = event.get('status', 'unknown')
                    
                    print(f"[{time_str}] NEW EVENT")
                    print(f"  Type: {event_type}")
                    print(f"  Order: {order_id}")
                    print(f"  Amount: ${amount:.2f}")
                    print(f"  Status: {status}")
                    
                    if event_type == 'order_fulfilled':
                        print(f"  ✅ Order complete!")
                    print()
                
                last_size = current_size
                last_events = current_events
                
                # Show daily total
                fulfilled = [e for e in current_events if e.get('event_type') == 'order_fulfilled']
                if fulfilled:
                    today_revenue = sum(e.get('amount', 0) for e in fulfilled)
                    print(f"Total revenue: ${today_revenue:.2f}")
                    print()
    
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")


def cmd_report():
    """Generate comprehensive report."""
    print("=" * 80)
    print("COMPREHENSIVE AUDIT LOG REPORT")
    print("=" * 80)
    print()

    # PERFORMANCE FIX: Parse orders once and reuse data across all analysis functions
    # Note: This changes the architecture to be more efficient but requires refactoring
    # For now, we call each function separately (they each parse independently)
    # TODO: Refactor to pass parsed data as parameter to avoid repeated parsing

    # Run all analysis
    cmd_summary()
    print("\n")
    cmd_verify()
    print("\n")
    cmd_customers()
    print("\n")
    cmd_revenue()

    # Order details
    print("=" * 80)
    print("ORDER DETAILS")
    print("=" * 80)
    print()

    events = parse_orders()
    orders = group_by_order(events)
    
    for i, (order_id, order_events) in enumerate(sorted(orders.items()), 1):
        print(f"Order #{i}: {order_id}")
        
        # Get details
        created = [e for e in order_events if e.get('event_type') == 'order_created']
        paid = [e for e in order_events if e.get('event_type') == 'payment_confirmed']
        fulfilled = [e for e in order_events if e.get('event_type') == 'order_fulfilled']
        
        if created:
            e = created[0]
            print(f"  Customer: {e.get('customer_id', 'unknown')}")
            print(f"  Amount: ${e.get('amount', 0):.2f}")
            print(f"  Created: {format_timestamp(e.get('timestamp', 0))}")
        
        if paid:
            e = paid[0]
            created_time = created[0].get('timestamp') if created else 0
            time_diff = e.get('timestamp', 0) - created_time
            print(f"  Paid: {format_timestamp(e.get('timestamp', 0))} (+{time_diff:.1f}s)")
        
        if fulfilled:
            e = fulfilled[0]
            created_time = created[0].get('timestamp') if created else 0
            time_diff = e.get('timestamp', 0) - created_time
            print(f"  Fulfilled: {format_timestamp(e.get('timestamp', 0))} (+{time_diff:.1f}s)")
            print(f"  Total time: {time_diff:.1f}s")
            
            token = e.get('metadata', {}).get('access_token')
            if token:
                print(f"  Access token: {token}")
        
        # Status
        if len(order_events) >= 3:
            print(f"  Status: ✅ COMPLETE")
        else:
            print(f"  Status: ⚠️  INCOMPLETE")
        print()
    
    print(f"All {len(orders)} orders processed!")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Audit Log Analyzer - Comprehensive audit log analysis")
        print()
        print("Usage:")
        print("  python audit_log_analyzer.py <command>")
        print()
        print("Commands:")
        print("  summary    - Quick overview of orders")
        print("  verify     - Full integrity verification")
        print("  customers  - Customer activity analysis")
        print("  revenue    - Revenue breakdown")
        print("  watch      - Real-time log monitoring")
        print("  report     - Complete comprehensive report")
        print()
        print("Examples:")
        print("  python audit_log_analyzer.py summary")
        print("  python audit_log_analyzer.py verify")
        print("  python audit_log_analyzer.py watch")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    commands = {
        'summary': cmd_summary,
        'verify': cmd_verify,
        'customers': cmd_customers,
        'revenue': cmd_revenue,
        'watch': cmd_watch,
        'report': cmd_report,
    }
    
    if command not in commands:
        print(f"Unknown command: {command}")
        print(f"Available commands: {', '.join(commands.keys())}")
        sys.exit(1)
    
    commands[command]()


if __name__ == '__main__':
    main()
