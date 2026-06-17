
                if (start_time is None or s.timestamp >= start_time) and
                   (end_time is None or s.timestamp <= end_time)
            ]
            self_model_snapshots = [
                s for s in self._self_model_history
                if (start_time is None or s.timestamp >= start_time) and
                   (end_time is None or s.timestamp <= end_time)
            ]
            
            return {
                "identity": self.identity,
                "belief_snapshots": [s.to_dict() for s in belief_snapshots],
                "desire_snapshots": [s.to_dict() for s in desire_snapshots],
                "self_model_snapshots": [s.to_dict() for s in self_model_snapshots],
                "current_beliefs": self._current_beliefs.to_dict(),
                "current_desires": self._current_desires.to_dict(),
                "current_self_model": self._current_self_model.to_dict(),
                "last_update": self._last_update.isoformat()
            }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the entire trajectory to a dictionary."""
        with self._lock:
            return {
                "identity": self.identity,
                "belief_history": [s.to_dict() for s in self._belief_history],
                "desire_history": [s.to_dict() for s in self._desire_history],
                "self_model_history": [s.to_dict() for s in self._self_model_history],
                "current_beliefs": self._current_beliefs.to_dict(),
                "current_desires": self._current_desires.to_dict(),
                "current_self_model": self._current_self_model.to_dict(),
                "belief_index": self._belief_index,
                "desire_index": self._desire_index,
                "last_update": self._last_update.isoformat()
            }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SelfTrajectory":
        """Deserialize a trajectory from a dictionary."""
        instance = cls(identity=data.get("identity", "EVEZ"))
        
        # Restore history
        instance._belief_history = [BeliefState.from_dict(s) for s in data.get("belief_history", [])]
        instance._desire_history = [DesireState.from_dict(s) for s in data.get("desire_history", [])]
        instance._self_model_history = [SelfModel.from_dict(s) for s in data.get("self_model_history", [])]
        
        # Restore current states
        instance._current_beliefs = BeliefState.from_dict(data.get("current_beliefs", {}))
        instance._current_desires = DesireState.from_dict(data.get("current_desires", {}))
        instance._current_self_model = SelfModel.from_dict(data.get("current_self_model", {}))
        
        # Restore indices
        instance._belief_index = data.get("belief_index", {})
        instance._desire_index = data.get("desire_index", {})
        
        # Restore last update time
        if "last_update" in data:
            instance._last_update = datetime.fromisoformat(data["last_update"])
        
        return instance
