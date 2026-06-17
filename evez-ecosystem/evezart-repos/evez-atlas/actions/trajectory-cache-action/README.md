# Trajectory Cache Action

[![GitHub Marketplace](https://img.shields.io/badge/Marketplace-Trajectory%20Cache-orange.svg)](https://github.com/marketplace/actions/trajectory-cache-action)
[![License: ISC](https://img.shields.io/badge/License-ISC-blue.svg)](https://opensource.org/licenses/ISC)

Predictive state caching for instant responses with ring buffer management, trajectory sampling, and fast-forward playback capabilities.

## Features

- 🔄 **Ring Buffer Management** - Efficient circular buffer for state caching
- 📊 **Trajectory Sampling** - High-frequency state sampling
- ⏩ **Fast-Forward Playback** - Replay cached states at any speed
- 🔐 **Cache Invalidation** - Time-based, event-based, or hybrid policies
- ⚡ **Negative Latency** - Predictive caching for instant responses
- 📈 **Hit Rate Tracking** - Monitor cache performance

## Usage

### Basic Example

```yaml
name: Setup Trajectory Cache
on: [push]

jobs:
  cache-setup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Initialize Trajectory Cache
        uses: evezart/trajectory-cache-action@v1
        with:
          cache-size: 1000
          prediction-window: 60
```

### Advanced Example with Custom Configuration

```yaml
name: Advanced Trajectory Caching
on: [workflow_dispatch]

jobs:
  setup-cache:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Trajectory Cache
        id: cache
        uses: evezart/trajectory-cache-action@v1
        with:
          cache-size: 5000
          prediction-window: 120
          sampling-rate: 20
          invalidation-policy: hybrid
          enable-playback: true
      
      - name: Display Cache Info
        run: |
          echo "Cache ID: ${{ steps.cache.outputs.cache-id }}"
          echo "Cache Endpoint: ${{ steps.cache.outputs.cache-endpoint }}"
          echo "Hit Rate: ${{ steps.cache.outputs.hit-rate }}"
          echo "Buffer Status: ${{ steps.cache.outputs.buffer-status }}"
      
      - name: Upload Cache Artifacts
        uses: actions/upload-artifact@v4
        with:
          name: trajectory-cache
          path: trajectory-cache/
```

### Full Stack Integration

```yaml
name: Complete Cognitive Stack
on: [push]

jobs:
  deploy-stack:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      # Step 1: LORD Fusion
      - name: LORD Fusion Setup
        id: lord
        uses: evezart/lord-fusion-action@v1
        with:
          recursion-level: 15
          entity-type: hybrid
          deploy-target: artifact
      
      # Step 2: Cognitive Engine
      - name: Cognitive Engine Bootstrap
        id: engine
        uses: evezart/cognitive-engine-bootstrap@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          hosting-provider: vercel
      
      # Step 3: Trajectory Cache
      - name: Trajectory Cache Setup
        id: cache
        uses: evezart/trajectory-cache-action@v1
        with:
          cache-size: 2000
          prediction-window: 90
          sampling-rate: 15
          invalidation-policy: hybrid
          enable-playback: true
      
      # Verify integration
      - name: Stack Verification
        run: |
          echo "=== Cognitive Stack Deployed ==="
          echo "LORD Dashboard: ${{ steps.lord.outputs.dashboard-url }}"
          echo "Cognitive Daemon: ${{ steps.engine.outputs.daemon-endpoint }}"
          echo "Cache Endpoint: ${{ steps.cache.outputs.cache-endpoint }}"
          echo "Cache Hit Rate: ${{ steps.cache.outputs.hit-rate }}"
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `cache-size` | Ring buffer size for state caching (10-10000) | Yes | `1000` |
| `prediction-window` | Prediction window in seconds (1-3600) | Yes | `60` |
| `sampling-rate` | Trajectory sampling rate (samples per second) | No | `10` |
| `invalidation-policy` | Cache invalidation policy: `time-based`, `event-based`, `hybrid` | No | `hybrid` |
| `enable-playback` | Enable fast-forward playback | No | `true` |

## Outputs

| Output | Description |
|--------|-------------|
| `cache-id` | Unique cache identifier |
| `cache-endpoint` | Cache access endpoint |
| `hit-rate` | Initial cache hit rate (0.00-1.00) |
| `buffer-status` | Ring buffer initialization status |

## How It Works

### 1. Ring Buffer Architecture

The action implements a circular buffer that efficiently manages state caching:

```
┌─────────────────────────────────┐
│      Ring Buffer (Size: N)      │
├─────────────────────────────────┤
│  [0] → [1] → [2] → ... → [N-1] │
│   ↑                        ↓    │
│   └────────────────────────┘    │
│      (Wraps around)             │
└─────────────────────────────────┘
```

### 2. Trajectory Sampling

Samples future states at specified rate:
- **Sampling Rate**: 10 samples/second (default)
- **Prediction Window**: 60 seconds (default)
- **Total Samples**: 600 states cached

### 3. Cache Invalidation

Three invalidation strategies:

**Time-Based**:
- Invalidate after prediction window expires
- Auto-refresh on time boundary

**Event-Based**:
- Invalidate on state change events
- Invalidate on workflow completion

**Hybrid** (Recommended):
- Combine time-based and event-based
- Invalidate on timeout OR state change

### 4. Fast-Forward Playback

Replay cached states with controls:
- Play all states sequentially
- Skip to specific timestamp
- Adjust playback speed
- Reverse playback

## Cache Performance

### Hit Rate Expectations

- **Initial**: 75-90%
- **Warmed Up**: 85-95%
- **Optimal**: 90-95%

### Factors Affecting Performance

- **Cache Size**: Larger = better hit rate
- **Prediction Window**: Longer = more coverage
- **Sampling Rate**: Higher = finer granularity
- **Invalidation Policy**: Hybrid usually performs best

## Artifacts Generated

The action generates the following files:

```
trajectory-cache/
├── ring-buffer.json          # Ring buffer state
├── trajectory-states.json    # Sampled trajectory states
├── invalidation-policy.json  # Invalidation configuration
└── playback.sh              # Fast-forward playback script
```

## Pricing

Standard GitHub Actions pricing applies:

- **Public Repositories**: Free
- **Private Repositories**: 
  - $0.008/minute for Linux runners
  - ~$0.01 per setup
  - Average run time: <1 minute

## Real-World Use Cases

### 1. CI/CD Optimization
Cache build states to predict failures before they occur.

### 2. Workflow Prediction
Anticipate workflow outcomes based on historical patterns.

### 3. State Playback
Replay past states for debugging and analysis.

### 4. Performance Testing
Test system behavior under various prediction scenarios.

## Examples from Production

See our main repository for production examples:
- [Evez666 Repository](https://github.com/EvezArt/Evez666)
- [Quantum Evolution Demo](https://github.com/EvezArt/Evez666/blob/main/scripts/demo_quantum_evolution.py)

## API Reference

### Cache Endpoint

```
GET /cache/{cache-id}/state/{index}
GET /cache/{cache-id}/trajectory
POST /cache/{cache-id}/invalidate
```

### Playback Script

```bash
# Run playback
./trajectory-cache/playback.sh

# Play all states
./trajectory-cache/playback.sh play-all

# Skip to timestamp
./trajectory-cache/playback.sh skip-to 2024-02-14T12:00:00Z
```

## Troubleshooting

### Cache Size Too Small

Increase `cache-size` to improve hit rate.

### Low Hit Rate

- Increase `prediction-window`
- Increase `sampling-rate`
- Consider `hybrid` invalidation policy

### Memory Issues

Reduce `cache-size` or `sampling-rate`.

## Support

- **Issues**: [GitHub Issues](https://github.com/EvezArt/trajectory-cache-action/issues)
- **Documentation**: [Full Documentation](https://github.com/EvezArt/trajectory-cache-action/wiki)
- **Community**: [Discussions](https://github.com/EvezArt/trajectory-cache-action/discussions)

## License

ISC © EvezArt

## Related Actions

- [LORD Fusion Setup](https://github.com/marketplace/actions/lord-fusion-setup)
- [Cognitive Engine Bootstrap](https://github.com/marketplace/actions/cognitive-engine-bootstrap)

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

**Note**: This action implements predictive caching algorithms. All "trajectory" and "prediction" terminology refers to computational state forecasting based on historical patterns, not actual future prediction.
