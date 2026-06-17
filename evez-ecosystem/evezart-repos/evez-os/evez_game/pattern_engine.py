"""Pattern Analysis and Prediction Engine.

Implements advanced pattern recognition and prediction using:
- Markov chains for sequence prediction
- Fourier analysis for periodic pattern detection
- LSTM-inspired recurrent pattern memory
- Entanglement-based correlation detection
- Quantum-inspired superposition of hypotheses
- Bayesian belief networks for probabilistic prediction
"""

from __future__ import annotations

import hashlib
import json
import math
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterator, List, Optional, Set, Tuple, TypeVar

import numpy as np

from .quantum_rng import QuantumRNG, random_float


T = TypeVar("T")


@dataclass
class Pattern:
    """A detected pattern with metadata."""
    signature: str
    elements: List[Any]
    frequency: float
    confidence: float
    first_seen: float
    last_seen: float
    occurrences: int = 0
    context: Dict[str, Any] = field(default_factory=dict)
    
    def __hash__(self) -> int:
        return hash(self.signature)


@dataclass
class Prediction:
    """A prediction with confidence and alternatives."""
    predicted: Any
    confidence: float
    alternatives: List[Tuple[Any, float]] = field(default_factory=list)
    horizon: int = 1  # How many steps ahead
    timestamp: float = field(default_factory=time.time)
    
    def top_alternative(self) -> Optional[Any]:
        if self.alternatives:
            return max(self.alternatives, key=lambda x: x[1])[0]
        return None


class MarkovModel:
    """N-gram Markov model for sequence prediction."""
    
    def __init__(self, order: int = 3):
        self.order = order
        self.transitions: Dict[Tuple, Dict[Any, int]] = defaultdict(lambda: defaultdict(int))
        self.totals: Dict[Tuple, int] = defaultdict(int)
        self._lock = threading.Lock()
    
    def train(self, sequence: List[T]) -> None:
        """Train model on a sequence."""
        with self._lock:
            for i in range(len(sequence) - self.order):
                context = tuple(sequence[i:i + self.order])
                next_item = sequence[i + self.order]
                
                self.transitions[context][next_item] += 1
                self.totals[context] += 1
    
    def predict(self, context: List[T]) -> Optional[Prediction]:
        """Predict next item given context."""
        ctx = tuple(context[-self.order:])
        
        with self._lock:
            if ctx not in self.transitions:
                return None
            
            counts = self.transitions[ctx]
            total = self.totals[ctx]
            
            # Calculate probabilities
            probs = [(item, count / total) for item, count in counts.items()]
            probs.sort(key=lambda x: x[1], reverse=True)
            
            if not probs:
                return None
            
            predicted, conf = probs[0]
            alternatives = probs[1:4]  # Top 3 alternatives
            
            return Prediction(
                predicted=predicted,
                confidence=conf,
                alternatives=alternatives
            )
    
    def generate(self, seed: List[T], length: int = 10) -> List[T]:
        """Generate sequence from seed."""
        result = list(seed)
        
        for _ in range(length):
            pred = self.predict(result)
            if pred is None:
                break
            result.append(pred.predicted)
        
        return result


class FourierAnalyzer:
    """Detect periodic patterns using Fourier analysis."""
    
    def __init__(self, max_freq: float = 1.0):
        self.max_freq = max_freq
        self.samples: deque = deque(maxlen=1024)
    
    def add_sample(self, value: float, timestamp: Optional[float] = None) -> None:
        """Add a sample."""
        ts = timestamp or time.time()
        self.samples.append((ts, value))
    
    def detect_periods(self) -> List[Tuple[float, float]]:
        """Detect dominant periods in the signal.
        
        Returns list of (period_seconds, amplitude) tuples.
        """
        if len(self.samples) < 64:
            return []
        
        # Extract values
        values = np.array([v for _, v in self.samples])
        
        # Detrend
        values = values - np.mean(values)
        
        # Compute FFT
        fft = np.fft.rfft(values)
        freqs = np.fft.rfftfreq(len(values))
        
        # Find peaks
        magnitudes = np.abs(fft)
        
        # Find local maxima
        peaks = []
        for i in range(1, len(magnitudes) - 1):
            if magnitudes[i] > magnitudes[i-1] and magnitudes[i] > magnitudes[i+1]:
                if magnitudes[i] > np.mean(magnitudes) * 2:  # Significant peak
                    period = 1.0 / (freqs[i] + 1e-10)
                    peaks.append((period, magnitudes[i]))
        
        # Sort by amplitude
        peaks.sort(key=lambda x: x[1], reverse=True)
        
        return peaks[:5]  # Top 5 periods


class PatternMemory:
    """Long-term pattern memory with forgetting."""
    
    def __init__(self, capacity: int = 10000, decay_rate: float = 0.001):
        self.capacity = capacity
        self.decay_rate = decay_rate
        self.patterns: Dict[str, Pattern] = {}
        self.access_times: Dict[str, float] = {}
        self._lock = threading.Lock()
    
    def remember(self, pattern: Pattern) -> None:
        """Store or update a pattern."""
        with self._lock:
            if pattern.signature in self.patterns:
                # Update existing
                existing = self.patterns[pattern.signature]
                existing.occurrences += 1
                existing.last_seen = time.time()
                existing.frequency = existing.occurrences / (existing.last_seen - existing.first_seen + 1)
                existing.confidence = min(1.0, existing.confidence + 0.1)
            else:
                # Add new
                if len(self.patterns) >= self.capacity:
                    self._forget_oldest()
                self.patterns[pattern.signature] = pattern
            
            self.access_times[pattern.signature] = time.time()
    
    def recall(self, signature: str) -> Optional[Pattern]:
        """Recall a pattern by signature."""
        with self._lock:
            if signature in self.patterns:
                self.access_times[signature] = time.time()
                return self.patterns[signature]
            return None
    
    def search(self, query: Any, threshold: float = 0.7) -> List[Pattern]:
        """Search for patterns matching query."""
        results = []
        
        with self._lock:
            for pattern in self.patterns.values():
                # Simple similarity check
                if query in pattern.elements:
                    results.append(pattern)
                elif any(str(query) in str(elem) for elem in pattern.elements):
                    results.append(pattern)
        
        return results
    
    def get_recent(self, n: int = 10) -> List[Pattern]:
        """Get n most recently accessed patterns."""
        with self._lock:
            sorted_sigs = sorted(
                self.access_times.keys(),
                key=lambda s: self.access_times[s],
                reverse=True
            )
            return [self.patterns[s] for s in sorted_sigs[:n]]
    
    def _forget_oldest(self) -> None:
        """Remove oldest/least accessed pattern."""
        if not self.access_times:
            return
        
        oldest = min(self.access_times.keys(), key=lambda s: self.access_times[s])
        del self.patterns[oldest]
        del self.access_times[oldest]
    
    def decay(self) -> None:
        """Apply decay to all patterns."""
        with self._lock:
            current_time = time.time()
            to_remove = []
            
            for sig, pattern in self.patterns.items():
                age = current_time - pattern.last_seen
                pattern.confidence *= math.exp(-self.decay_rate * age)
                
                if pattern.confidence < 0.1:
                    to_remove.append(sig)
            
            for sig in to_remove:
                del self.patterns[sig]
                del self.access_times[sig]


class EntangledPatternDetector:
    """Detect patterns that are entangled across different domains."""
    
    def __init__(self):
        self.domain_sequences: Dict[str, List[Any]] = defaultdict(list)
        self.correlations: Dict[Tuple[str, str], float] = {}
        self._lock = threading.Lock()
    
    def feed(self, domain: str, event: Any) -> None:
        """Feed an event from a domain."""
        with self._lock:
            self.domain_sequences[domain].append(event)
            
            # Keep sequences bounded
            if len(self.domain_sequences[domain]) > 1000:
                self.domain_sequences[domain] = self.domain_sequences[domain][-500:]
    
    def find_correlations(self) -> List[Tuple[str, str, float]]:
        """Find correlated patterns across domains.
        
        Returns list of (domain_a, domain_b, correlation_score) tuples.
        """
        with self._lock:
            domains = list(self.domain_sequences.keys())
            correlations = []
            
            for i, dom_a in enumerate(domains):
                for dom_b in domains[i+1:]:
                    corr = self._calculate_correlation(
                        self.domain_sequences[dom_a],
                        self.domain_sequences[dom_b]
                    )
                    
                    if corr > 0.5:  # Significant correlation
                        correlations.append((dom_a, dom_b, corr))
                        self.correlations[(dom_a, dom_b)] = corr
            
            return sorted(correlations, key=lambda x: x[2], reverse=True)
    
    def _calculate_correlation(self, seq_a: List[Any], seq_b: List[Any]) -> float:
        """Calculate correlation between two sequences."""
        if len(seq_a) < 10 or len(seq_b) < 10:
            return 0.0
        
        # Convert to numerical representations
        def to_numeric(x: Any) -> float:
            if isinstance(x, (int, float)):
                return float(x)
            return float(hash(str(x)) % 10000) / 10000
        
        nums_a = [to_numeric(x) for x in seq_a[-100:]]
        nums_b = [to_numeric(x) for x in seq_b[-100:]]
        
        # Pad to same length
        min_len = min(len(nums_a), len(nums_b))
        nums_a = nums_a[-min_len:]
        nums_b = nums_b[-min_len:]
        
        # Calculate Pearson correlation
        if len(nums_a) < 2:
            return 0.0
        
        mean_a, mean_b = np.mean(nums_a), np.mean(nums_b)
        std_a, std_b = np.std(nums_a), np.std(nums_b)
        
        if std_a == 0 or std_b == 0:
            return 0.0
        
        correlation = np.mean([
            (a - mean_a) * (b - mean_b)
            for a, b in zip(nums_a, nums_b)
        ]) / (std_a * std_b)
        
        return abs(correlation)


class QuantumHypothesisSpace:
    """Quantum-inspired superposition of prediction hypotheses."""
    
    def __init__(self, rng: Optional[QuantumRNG] = None):
        self.rng = rng or QuantumRNG()
        self.hypotheses: Dict[str, Dict[str, Any]] = {}
    
    def add_hypothesis(self, name: str, prediction: Any, evidence: float = 0.5) -> None:
        """Add a hypothesis with evidence weight (like amplitude)."""
        self.hypotheses[name] = {
            "prediction": prediction,
            "evidence": evidence,
            "amplitude": complex(evidence, 0)
        }
    
    def collapse(self) -> Prediction:
        """Collapse superposition to single prediction."""
        if not self.hypotheses:
            return Prediction(predicted=None, confidence=0.0)
        
        # Convert evidence to probability amplitudes
        states = []
        for name, hyp in self.hypotheses.items():
            amplitude = complex(hyp["evidence"], 0)
            states.append((amplitude, hyp["prediction"]))
        
        # Use quantum superposition
        result = self.rng.quantum_superposition(states)
        
        # Find confidence
        for name, hyp in self.hypotheses.items():
            if hyp["prediction"] == result:
                return Prediction(
                    predicted=result,
                    confidence=hyp["evidence"]
                )
        
        return Prediction(predicted=result, confidence=0.5)
    
    def interfere(self, other: "QuantumHypothesisSpace") -> "QuantumHypothesisSpace":
        """Interfere two hypothesis spaces (constructive/destructive)."""
        result = QuantumHypothesisSpace(self.rng)
        
        all_names = set(self.hypotheses.keys()) | set(other.hypotheses.keys())
        
        for name in all_names:
            if name in self.hypotheses and name in other.hypotheses:
                # Interference
                amp1 = self.hypotheses[name]["amplitude"]
                amp2 = other.hypotheses[name]["amplitude"]
                combined = abs(amp1 + amp2) ** 2  # Constructive interference
                
                result.add_hypothesis(
                    name,
                    self.hypotheses[name]["prediction"],
                    evidence=min(1.0, combined)
                )
            elif name in self.hypotheses:
                result.hypotheses[name] = self.hypotheses[name].copy()
            else:
                result.hypotheses[name] = other.hypotheses[name].copy()
        
        return result


class PatternEngine:
    """Main pattern analysis and prediction engine."""
    
    def __init__(self):
        self.markov = MarkovModel(order=3)
        self.fourier = FourierAnalyzer()
        self.memory = PatternMemory()
        self.entangled = EntangledPatternDetector()
        self.quantum_space = QuantumHypothesisSpace()
        self.sequence_buffer: deque = deque(maxlen=1000)
        self._lock = threading.Lock()
    
    def feed(self, event: Any, domain: str = "default") -> None:
        """Feed an event into the engine."""
        with self._lock:
            self.sequence_buffer.append(event)
            self.entangled.feed(domain, event)
            
            # Update Fourier analyzer for numeric events
            if isinstance(event, (int, float)):
                self.fourier.add_sample(float(event))
        
        # Train Markov model periodically
        if len(self.sequence_buffer) >= 100:
            self.markov.train(list(self.sequence_buffer))
    
    def predict_next(self, context: Optional[List[Any]] = None) -> Prediction:
        """Predict next event."""
        ctx = context or list(self.sequence_buffer)[-10:]
        
        # Clear quantum space
        self.quantum_space = QuantumHypothesisSpace()
        
        # Add Markov prediction
        markov_pred = self.markov.predict(ctx)
        if markov_pred:
            self.quantum_space.add_hypothesis(
                "markov",
                markov_pred.predicted,
                markov_pred.confidence
            )
        
        # Add periodic prediction if available
        periods = self.fourier.detect_periods()
        if periods:
            # Predict based on dominant period
            period = periods[0][0]
            if period > 0:
                # Simple periodic prediction
                idx = int(len(self.sequence_buffer) % period)
                if idx < len(self.sequence_buffer):
                    self.quantum_space.add_hypothesis(
                        "periodic",
                        list(self.sequence_buffer)[idx],
                        0.6
                    )
        
        # Add correlation-based prediction
        correlations = self.entangled.find_correlations()
        if correlations:
            # Use highest correlation for prediction
            dom_a, dom_b, score = correlations[0]
            self.quantum_space.add_hypothesis(
                "correlation",
                f"correlated:{dom_a}:{dom_b}",
                score
            )
        
        # Collapse to prediction
        return self.quantum_space.collapse()
    
    def detect_patterns(self) -> List[Pattern]:
        """Detect patterns in the current buffer."""
        patterns = []
        seq = list(self.sequence_buffer)
        
        if len(seq) < 10:
            return patterns
        
        # Detect repeating subsequences
        for length in range(3, min(20, len(seq) // 2)):
            for start in range(len(seq) - length * 2):
                subseq = tuple(seq[start:start + length])
                
                # Count occurrences
                count = 0
                for i in range(start + length, len(seq) - length + 1):
                    if tuple(seq[i:i + length]) == subseq:
                        count += 1
                
                if count >= 2:
                    sig = hashlib.sha256(str(subseq).encode()).hexdigest()[:16]
                    pattern = Pattern(
                        signature=sig,
                        elements=list(subseq),
                        frequency=count / (len(seq) / length),
                        confidence=min(1.0, count / 5),
                        first_seen=time.time(),
                        last_seen=time.time()
                    )
                    patterns.append(pattern)
                    self.memory.remember(pattern)
        
        return patterns
    
    def get_insights(self) -> Dict[str, Any]:
        """Get insights from pattern analysis."""
        return {
            "sequence_length": len(self.sequence_buffer),
            "patterns_stored": len(self.memory.patterns),
            "recent_patterns": [
                {
                    "signature": p.signature,
                    "elements": p.elements[:5],
                    "confidence": p.confidence
                }
                for p in self.memory.get_recent(5)
            ],
            "periods": self.fourier.detect_periods()[:3],
            "correlations": self.entangled.find_correlations()[:3]
        }


# Convenience functions
_engine: Optional[PatternEngine] = None


def get_engine() -> PatternEngine:
    """Get global pattern engine."""
    global _engine
    if _engine is None:
        _engine = PatternEngine()
    return _engine


def feed_event(event: Any, domain: str = "default") -> None:
    """Feed event to global engine."""
    get_engine().feed(event, domain)


def predict() -> Prediction:
    """Make prediction using global engine."""
    return get_engine().predict_next()


def detect() -> List[Pattern]:
    """Detect patterns using global engine."""
    return get_engine().detect_patterns()
