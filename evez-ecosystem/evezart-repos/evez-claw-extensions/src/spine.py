"""
Spine: Immutable hash-chained event log
Ground truth for all state changes
"""

import hashlib
import json
import time

class Spine:
    """Append-only cryptographically-chained event log."""
    
    def __init__(self):
        self.events = []
        self.genesis_time = time.time()
        self.genesis_hash = self._hash("")
    
    def log(self, event_type, data):
        """Append event to spine."""
        predecessor = self.events[-1]["hash"] if self.events else self.genesis_hash
        
        event = {
            "index": len(self.events),
            "timestamp": time.time(),
            "type": event_type,
            "data": data,
            "predecessor": predecessor
        }
        
        event["hash"] = self._hash(json.dumps(event, sort_keys=True))
        self.events.append(event)
        return event["hash"]
    
    def _hash(self, data):
        """SHA-256 hash."""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def verify_chain(self):
        """Verify cryptographic integrity."""
        for i, event in enumerate(self.events):
            event_copy = {k: v for k, v in event.items() if k != "hash"}
            computed = self._hash(json.dumps(event_copy, sort_keys=True))
            
            if computed != event["hash"]:
                return False, f"Hash mismatch at index {i}"
            
            if i > 0 and event["predecessor"] != self.events[i-1]["hash"]:
                return False, f"Chain break at index {i}"
        
        return True, "Chain intact"
    
    def get_events_by_type(self, event_type):
        """Filter events by type."""
        return [e for e in self.events if e["type"] == event_type]
    
    def export(self, filename):
        """Export to JSON file."""
        with open(filename, 'w') as f:
            json.dump(self.events, f, indent=2)


if __name__ == "__main__":
    print("Testing spine integrity...")
    spine = Spine()
    
    # Log events
    for i in range(100):
        spine.log("test_event", {"value": i, "square": i**2})
    
    # Verify
    valid, msg = spine.verify_chain()
    print(f"Chain verification: {msg}")
    
    # Try to tamper
    if spine.events:
        spine.events[50]["data"]["value"] = 999
        valid, msg = spine.verify_chain()
        print(f"After tampering: {msg}")
    
    print(f"\n✓ Logged {len(spine.events)} events")
