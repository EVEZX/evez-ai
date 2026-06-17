
            new_value=new_value,
            metadata=metadata or {}
        )
        self._deltas.append(delta)
        self._save_state()
        return delta
