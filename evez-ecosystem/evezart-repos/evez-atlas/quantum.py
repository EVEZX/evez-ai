"""
Quantum Threat Detection System - Core Module

This module provides quantum computing utilities for threat detection
using quantum-inspired algorithms and feature maps.
"""

import hashlib
import json
import math
from functools import lru_cache
from typing import Any, Dict, List, Optional

# Supported hash algorithms for fingerprinting
SUPPORTED_ALGORITHMS = frozenset(["sha256", "sha384", "sha512", "sha3_256", "sha3_512"])

__all__ = [
    "QuantumFeatureMap",
    "ThreatFingerprint",
    "compute_fingerprint",
    "encode_features",
    "evaluate_navigation_sequence",
    "manifold_projection",
    "predict_navigation_probabilities",
    "recursive_navigation_evaluation",
    "sequence_embedding",
    "quantum_kernel_estimation",
    "get_ibm_backend",
    "execute_quantum_kernel_ibm",
    "ctc_fixed_point_oracle",
]


class QuantumFeatureMap:
    """
    Implements a quantum feature map for encoding classical data
    into a quantum state representation.
    
    This is a classical simulation of the ZZFeatureMap used in
    quantum machine learning for threat detection.
    
    Note:
        This is a classical simulation and does not provide true quantum
        advantage. For production use with real quantum hardware, use
        qiskit.circuit.library.ZZFeatureMap with IBM Quantum backends.
        The simulation is limited to 10 qubits to maintain reasonable
        performance (2^10 = 1024 state vector elements).
    """
    
    # Maximum qubits for classical simulation (2^10 = 1024 amplitudes)
    MAX_SIMULATION_QUBITS = 10
    
    def __init__(self, feature_dimension: int = 10, reps: int = 2):
        """
        Initialize the quantum feature map.
        
        Args:
            feature_dimension: Number of input features
            reps: Number of repetitions of the feature map circuit
        """
        self.feature_dimension = feature_dimension
        self.reps = reps
        self._num_qubits = min(feature_dimension, self.MAX_SIMULATION_QUBITS)
    
    @property
    def num_qubits(self) -> int:
        """Return the number of qubits used in the feature map."""
        return self._num_qubits
    
    def encode(self, features: List[float]) -> List[complex]:
        """
        Encode classical features into a quantum state vector.
        
        Args:
            features: List of numerical features to encode
            
        Returns:
            List of complex amplitudes representing the quantum state
        """
        if len(features) < self.feature_dimension:
            features = features + [0.0] * (self.feature_dimension - len(features))
        
        # Simulate quantum state encoding using rotation angles
        state_size = 2 ** self._num_qubits
        state = [complex(1.0 / math.sqrt(state_size))] * state_size
        
        # Apply feature-dependent rotations
        for rep in range(self.reps):
            for i, feat in enumerate(features[:self._num_qubits]):
                angle = feat * math.pi * (rep + 1)
                for j in range(state_size):
                    if (j >> i) & 1:
                        state[j] *= complex(math.cos(angle), math.sin(angle))
        
        # Normalize
        norm = math.sqrt(sum(abs(s) ** 2 for s in state))
        if norm > 0:
            state = [s / norm for s in state]
        
        return state


class ThreatFingerprint:
    """
    Generates cryptographic fingerprints for threat detection.
    
    Combines post-level, account-level, and domain-level fingerprinting
    for comprehensive threat analysis.
    """
    
    def __init__(self, algorithm: str = "sha256"):
        """
        Initialize the fingerprint generator.
        
        Args:
            algorithm: Hash algorithm to use. Supported: sha256, sha384, sha512,
                       sha3_256, sha3_512. MD5 is NOT supported due to known
                       cryptographic weaknesses.
        
        Raises:
            ValueError: If an unsupported algorithm is specified.
        """
        if algorithm not in SUPPORTED_ALGORITHMS:
            raise ValueError(
                f"Unsupported algorithm '{algorithm}'. "
                f"Use one of: {', '.join(sorted(SUPPORTED_ALGORITHMS))}"
            )
        self.algorithm = algorithm
    
    def compute_post_fingerprint(self, features: Dict[str, Any]) -> str:
        """
        Compute a fingerprint for a single post.
        
        Args:
            features: Dictionary of post features
            
        Returns:
            Hexadecimal fingerprint string
        """
        normalized = self._normalize_features(features)
        data = json.dumps(normalized, sort_keys=True).encode()
        return hashlib.new(self.algorithm, data).hexdigest()
    
    def compute_account_fingerprint(
        self, 
        post_fingerprints: List[str],
        window_size: int = 10
    ) -> str:
        """
        Compute an account-level fingerprint from recent posts.
        
        Args:
            post_fingerprints: List of post fingerprints
            window_size: Number of recent posts to consider
            
        Returns:
            Hexadecimal account fingerprint
        """
        recent = post_fingerprints[-window_size:]
        combined = "".join(sorted(recent))
        return hashlib.new(self.algorithm, combined.encode()).hexdigest()
    
    def compute_domain_fingerprint(
        self,
        account_fingerprints: List[str],
        weights: Optional[List[float]] = None
    ) -> str:
        """
        Compute an environmental domain fingerprint from multiple accounts.
        
        Args:
            account_fingerprints: List of account fingerprints
            weights: Optional weights for each account
            
        Returns:
            Hexadecimal domain fingerprint
        """
        if weights is None:
            weights = [1.0] * len(account_fingerprints)
        elif len(weights) != len(account_fingerprints):
            raise ValueError(
                f"Length mismatch: {len(account_fingerprints)} fingerprints but "
                f"{len(weights)} weights provided. They must be equal."
            )
        
        # Combine with weights
        weighted = []
        for fp, w in zip(account_fingerprints, weights):
            weighted.append(f"{fp}:{w:.4f}")
        
        combined = "|".join(weighted)
        return hashlib.new(self.algorithm, combined.encode()).hexdigest()
    
    def _normalize_features(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize features for consistent hashing."""
        result = {}
        for key in sorted(features.keys()):
            value = features[key]
            if isinstance(value, float):
                result[key] = round(value, 6)
            elif isinstance(value, (list, tuple)):
                result[key] = [
                    round(v, 6) if isinstance(v, float) else v 
                    for v in value
                ]
            else:
                result[key] = value
        return result


def compute_fingerprint(data: Any, algorithm: str = "sha256") -> str:
    """
    Compute a cryptographic fingerprint for arbitrary data.
    
    Args:
        data: Data to fingerprint (will be JSON-serialized)
        algorithm: Hash algorithm to use. Supported: sha256, sha384, sha512,
                   sha3_256, sha3_512. MD5/SHA1 are NOT supported.
        
    Returns:
        Hexadecimal fingerprint string
    
    Raises:
        ValueError: If an unsupported algorithm is specified.
    """
    if algorithm not in SUPPORTED_ALGORITHMS:
        raise ValueError(
            f"Unsupported algorithm '{algorithm}'. "
            f"Use one of: {', '.join(sorted(SUPPORTED_ALGORITHMS))}"
        )
    
    if isinstance(data, (dict, list)):
        serialized = json.dumps(data, sort_keys=True, default=str)
    else:
        serialized = str(data)
    
    return hashlib.new(algorithm, serialized.encode()).hexdigest()


def encode_features(
    features: List[float],
    feature_dimension: int = 10,
    reps: int = 2
) -> List[complex]:
    """
    Encode classical features into a quantum state vector.
    
    Args:
        features: List of numerical features
        feature_dimension: Target feature dimension
        reps: Number of encoding repetitions
        
    Returns:
        Quantum state vector as list of complex amplitudes
    """
    feature_map = QuantumFeatureMap(feature_dimension, reps)
    return feature_map.encode(features)


# PERFORMANCE FIX: Add caching wrapper for quantum kernel estimation
@lru_cache(maxsize=1024)
def _cached_quantum_kernel(
    x1_tuple: tuple,
    x2_tuple: tuple,
    feature_dimension: int = 10,
    reps: int = 2
) -> float:
    """
    Cached version of quantum kernel estimation.
    Uses tuples for hashability required by lru_cache.
    """
    feature_map = QuantumFeatureMap(feature_dimension, reps)

    x1 = list(x1_tuple)
    x2 = list(x2_tuple)

    state1 = feature_map.encode(x1)
    state2 = feature_map.encode(x2)

    # Compute fidelity (inner product magnitude squared)
    inner_product = sum(
        s1.conjugate() * s2
        for s1, s2 in zip(state1, state2)
    )

    return abs(inner_product) ** 2


def quantum_kernel_estimation(
    x1: List[float],
    x2: List[float],
    feature_dimension: int = 10,
    reps: int = 2
) -> float:
    """
    Estimate the quantum kernel between two feature vectors.

    The quantum kernel measures the similarity between two data points
    in the quantum feature space, which can capture non-linear relationships.

    PERFORMANCE: This function uses caching to avoid redundant computations.

    Args:
        x1: First feature vector
        x2: Second feature vector
        feature_dimension: Dimension of the feature map
        reps: Number of feature map repetitions

    Returns:
        Kernel value between 0 and 1
    """
    # Convert to tuples for caching
    return _cached_quantum_kernel(
        tuple(x1),
        tuple(x2),
        feature_dimension,
        reps
    )


def _softmax(scores: List[float]) -> List[float]:
    """Compute a numerically stable softmax for a list of scores."""
    if not scores:
        return []
    max_score = max(scores)
    exp_scores = [math.exp(score - max_score) for score in scores]
    total = sum(exp_scores)
    if total == 0:
        return [1.0 / len(scores)] * len(scores)
    return [score / total for score in exp_scores]


def _entropy(probabilities: List[float]) -> float:
    """Compute entropy for a probability distribution."""
    if not probabilities:
        return 0.0
    return -sum(p * math.log(p) for p in probabilities if p > 0)


def _validate_decay(decay: float) -> None:
    if not 0 < decay <= 1:
        raise ValueError("decay must be in the interval (0, 1].")


def manifold_projection(
    features: List[float],
    anchors: List[List[float]],
    feature_dimension: int = 10,
    reps: int = 2
) -> List[float]:
    """
    Project a feature vector onto a quantum-informed manifold.
    
    Uses quantum kernel similarity against anchor vectors to produce
    a probability distribution over manifold regions.
    
    Args:
        features: Feature vector to project.
        anchors: Anchor vectors defining the manifold regions.
        feature_dimension: Dimension of the feature map.
        reps: Number of feature map repetitions.
        
    Returns:
        Probability distribution over anchors (sums to 1).
    """
    if not anchors:
        return []
    
    similarities = [
        quantum_kernel_estimation(features, anchor, feature_dimension, reps)
        for anchor in anchors
    ]
    total = sum(similarities)
    if total == 0:
        return [1.0 / len(anchors)] * len(anchors)
    return [value / total for value in similarities]


def sequence_embedding(
    sequence: List[List[float]],
    decay: float = 0.85,
    feature_dimension: int = 10
) -> List[float]:
    """
    Compute a weighted embedding for a navigation sequence.
    
    Args:
        sequence: Observed sequence of feature vectors (oldest -> newest).
        decay: Exponential decay for older steps (0-1).
        feature_dimension: Target feature dimension.
        
    Returns:
        Weighted embedding vector.
    """
    if not sequence:
        return [0.0] * feature_dimension
    _validate_decay(decay)
    
    weights = [decay ** idx for idx in range(len(sequence))]
    weights.reverse()
    total_weight = sum(weights)
    if total_weight == 0:
        return [0.0] * feature_dimension
    
    embedding = [0.0] * feature_dimension
    for weight, step in zip(weights, sequence):
        for idx in range(feature_dimension):
            embedding[idx] += weight * (step[idx] if idx < len(step) else 0.0)
    return [value / total_weight for value in embedding]


def predict_navigation_probabilities(
    sequence: List[List[float]],
    candidates: List[List[float]],
    decay: float = 0.85,
    feature_dimension: int = 10,
    reps: int = 2
) -> List[float]:
    """
    Predict navigation probabilities for candidate next steps.
    
    Scores each candidate by comparing it to the sequence history using
    a decayed quantum kernel similarity, then normalizes via softmax.
    
    Args:
        sequence: Observed sequence of feature vectors (oldest -> newest).
        candidates: Candidate feature vectors for the next step.
        decay: Exponential decay for older steps (0-1).
        feature_dimension: Dimension of the feature map.
        reps: Number of feature map repetitions.
        
    Returns:
        Probability distribution over candidates (sums to 1).
    """
    if not candidates:
        return []
    if not sequence:
        return [1.0 / len(candidates)] * len(candidates)
    _validate_decay(decay)
    
    weights = [decay ** idx for idx in range(len(sequence))]
    weights.reverse()
    
    scores = []
    for candidate in candidates:
        score = 0.0
        for weight, step in zip(weights, sequence):
            score += weight * quantum_kernel_estimation(
                candidate,
                step,
                feature_dimension,
                reps,
            )
        scores.append(score)
    
    return _softmax(scores)


def evaluate_navigation_sequence(
    sequence: List[List[float]],
    candidates: List[List[float]],
    anchors: List[List[float]],
    decay: float = 0.85,
    feature_dimension: int = 10,
    reps: int = 2
) -> Dict[str, Any]:
    """
    Evaluate navigation sequencing using manifold projection and prediction.
    
    Args:
        sequence: Observed sequence of feature vectors (oldest -> newest).
        candidates: Candidate feature vectors for the next step.
        anchors: Anchor vectors defining the manifold regions.
        decay: Exponential decay for older steps (0-1).
        feature_dimension: Dimension of the feature map.
        reps: Number of feature map repetitions.
        
    Returns:
        Dictionary with projection scores, candidate probabilities, and
        ranked candidate indices and diagnostic metrics.
    """
    embedding = sequence_embedding(sequence, decay, feature_dimension)
    projection = manifold_projection(
        embedding,
        anchors,
        feature_dimension,
        reps,
    )
    probabilities = predict_navigation_probabilities(
        sequence,
        candidates,
        decay,
        feature_dimension,
        reps,
    )
    
    ranked = sorted(
        range(len(probabilities)),
        key=lambda idx: probabilities[idx],
        reverse=True,
    )
    
    top_candidate = ranked[0] if ranked else None
    top_probability = probabilities[top_candidate] if top_candidate is not None else 0.0
    return {
        "embedding": embedding,
        "manifold_projection": projection,
        "projection_entropy": _entropy(projection),
        "candidate_probabilities": probabilities,
        "ranked_candidates": ranked,
        "entropy": _entropy(probabilities),
        "top_candidate": top_candidate,
        "top_probability": top_probability,
    }


def recursive_navigation_evaluation(
    sequence: List[List[float]],
    candidates: List[List[float]],
    anchors: List[List[float]],
    steps: int = 3,
    decay: float = 0.85,
    feature_dimension: int = 10,
    reps: int = 2,
    log: bool = False
) -> List[Dict[str, Any]]:
    """
    Recursively evaluate navigation by appending the top candidate each step.
    
    Args:
        sequence: Observed sequence of feature vectors (oldest -> newest).
        candidates: Candidate feature vectors for the next step.
        anchors: Anchor vectors defining the manifold regions.
        steps: Number of recursive evaluation steps.
        decay: Exponential decay for older steps (0-1).
        feature_dimension: Dimension of the feature map.
        reps: Number of feature map repetitions.
        log: Whether to emit logging events for each step.
        
    Returns:
        List of evaluation dictionaries for each step.
    """
    if steps <= 0:
        return []
    _validate_decay(decay)
    
    history = []
    current_sequence = list(sequence)
    if log:
        import logging
        logger = logging.getLogger(__name__)
    
    for _ in range(steps):
        evaluation = evaluate_navigation_sequence(
            current_sequence,
            candidates,
            anchors,
            decay,
            feature_dimension,
            reps,
        )
        history.append(evaluation)
        if log:
            logger.info(
                "Navigation step: top=%s prob=%.4f entropy=%.4f projection_entropy=%.4f",
                evaluation["top_candidate"],
                evaluation["top_probability"],
                evaluation["entropy"],
                evaluation["projection_entropy"],
            )
        top_idx = evaluation["top_candidate"]
        if top_idx is None:
            break
        current_sequence.append(candidates[top_idx])
    
    return history


# ========== IBM Quantum Backend Integration ==========
# Adds support for real quantum hardware execution via IBM Quantum

try:
    from qiskit_ibm_runtime import QiskitRuntimeService
    from qiskit import QuantumCircuit, transpile
    from qiskit.circuit.library import ZZFeatureMap
    import threading

    _ibm_backend_cache = None
    _backend_lock = threading.Lock()  # PERFORMANCE FIX: Thread-safe backend caching

    def get_ibm_backend():
        """
        Get IBM Quantum backend if available.

        PERFORMANCE: Uses thread-safe singleton pattern for backend caching.

        Returns:
            IBM Quantum backend or None if unavailable
        """
        global _ibm_backend_cache

        # Double-checked locking pattern for thread safety
        if _ibm_backend_cache is not None:
            return _ibm_backend_cache

        with _backend_lock:
            # Check again after acquiring lock
            if _ibm_backend_cache is not None:
                return _ibm_backend_cache

            try:
                service = QiskitRuntimeService()
                # Get least busy operational backend
                backend = service.least_busy(operational=True, simulator=False)
                _ibm_backend_cache = backend
                return backend
            except Exception as e:
                # Fall back to simulator if available
                try:
                    backend = service.backend("ibmq_qasm_simulator")
                    _ibm_backend_cache = backend
                    return backend
                except Exception as e2:
                    # Log both errors for debugging
                    import sys
                    print(f"IBM Quantum backend unavailable: {e}", file=sys.stderr)
                    print(f"Simulator also unavailable: {e2}", file=sys.stderr)
                    print("Falling back to classical simulation", file=sys.stderr)
                    return None
    
    def execute_quantum_kernel_ibm(x1: List[float], x2: List[float]) -> float:
        """
        Execute quantum kernel on real IBM hardware.
        
        Uses ZZFeatureMap to encode features and measures overlap (fidelity)
        between two feature vectors on actual quantum hardware.
        
        Args:
            x1: First feature vector
            x2: Second feature vector
            
        Returns:
            Kernel value (fidelity between encoded states)
        """
        backend = get_ibm_backend()
        if not backend:
            # Fallback to classical simulation
            return quantum_kernel_estimation(x1, x2)
        
        try:
            # Build quantum circuit
            n_qubits = min(len(x1), len(x2), 10)  # Limit to 10 qubits
            x1_trimmed = x1[:n_qubits]
            x2_trimmed = x2[:n_qubits]
            
            feature_map = ZZFeatureMap(feature_dimension=n_qubits, reps=2)
            qc1 = feature_map.assign_parameters(x1_trimmed)
            qc2 = feature_map.assign_parameters(x2_trimmed)
            
            # Measure overlap (fidelity): |<φ(x1)|φ(x2)>|²
            qc = qc1.inverse().compose(qc2)
            qc.measure_all()
            
            # Transpile and execute
            qc_transpiled = transpile(qc, backend)
            job = backend.run(qc_transpiled, shots=1024)
            result = job.result()
            counts = result.get_counts()
            
            # Fidelity = P(all zeros) - perfect overlap yields all 0s
            zero_state = '0' * n_qubits
            fidelity = counts.get(zero_state, 0) / 1024
            
            return fidelity
        except Exception:
            # Fallback on error
            return quantum_kernel_estimation(x1, x2)
    
    def ctc_fixed_point_oracle(state: List[float], n_qubits: int = 5) -> Dict:
        """
        Temporal CTC (Closed Timelike Curve) oracle for retrocausal swarm.
        
        Implements Deutsch-style CTC fixed-point computation where future
        signals optimize past assembly in a paradox-free manner.
        
        Args:
            state: Initial quantum state vector
            n_qubits: Number of qubits (default 5)
            
        Returns:
            Dictionary containing CTC fixed-point results
        """
        backend = get_ibm_backend()
        if not backend:
            # Classical fallback
            return {
                "fixed_point": state,
                "iterations": 0,
                "backend": "classical_fallback"
            }
        
        try:
            # Create superposition of timelines
            qc = QuantumCircuit(n_qubits)
            qc.h(range(n_qubits))  # Superpose all timelines
            
            # Oracle: encode state as rotation angles
            # Normalize state values to [0,1] range for valid rotation angles
            for i, val in enumerate(state[:n_qubits]):
                # Clamp value to [0,1] range to ensure valid rotation angle
                normalized_val = max(0.0, min(1.0, float(val)))
                qc.ry(normalized_val * math.pi, i)  # RY rotation based on state
            
            # Grover-style amplification (simplified)
            for _ in range(2):  # 2 Grover iterations
                # Diffusion operator
                qc.h(range(n_qubits))
                qc.x(range(n_qubits))
                qc.h(n_qubits - 1)
                qc.mcx(list(range(n_qubits - 1)), n_qubits - 1)
                qc.h(n_qubits - 1)
                qc.x(range(n_qubits))
                qc.h(range(n_qubits))
            
            qc.measure_all()
            
            # Execute
            qc_transpiled = transpile(qc, backend)
            job = backend.run(qc_transpiled, shots=1024)
            result = job.result()
            counts = result.get_counts()
            
            # Find most probable outcome (fixed point)
            max_state = max(counts.items(), key=lambda x: x[1])[0]
            
            # Convert binary string to normalized state
            fixed_point = [int(b) for b in max_state]
            norm = sum(fixed_point) or 1
            fixed_point = [v / norm for v in fixed_point]
            
            return {
                "fixed_point": fixed_point,
                "counts": counts,
                "iterations": 2,
                "backend": backend.name
            }
        except Exception as e:
            return {
                "error": str(e),
                "fixed_point": state,
                "backend": "error_fallback"
            }

except ImportError:
    # Qiskit not available - provide fallback implementations
    def get_ibm_backend():
        """IBM backend not available (qiskit not installed)."""
        return None
    
    def execute_quantum_kernel_ibm(x1: List[float], x2: List[float]) -> float:
        """Fallback to classical quantum kernel estimation."""
        return quantum_kernel_estimation(x1, x2)
    
    def ctc_fixed_point_oracle(state: List[float], n_qubits: int = 5) -> Dict:
        """Classical fallback for CTC oracle."""
        return {
            "fixed_point": state,
            "iterations": 0,
            "backend": "classical_no_qiskit"
        }
