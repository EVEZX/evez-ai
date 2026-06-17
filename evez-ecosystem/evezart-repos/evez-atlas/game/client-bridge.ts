/**
 * Client-side prediction + rollback bridge
 * 
 * Client predicts moves optimistically, server finalizes, client rolls back if mismatch.
 */

export interface PredictedMove {
  tick: number;
  playerId: string;
  dx: number;
  dy: number;
  status: "pending" | "confirmed" | "rejected";
}

export class ClientBridge {
  private predictions: PredictedMove[] = [];

  predict(tick: number, playerId: string, dx: number, dy: number) {
    this.predictions.push({
      tick,
      playerId,
      dx,
      dy,
      status: "pending"
    });
  }

  reconcile(serverTick: number, serverState: any) {
    // Mark predictions as confirmed or rejected
    for (const pred of this.predictions) {
      if (pred.tick <= serverTick) {
        // Check if server state matches prediction (stub)
        pred.status = "confirmed"; // or "rejected"
      }
    }

    // Remove old predictions
    this.predictions = this.predictions.filter(p => p.status === "pending");
  }

  getPendingPredictions(): PredictedMove[] {
    return this.predictions.filter(p => p.status === "pending");
  }
}
