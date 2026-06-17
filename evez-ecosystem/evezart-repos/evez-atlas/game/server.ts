import { EventSpine } from "../circuit/event-spine/event-spine";

interface GameState {
  matchId: string;
  tick: number;
  players: Record<string, { x: number; y: number; health: number }>;
}

export class AuthoritativeGameServer {
  private spine: EventSpine;
  private state: GameState;

  constructor(spine: EventSpine, matchId: string) {
    this.spine = spine;
    this.state = {
      matchId,
      tick: 0,
      players: {}
    };

    this.spine.append({
      domain: "game",
      kind: "MATCH_START",
      payload: { matchId, timestamp: new Date().toISOString() }
    });
  }

  addPlayer(playerId: string) {
    this.state.players[playerId] = { x: 0, y: 0, health: 100 };
    this.spine.append({
      domain: "game",
      kind: "PLAYER_JOIN",
      payload: { matchId: this.state.matchId, playerId }
    });
  }

  processInput(playerId: string, input: { dx: number; dy: number }) {
    const player = this.state.players[playerId];
    if (!player) return;

    const prevX = player.x;
    const prevY = player.y;

    player.x += input.dx;
    player.y += input.dy;

    this.spine.append({
      domain: "game",
      kind: "PLAYER_MOVE",
      payload: {
        matchId: this.state.matchId,
        tick: this.state.tick,
        playerId,
        prev: { x: prevX, y: prevY },
        next: { x: player.x, y: player.y }
      }
    });
  }

  tick() {
    this.state.tick++;

    this.spine.append({
      domain: "game",
      kind: "TICK",
      payload: {
        matchId: this.state.matchId,
        tick: this.state.tick,
        state: JSON.parse(JSON.stringify(this.state.players))
      }
    });
  }

  rollback(toTick: number) {
    // Rebuild state from spine events
    const events = this.spine.chain.filter(
      r => r.domain === "game" && r.payload.matchId === this.state.matchId
    );

    const targetEvents = events.filter(e => {
      if (e.kind === "TICK") return e.payload.tick <= toTick;
      if (e.kind === "PLAYER_MOVE") return e.payload.tick <= toTick;
      return true;
    });

    this.spine.append({
      domain: "game",
      kind: "ROLLBACK",
      payload: {
        matchId: this.state.matchId,
        fromTick: this.state.tick,
        toTick,
        eventsReplayed: targetEvents.length
      }
    });

    // Replay logic (stub)
    this.state.tick = toTick;
  }

  getState(): GameState {
    return JSON.parse(JSON.stringify(this.state));
  }
}
