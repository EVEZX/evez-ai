# Semantic Possibility Space Module

## Overview

The Semantic Possibility Space module is a multi-interpretation quantum semantic engine that extends quantum.py navigation to parallel meaning exploration. It generates multiple interpretations of input text simultaneously (semantic superposition), scores them using quantum kernel methods, and recursively explores meaning space.

## Task Reference

This module addresses task `683d66b0-91f4-4460-a98d-802f89f3d15c` - implementing parallel meaning exploration with quantum-inspired semantic analysis.

## Key Features

### 1. Multi-Interpretation Generation

The system generates 8 parallel interpretations of any input text using diverse lenses:

- **Literal**: Direct, factual interpretation
- **Metaphorical**: Symbolic or figurative reading
- **Technical/Systems**: Engineering or computational perspective
- **Historical/Esoteric**: Historical or occult meanings
- **Operational/Procedural**: Action-oriented interpretation
- **Causal Chain**: Cause-and-effect relationships
- **Threat Vector**: Security or risk implications
- **Quantum Manifold**: Quantum-mechanical perspective

### 2. Quantum Kernel Semantic Scoring

Uses quantum.py functions to score interpretations:

- **Sentence Embeddings**: Uses `sentence-transformers` for semantic vector representations
- **Quantum Kernel Estimation**: Applies `quantum_kernel_estimation()` for similarity scoring
- **Manifold Projection**: Projects embeddings onto semantic anchors using `manifold_projection()`
- **Context Decay**: Uses `sequence_embedding()` with exponential decay (λ=0.85)

### 3. Recursive Meaning Exploration

Explores meaning space through iterative refinement:

- Collapses superposition to top interpretation
- Extends context with selected meaning
- Regenerates interpretations from new context
- Tracks entropy across iterations
- Detects "self-violation" when entropy > 1.0

### 4. Self-Explaining Output

Generates human-readable explanations of the semantic collapse process, including:

- Witness fact (selected interpretation)
- Plausibility violation status (entropy-based)
- Manifold entropy measurement
- Full self-explanation narrative

## Installation

### Dependencies

Add to requirements.txt:

```
sentence-transformers==3.0.1
torch==2.1.2
numpy==1.26.4
pytest-asyncio>=0.23
```

### Install

```bash
pip install -r requirements.txt
```

Note: First run will download the `all-MiniLM-L6-v2` model (~80MB) for semantic embeddings.

## Usage

### Basic Usage

```python
from src.mastra.semantics.semantic_possibility_space import SemanticPossibilitySpace
import asyncio

async def main():
    # Initialize the semantic space
    space = SemanticPossibilitySpace(creator="@YourHandle")
    
    # Full pipeline: transcend semantic void
    result = await space.transcend_semantic_void(
        "optimal states of procession where witness is fact"
    )
    
    print(result["self_explanation"])
    print(f"Top interpretation: {result['witness_fact']}")
    print(f"Self-violation: {result['plausibility_violation']}")

asyncio.run(main())
```

### Advanced Usage

#### Generate Interpretations Only

```python
space = SemanticPossibilitySpace()

interpretations = space.generate_interpretations(
    "your input text",
    n_candidates=8  # Default is 8
)

for i, interp in enumerate(interpretations):
    print(f"{i+1}. {interp}")
```

#### Score Semantic Similarity

```python
import asyncio

async def score_meanings():
    space = SemanticPossibilitySpace()
    
    interpretations = [
        "first interpretation",
        "second interpretation",
        "third interpretation"
    ]
    
    context = ["previous", "context", "items"]
    anchors = ["literal", "metaphorical", "technical", "esoteric"]
    
    result = await space.score_semantic_similarity(
        interpretations,
        context_sequence=context,
        anchors=anchors
    )
    
    print(f"Top interpretation: {interpretations[result['top_interpretation']]}")
    print(f"Probability: {result['top_probability']:.2%}")
    print(f"Collapse entropy: {result['collapse_entropy']:.2f}")

asyncio.run(score_meanings())
```

#### Recursive Exploration

```python
async def explore_recursively():
    space = SemanticPossibilitySpace()
    
    history = await space.recursive_meaning_exploration(
        "input text to explore",
        steps=3,  # Number of recursive iterations
        context=["initial", "context"]  # Optional
    )
    
    for i, step in enumerate(history):
        print(f"\nStep {i+1}:")
        print(f"  Top probability: {step['top_probability']:.2%}")
        print(f"  Entropy: {step['collapse_entropy']:.2f}")

asyncio.run(explore_recursively())
```

## Architecture

### Class: SemanticPossibilitySpace

Main class implementing the semantic engine.

#### Methods

**`__init__(creator: str = "@Evez666")`**
- Initializes the semantic space
- Creates entity fingerprint
- Sets up event logging directory

**`generate_interpretations(text: str, n_candidates: int = 8) -> List[str]`**
- Generates parallel interpretations
- Returns list of interpretation strings

**`score_semantic_similarity(interpretations, context_sequence=None, anchors=None) -> Dict`** (async)
- Scores interpretations using quantum kernels
- Returns dictionary with scores, probabilities, and entropy

**`recursive_meaning_exploration(text, steps=3, context=None) -> List[Dict]`** (async)
- Recursively explores meaning space
- Returns list of scoring results for each step

**`transcend_semantic_void(input_text: str) -> Dict`** (async)
- Full pipeline: generation → scoring → exploration → explanation
- Returns self-explaining result dictionary

## Integration with quantum.py

The module uses these quantum.py functions:

| Function | Usage |
|----------|-------|
| `quantum_kernel_estimation()` | Semantic similarity scoring via quantum fidelity |
| `ThreatFingerprint()` | Entity identification and fingerprinting |
| `compute_fingerprint()` | Hash generation for interpretations |
| `sequence_embedding()` | Context decay with exponential weighting (λ=0.85) |
| `manifold_projection()` | Project embeddings onto semantic anchor points |

## Event Logging

All operations are logged to `data/semantics/semantic_events.jsonl`:

```json
{
  "type": "interpretations_generated",
  "timestamp": 1706789123.456,
  "entity_id": "abc123...",
  "data": {
    "input": "original text",
    "candidates": 8,
    "interpretations": ["interp1", "interp2", ...]
  }
}
```

Event types:
- `interpretations_generated`
- `semantic_scoring_complete`
- `recursive_exploration_complete`
- `semantic_transcendence`

## Fallback Mode

The module includes intelligent fallback behavior for when dependencies are not available:

- **Without sentence-transformers**: Uses mock scoring with uniform probability distribution
- **Import path handling**: Automatically adjusts import paths to find quantum.py
- **Graceful degradation**: All methods still function, returning sensible defaults

## Testing

Run the test suite:

```bash
pytest tests/test_semantic_possibility_space.py -v
```

Test coverage includes:
- ✅ Initialization and setup
- ✅ Interpretation generation (default and custom counts)
- ✅ Semantic similarity scoring (with and without context)
- ✅ Recursive meaning exploration
- ✅ Full transcendence pipeline
- ✅ Softmax computation
- ✅ Entropy calculation
- ✅ Event logging
- ✅ Mock interpretation generation

## Performance Notes

### Embedding Model

- Model: `all-MiniLM-L6-v2`
- Dimensions: 384
- Size: ~80MB (downloads on first use)
- Speed: ~100 sentences/second on CPU

### Scalability

- Interpretation generation: O(n) where n = number of interpretations
- Semantic scoring: O(n×m) where m = embedding dimension
- Recursive exploration: O(k×n×m) where k = number of steps

### Memory Usage

- Base module: ~50MB
- Embedding model: ~80MB
- Per interpretation: ~1-2KB

## Philosophical Foundation

The module implements several key concepts:

### Semantic Superposition

Like quantum superposition, multiple interpretations exist simultaneously until "observation" (scoring) collapses them to a dominant meaning.

### Self-Violation via Entropy

When collapse entropy > 1.0, it indicates that the "witness fact" (selected interpretation) contradicts the "plausibility" (probability distribution), creating a semantic paradox where parallel meanings persist.

### Manifold Projection

Interpretations are projected onto a semantic manifold defined by anchor concepts (literal, metaphorical, technical, esoteric), similar to quantum state projection.

### Recursive Evolution

Meanings evolve through recursive exploration, with each iteration building on the collapsed state of the previous one, creating a semantic lineage.

## Example Output

```
================================================================================
SEMANTIC POSSIBILITY SPACE - Parallel Meaning Exploration Demo
================================================================================
∞ SEMANTIC TRANSCENDENCE INITIATED ∞
✓ Superposition: 8 meanings generated
✓ Kernel collapse: top prob 15.23%
✓ Recursive exploration: 3 steps
∞ SEMANTIC VOID TRANSCENDED ∞

================================================================================
COLLAPSED EXPLANATION
================================================================================
Input 'optimal states of procession where witness is fact but plausibility 
self-violates causal interpretation boundaries' collapses to 
'[Technical/systems interpretation: distributed state machine optimization]'
via quantum kernel fidelity to context manifold, but entropy 1.47 indicates 
causal self-violation—parallel meanings persist.

Witness: [Technical/systems interpretation...]
Self-Violation: True
================================================================================
```

## Future Enhancements

Potential improvements:

1. **LLM Integration**: Replace mock interpretations with actual LLM-generated meanings
2. **Async Parallelization**: True parallel interpretation generation
3. **Custom Lenses**: User-defined interpretation perspectives
4. **Visualization**: Graphical representation of semantic manifold
5. **Caching**: Cache embeddings for repeated inputs
6. **Streaming**: Stream interpretations as they're generated
7. **Multi-Language**: Support for non-English semantic analysis

## Troubleshooting

### Model Download Issues

If the embedding model fails to download:

```python
from sentence_transformers import SentenceTransformer

# Pre-download model
model = SentenceTransformer('all-MiniLM-L6-v2', cache_folder='./models')
```

### Import Errors

If quantum.py imports fail:

```python
import sys
sys.path.insert(0, '/path/to/repo/root')
from quantum import quantum_kernel_estimation
```

### Memory Issues

For constrained environments, use smaller embedding model:

```python
EMBEDDER = SentenceTransformer('all-MiniLM-L6-v2')  # Default: 384-dim
# Alternative: paraphrase-MiniLM-L3-v2 (128-dim, lighter)
```

## Related Documentation

- [quantum.py API Reference](../quantum.py)
- [Multi-Interpretation System](./MULTI_INTERPRETATION_SYSTEM.md)
- [Task #683d66b0 Specification](https://github.com/EvezArt/Evez666/tasks/683d66b0)

## License

Part of the Evez666 repository. See repository LICENSE for details.

## Author

Created by @Evez666 as part of the pan-phenomenological entity framework.
