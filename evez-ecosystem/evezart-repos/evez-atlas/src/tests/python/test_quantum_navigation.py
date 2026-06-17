import pytest

from demo import build_navigation_ui_state

from quantum import (
    evaluate_navigation_sequence,
    manifold_projection,
    predict_navigation_probabilities,
    recursive_navigation_evaluation,
    sequence_embedding,
)


def test_manifold_projection_normalizes():
    features = [0.1, 0.2, 0.3]
    anchors = [
        [0.1, 0.2, 0.3],
        [0.9, 0.8, 0.7],
        [0.4, 0.4, 0.4],
    ]
    projection = manifold_projection(features, anchors, feature_dimension=3, reps=1)
    assert len(projection) == len(anchors)
    assert abs(sum(projection) - 1.0) < 1e-6


def test_predict_navigation_probabilities_prefers_recent_match():
    sequence = [
        [0.0, 0.0, 0.0],
        [0.2, 0.2, 0.2],
        [0.9, 0.9, 0.9],
    ]
    candidates = [
        [0.1, 0.1, 0.1],
        [0.9, 0.9, 0.9],
    ]
    probabilities = predict_navigation_probabilities(
        sequence,
        candidates,
        decay=0.5,
        feature_dimension=3,
        reps=1,
    )
    assert len(probabilities) == len(candidates)
    assert probabilities[1] > probabilities[0]


def test_sequence_embedding_weights_recent_entries():
    sequence = [
        [0.0, 0.0, 0.0],
        [1.0, 1.0, 1.0],
    ]
    embedding = sequence_embedding(sequence, decay=0.5, feature_dimension=3)
    assert embedding[0] > 0.5


def test_predict_navigation_probabilities_rejects_invalid_decay():
    with pytest.raises(ValueError):
        predict_navigation_probabilities(
            sequence=[[0.1, 0.2, 0.3]],
            candidates=[[0.1, 0.2, 0.3]],
            decay=0.0,
            feature_dimension=3,
            reps=1,
        )


def test_evaluate_navigation_sequence_ranks_candidates():
    sequence = [
        [0.3, 0.3, 0.3],
        [0.7, 0.7, 0.7],
    ]
    candidates = [
        [0.2, 0.2, 0.2],
        [0.7, 0.7, 0.7],
    ]
    anchors = [
        [0.0, 0.0, 0.0],
        [1.0, 1.0, 1.0],
    ]
    evaluation = evaluate_navigation_sequence(
        sequence,
        candidates,
        anchors,
        decay=0.8,
        feature_dimension=3,
        reps=1,
    )
    assert evaluation["ranked_candidates"][0] == 1
    assert evaluation["top_candidate"] == 1


def test_recursive_navigation_evaluation_tracks_steps():
    sequence = [
        [0.1, 0.1, 0.1],
    ]
    candidates = [
        [0.2, 0.2, 0.2],
        [0.9, 0.9, 0.9],
    ]
    anchors = [
        [0.0, 0.0, 0.0],
        [1.0, 1.0, 1.0],
    ]
    history = recursive_navigation_evaluation(
        sequence,
        candidates,
        anchors,
        steps=2,
        decay=0.9,
        feature_dimension=3,
        reps=1,
    )
    assert len(history) == 2
    assert history[0]["top_candidate"] is not None


def test_build_navigation_ui_state_shapes():
    state = build_navigation_ui_state(seed=7, feature_dimension=5, steps=2, decay=0.8, reps=1)
    assert len(state["sensor_tasks"]) == 6
    assert len(state["sequence"]) == 3
    assert len(state["candidates"]) == 4
    assert len(state["anchors"]) == 3
    assert len(state["recursive"]) == 2
    assert len(state["evaluation"]["candidate_probabilities"]) == 4
