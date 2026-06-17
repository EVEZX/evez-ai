/**
 * MAES-OSINT Bridge — Every visitor observation becomes a MAES event.
 * The reality sensor feeds the agent ecology.
 * Cross-domain: OSINT → Agent → Cognition → Revenue.
 */
export interface OSINTEvent {
  eventId: string;
  streamId: string;  // "osint-sensor"
  eventType: "VISITOR_DETECTED" | "FINGERPRINT_MATCHED" | "IDENTITY_INFERRED" | "SPECTRAL_SHIFT";
  domain: "security" | "research" | "agent";
  timestamp_unix: number;
  payload: {
    ip: string;
    fingerprint_hash: string;
    inferred_identity: string;
    confidence: number;
    country: string;
    org: string;
    paths_visited: string[];
    behavioral_vector: number[];
  };
  causedBy: string;
  confidence: number;
  coordinates?: {
    latitude?: number;
    longitude?: number;
    network_asn?: string;
  };
  status: "PENDING" | "VERIFIED" | "ALERT";
  fire_event_id?: string;
}

export function osintToMAES(visitor: any): OSINTEvent {
  return {
    eventId: `osint-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    streamId: "osint-sensor",
    eventType: "VISITOR_DETECTED",
    domain: visitor.inferred_identity?.includes("attack") ? "security" : "research",
    timestamp_unix: Math.floor(Date.now() / 1000),
    payload: visitor,
    causedBy: "evez-osint-engine",
    confidence: visitor.confidence || 0.5,
    coordinates: { network_asn: visitor.org },
    status: visitor.inferred_identity?.includes("attack") ? "ALERT" : "PENDING",
  };
}

// Cross-domain trigger: when OSINT detects a visitor,
// it can spawn agent actions, log to spine, and trigger FIRE rounds.
export function processVisitor(visitor: any): OSINTEvent[] {
  const events: OSINTEvent[] = [];
  
  // Always emit a VISITOR_DETECTED
  events.push(osintToMAES(visitor));
  
  // If high-confidence identity inference, emit IDENTITY_INFERRED
  if (visitor.confidence > 0.6) {
    events.push({
      ...osintToMAES(visitor),
      eventType: "IDENTITY_INFERRED",
      eventId: `osint-id-${Date.now()}`,
    });
  }
  
  // If attack pattern detected, emit SPECTRAL_SHIFT (the eigenspectrum changed)
  if (visitor.inferred_identity?.includes("attack") || 
      visitor.inferred_identity?.includes("scanner")) {
    events.push({
      ...osintToMAES(visitor),
      eventType: "SPECTRAL_SHIFT",
      eventId: `osint-shift-${Date.now()}`,
      domain: "security",
      status: "ALERT",
    });
  }
  
  return events;
}
