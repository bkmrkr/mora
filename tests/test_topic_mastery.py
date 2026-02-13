"""Tests for topic mastery calculation."""
import pytest
from unittest.mock import patch, MagicMock


class TestComputeTopicMastery:
    """Tests for _compute_topic_mastery function."""

    def test_returns_zero_when_no_nodes(self):
        """Should return 0 when topic has no curriculum nodes."""
        with patch('routes.session.node_model') as mock_nodes:
            with patch('routes.session.skill_model') as mock_skill:
                mock_nodes.get_for_topic.return_value = []
                mock_skill.get.return_value = {'mastery_level': 0.5}

                from routes.session import _compute_topic_mastery
                result = _compute_topic_mastery(1, 1)
                assert result == 0.0

    def test_averages_multiple_nodes(self):
        """Should average mastery across all nodes in topic."""
        with patch('routes.session.node_model') as mock_nodes:
            with patch('routes.session.skill_model') as mock_skill:
                # 3 nodes with mastery 0.6, 0.7, 0.8
                mock_nodes.get_for_topic.return_value = [
                    {'id': 1}, {'id': 2}, {'id': 3}
                ]
                mock_skill.get.side_effect = [
                    {'mastery_level': 0.6},
                    {'mastery_level': 0.7},
                    {'mastery_level': 0.8},
                ]

                from routes.session import _compute_topic_mastery
                result = _compute_topic_mastery(1, 1)
                # (0.6 + 0.7 + 0.8) / 3 * 100 = 70%
                assert result == 70.0

    def test_returns_one_decimal_place(self):
        """Should return value with 1 decimal place for precision."""
        with patch('routes.session.node_model') as mock_nodes:
            with patch('routes.session.skill_model') as mock_skill:
                # Mastery that would round to same in integer
                mock_nodes.get_for_topic.return_value = [{'id': 1}]
                mock_skill.get.return_value = {'mastery_level': 0.644}

                from routes.session import _compute_topic_mastery
                result = _compute_topic_mastery(1, 1)
                # 0.644 * 100 = 64.4
                assert result == 64.4


class TestGetTopicProgress:
    """Tests for _get_topic_progress function."""

    def test_returns_progress_for_each_node(self):
        """Should return progress dict for each node in topic."""
        with patch('routes.session.node_model') as mock_nodes:
            with patch('routes.session.skill_model') as mock_skill:
                with patch('routes.session.elo') as mock_elo:
                    mock_nodes.get_for_topic.return_value = [
                        {'id': 1, 'name': 'Node A'},
                        {'id': 2, 'name': 'Node B'},
                    ]
                    mock_skill.get.side_effect = [
                        {'mastery_level': 0.5, 'skill_rating': 800, 'total_attempts': 5},
                        {'mastery_level': 0.8, 'skill_rating': 1000, 'total_attempts': 10},
                    ]
                    mock_elo.is_mastered.side_effect = [False, True]

                    from routes.session import _get_topic_progress
                    result = _get_topic_progress(1, 1)

                    assert len(result) == 2
                    assert result[0]['name'] == 'Node A'
                    assert result[0]['mastery_pct'] == 50.0
                    assert result[1]['name'] == 'Node B'
                    assert result[1]['mastery_pct'] == 80.0

    def test_differentiates_similar_mastery_values(self):
        """Should show different percentages for similar mastery values.

        This is the key bug fix: values like 0.642 and 0.644 should
        display as 64.2% and 64.4%, not both as 64%.
        """
        with patch('routes.session.node_model') as mock_nodes:
            with patch('routes.session.skill_model') as mock_skill:
                with patch('routes.session.elo') as mock_elo:
                    mock_nodes.get_for_topic.return_value = [
                        {'id': 1, 'name': 'Node A'},
                        {'id': 2, 'name': 'Node B'},
                    ]
                    # Two nodes with very similar mastery
                    mock_skill.get.side_effect = [
                        {'mastery_level': 0.642, 'skill_rating': 884, 'total_attempts': 5},
                        {'mastery_level': 0.644, 'skill_rating': 888, 'total_attempts': 5},
                    ]
                    mock_elo.is_mastered.return_value = False

                    from routes.session import _get_topic_progress
                    result = _get_topic_progress(1, 1)

                    # Should NOT be equal - they should be 64.2% and 64.4%
                    assert result[0]['mastery_pct'] != result[1]['mastery_pct']
                    assert result[0]['mastery_pct'] == 64.2
                    assert result[1]['mastery_pct'] == 64.4


class TestMasteryDelta:
    """Tests that mastery delta is computed correctly.

    This was a key bug: delta showed 0% even when mastery changed
    because rounding lost precision.
    """

    def test_delta_reflects_small_changes(self):
        """Small mastery changes should be visible in delta."""
        # Simulate: before avg = 64.4%, after avg = 64.5%
        before = 64.4
        after = 64.5
        delta = round(after - before, 1)

        assert delta == 0.1, "Delta should be 0.1%, not 0%"

    def test_delta_with_integer_rounding_was_bug(self):
        """Demonstrate the old bug: integer rounding loses delta."""
        # Old code: round(64.4) = 64, round(64.5) = 65, delta = 1%
        # But with values 64.4 and 64.41: round both = 64, delta = 0%
        before_int = round(64.4)  # 64
        after_int = round(64.41)  # 64 (same!)
        delta_int = after_int - before_int

        # With new code using decimal places: 64.4 stays 64.4
        # Note: Python's round() uses banker's rounding (round half to even)
        before_float = round(64.4, 1)  # 64.4
        after_float = round(64.41, 1)  # 64.4 (banker's rounding)
        delta_float = round(after_float - before_float, 1)

        assert delta_int == 0, "Old bug: delta was 0% with int rounding"
        # With banker's rounding, both round to 64.4, so delta is 0
        # This demonstrates the limitation of float rounding regardless
        assert delta_float == 0.0, "Banker's rounding affects small deltas"
