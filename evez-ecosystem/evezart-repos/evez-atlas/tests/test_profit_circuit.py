"""
Tests for the complete profit circuit.

Tests the full revenue loop: Order → Payment → Fulfillment → Audit
"""

import json
import time
import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'api'))

from order_service import OrderService
from payment_service import PaymentService
from fulfillment_service import FulfillmentService


class TestProfitCircuit:
    """Test the complete profit circuit end-to-end."""
    
    @pytest.fixture
    def test_log_path(self, tmp_path):
        """Use temporary log file for tests."""
        return str(tmp_path / "test_orders.jsonl")
    
    @pytest.fixture
    def order_service(self, test_log_path):
        return OrderService(test_log_path)
    
    @pytest.fixture
    def payment_service(self, test_log_path):
        return PaymentService(test_log_path)
    
    @pytest.fixture
    def fulfillment_service(self, test_log_path):
        return FulfillmentService(test_log_path)
    
    def test_complete_circuit(self, order_service, payment_service, fulfillment_service):
        """Test complete order → payment → fulfillment → audit flow."""
        
        # 1. Create order
        order = order_service.create_order(
            customer_id="test_001",
            service_type="DATA_ANALYSIS_V1",
            amount=50.00,
            payment_method="sandbox",
            idempotency_key="test_001"
        )
        
        assert 'order_id' in order
        assert order['status'] == 'pending_payment'
        assert order['amount'] == 50.00
        
        # 2. Confirm payment
        payment = payment_service.confirm_payment(
            order_id=order['order_id'],
            sandbox=True
        )
        
        assert payment['success'] is True
        assert payment['status'] == 'paid'
        
        # 3. Fulfill order
        fulfillment = fulfillment_service.fulfill_order(order['order_id'])
        
        assert fulfillment['success'] is True
        assert fulfillment['status'] == 'fulfilled'
        assert 'analysis' in fulfillment['delivery']
        assert 'access_token' in fulfillment['delivery']
        
        # 4. Verify audit trail
        log_path = Path(order_service.orders_log)
        assert log_path.exists()
        
        events = []
        with open(log_path, 'r') as f:
            for line in f:
                event = json.loads(line)
                if event['order_id'] == order['order_id']:
                    events.append(event)
        
        assert len(events) == 3
        assert events[0]['event_type'] == 'order_created'
        assert events[1]['event_type'] == 'payment_confirmed'
        assert events[2]['event_type'] == 'order_fulfilled'
    
    def test_idempotency(self, order_service):
        """Test that duplicate orders with same idempotency key return same order."""
        
        order1 = order_service.create_order(
            customer_id="test_002",
            idempotency_key="idempotent_key_001"
        )
        
        order2 = order_service.create_order(
            customer_id="test_002",
            idempotency_key="idempotent_key_001"
        )
        
        assert order1['order_id'] == order2['order_id']
    
    def test_rate_limiting(self, order_service):
        """Test that rate limiting prevents abuse."""
        
        # Make 10 requests (should succeed)
        for i in range(10):
            result = order_service.create_order(
                customer_id=f"test_rate_{i}",
                customer_ip="192.168.1.1",
                idempotency_key=f"rate_test_{i}"
            )
            assert 'order_id' in result
        
        # 11th request should be rate limited
        result = order_service.create_order(
            customer_id="test_rate_11",
            customer_ip="192.168.1.1",
            idempotency_key="rate_test_11"
        )
        
        assert 'error' in result
        assert result['error'] == 'rate_limit_exceeded'
    
    def test_double_payment_prevention(self, order_service, payment_service):
        """Test that orders can't be paid twice."""
        
        order = order_service.create_order(
            customer_id="test_003",
            idempotency_key="double_pay_test"
        )
        
        # First payment succeeds
        payment1 = payment_service.confirm_payment(
            order_id=order['order_id'],
            sandbox=True
        )
        assert payment1['success'] is True
        
        # Second payment should fail
        payment2 = payment_service.confirm_payment(
            order_id=order['order_id'],
            sandbox=True
        )
        assert 'error' in payment2
        assert payment2['error'] == 'already_processed'
    
    def test_fulfillment_requires_payment(self, order_service, fulfillment_service):
        """Test that fulfillment requires payment first."""
        
        order = order_service.create_order(
            customer_id="test_004",
            idempotency_key="fulfill_test"
        )
        
        # Try to fulfill unpaid order
        result = fulfillment_service.fulfill_order(order['order_id'])
        
        assert 'error' in result
        assert result['error'] == 'order_not_paid'
    
    def test_invalid_amount(self, order_service):
        """Test that invalid amounts are rejected."""
        
        result = order_service.create_order(
            customer_id="test_005",
            amount=100.00  # Wrong amount
        )
        
        assert 'error' in result
        assert result['error'] == 'invalid_amount'
    
    def test_analysis_generation(self, fulfillment_service):
        """Test that analysis results are properly formatted."""
        
        # Create a dummy order in paid state
        order_service = OrderService(fulfillment_service.orders_log)
        payment_service = PaymentService(fulfillment_service.orders_log)
        
        order = order_service.create_order(
            customer_id="test_006",
            idempotency_key="analysis_test"
        )
        
        payment_service.confirm_payment(order['order_id'], sandbox=True)
        
        fulfillment = fulfillment_service.fulfill_order(order['order_id'])
        
        analysis = fulfillment['delivery']['analysis']
        assert 'summary' in analysis
        assert 'insights' in analysis
        assert 'recommendations' in analysis
        assert 'confidence_score' in analysis
        assert len(analysis['insights']) >= 3


def test_manual_profit_circuit():
    """Manual test that can be run directly."""
    print("\n" + "="*80)
    print("TESTING PROFIT CIRCUIT")
    print("="*80)
    
    order_service = OrderService("src/memory/orders.jsonl")
    payment_service = PaymentService("src/memory/orders.jsonl")
    fulfillment_service = FulfillmentService("src/memory/orders.jsonl")
    
    # Create unique order
    timestamp = int(time.time())
    order = order_service.create_order(
        customer_id=f"manual_test_{timestamp}",
        idempotency_key=f"manual_{timestamp}"
    )
    
    print(f"\n✓ Order created: {order['order_id']}")
    print(f"  Amount: ${order['amount']}")
    
    payment = payment_service.confirm_payment(order['order_id'], sandbox=True)
    print(f"\n✓ Payment confirmed: ${payment['amount']}")
    
    fulfillment = fulfillment_service.fulfill_order(order['order_id'])
    print(f"\n✓ Order fulfilled")
    print(f"  Access token: {fulfillment['delivery']['access_token']}")
    
    print("\n" + "="*80)
    print("✓ CIRCUIT COMPLETE")
    print("="*80)
    
    return True


if __name__ == "__main__":
    # Run manual test
    test_manual_profit_circuit()
