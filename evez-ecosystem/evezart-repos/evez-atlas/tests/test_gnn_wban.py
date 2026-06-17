from agents.network.gnn_wban import GNNWBANOptimizer


def test_gnn_converges_within_20_epochs(tmp_path):
    optimizer = GNNWBANOptimizer(topology_path=str(tmp_path / "gnn_topology.json"))
    losses = optimizer.train(epochs=20)
    assert len(losses) == 20
    assert losses[-1] < losses[0]


def test_gnn_emits_topology(tmp_path):
    optimizer = GNNWBANOptimizer(topology_path=str(tmp_path / "gnn_topology.json"))
    payload = optimizer.optimize_and_emit()
    assert len(payload["nodes"]) == 6
    assert len(payload["edges"]) == 6
    assert (tmp_path / "gnn_topology.json").exists()
