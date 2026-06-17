"""EVEZ Memory Storage - Immutable Spine"""
import json
from pathlib import Path

class SpineStorage:
    def __init__(self, path="memory/spine.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(exist_ok=True)
    
    def append(self, event):
        self.path.write_text(self.path.read_text() + json.dumps(event) + "\n")
    
    def read(self, n=10):
        lines = self.path.read_text().strip().split("\n")
        return [json.loads(l) for l in lines[-n:]]
