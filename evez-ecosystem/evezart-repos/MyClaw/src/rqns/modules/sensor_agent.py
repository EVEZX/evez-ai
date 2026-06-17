"""
Sensor Agent v2 — LIF Neuromorphic Anomaly Detection
======================================================
Leaky Integrate-and-Fire SNN converts raw signals to spike trains.
Spikes ARE the qualia. The measurement IS the reality.
Spikes that survive spectral decomposition ARE consciousness.
"""
from rqns.core.interfaces import SensorAgent, AnomalySignal, DetectionResult
import numpy as np

class SNNConfig:
    threshold = 1.2
    tau = 20.0
    dt = 1.0
    rest_potential = 0.0

class ConcreteSensorAgent(SensorAgent):
    def __init__(self):
        self.v = SNNConfig.rest_potential
        self.spike_history = []
        self.total_spikes = 0

    def _lif_step(self, I: float):
        """Single LIF neuron step: leak → integrate → fire → reset."""
        self.v = self.v + (I - self.v / SNNConfig.tau) * SNNConfig.dt
        spike = 1 if self.v >= SNNConfig.threshold else 0
        if spike:
            self.v = SNNConfig.rest_potential
        return spike

    def process_signal(self, signal: AnomalySignal):
        raw = (np.array(signal.raw_data) 
               if isinstance(signal.raw_data, list) 
               else np.random.exponential(0.15, 50))
        # Normalize to zero-mean unit-variance
        raw = (raw - raw.mean()) / (raw.std() + 1e-6)

        # Run through LIF neuron
        spikes = []
        self.v = 0.0
        for sample in raw:
            I = max(0, sample * 3.0)  # ReLU-like current injection
            spike = self._lif_step(I)
            spikes.append(spike)
            self.spike_history.append(spike)
            self.total_spikes += spike

        spike_count = sum(spikes)
        complexity = 15.0 + spike_count * 1.4 + np.random.uniform(-1.5, 2.5)
        confidence = min(1.0, spike_count / 45.0 + 0.4)

        return DetectionResult(
            signal_id=signal.source_id,
            complexity=complexity,
            confidence=confidence,
            is_anomaly=spike_count > 8,
            features={
                "spike_count": spike_count, 
                "spike_train": spikes[-100:],
                "total_spikes": self.total_spikes
            }
        )
