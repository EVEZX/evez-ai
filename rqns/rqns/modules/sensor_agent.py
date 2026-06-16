"""Sensor Agent — LIF Neuromorphic SNN for anomaly detection"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

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

    def _lif_step(self, I):
        self.v = self.v + (I - self.v / SNNConfig.tau) * SNNConfig.dt
        spike = 1 if self.v >= SNNConfig.threshold else 0
        if spike:
            self.v = SNNConfig.rest_potential
        return spike

    def process_signal(self, signal):
        raw = np.array(signal.raw_data) if isinstance(signal.raw_data, list) else np.random.exponential(0.15, 50)
        raw = (raw - raw.mean()) / (raw.std() + 1e-6)

        spikes = []
        self.v = 0.0
        for sample in raw:
            I = max(0, sample * 3.0)
            spike = self._lif_step(I)
            spikes.append(spike)
            self.spike_history.append(spike)

        spike_count = sum(spikes)
        complexity = 15.0 + spike_count * 1.4 + np.random.uniform(-1.5, 2.5)
        confidence = min(1.0, spike_count / 45.0 + 0.4)

        return DetectionResult(
            signal_id=signal.source_id,
            complexity=complexity,
            confidence=confidence,
            is_anomaly=spike_count > 8,
            features={"spike_count": spike_count, "spike_train": spikes[-100:]}
        )
