"""
Tests for SimulationManager — state creation, persistence, and listing.
Does NOT require Neo4j or any external service.
"""

import os
import json
import tempfile
import pytest
from unittest.mock import patch


@pytest.fixture
def tmp_sim_dir(tmp_path):
    """Patch SimulationManager to use a temp directory for all state files."""
    with patch("app.services.simulation_manager.SimulationManager.SIMULATION_DATA_DIR", str(tmp_path)):
        yield tmp_path


def make_manager(tmp_sim_dir):
    from app.services.simulation_manager import SimulationManager
    return SimulationManager()


# ---------------------------------------------------------------------------
# create_simulation
# ---------------------------------------------------------------------------

def test_create_simulation_returns_state(tmp_sim_dir):
    manager = make_manager(tmp_sim_dir)
    state = manager.create_simulation(project_id="proj_abc", graph_id="graph_xyz")
    assert state.simulation_id.startswith("sim_")
    assert state.project_id == "proj_abc"
    assert state.graph_id == "graph_xyz"


def test_create_simulation_status_is_created(tmp_sim_dir):
    from app.services.simulation_manager import SimulationStatus
    manager = make_manager(tmp_sim_dir)
    state = manager.create_simulation(project_id="p1", graph_id="g1")
    assert state.status == SimulationStatus.CREATED


def test_create_simulation_persists_state_file(tmp_sim_dir):
    manager = make_manager(tmp_sim_dir)
    state = manager.create_simulation(project_id="p1", graph_id="g1")
    state_file = os.path.join(str(tmp_sim_dir), state.simulation_id, "state.json")
    assert os.path.exists(state_file)


def test_create_simulation_state_file_is_valid_json(tmp_sim_dir):
    manager = make_manager(tmp_sim_dir)
    state = manager.create_simulation(project_id="p1", graph_id="g1")
    state_file = os.path.join(str(tmp_sim_dir), state.simulation_id, "state.json")
    with open(state_file) as f:
        data = json.load(f)
    assert data["project_id"] == "p1"
    assert data["graph_id"] == "g1"


def test_create_simulation_default_platforms_enabled(tmp_sim_dir):
    manager = make_manager(tmp_sim_dir)
    state = manager.create_simulation(project_id="p1", graph_id="g1")
    assert state.enable_twitter is True
    assert state.enable_reddit is True


def test_create_simulation_custom_platform_flags(tmp_sim_dir):
    manager = make_manager(tmp_sim_dir)
    state = manager.create_simulation(
        project_id="p1", graph_id="g1",
        enable_twitter=False, enable_reddit=True
    )
    assert state.enable_twitter is False
    assert state.enable_reddit is True


# ---------------------------------------------------------------------------
# get_simulation
# ---------------------------------------------------------------------------

def test_get_simulation_returns_created_state(tmp_sim_dir):
    manager = make_manager(tmp_sim_dir)
    created = manager.create_simulation(project_id="p1", graph_id="g1")
    fetched = manager.get_simulation(created.simulation_id)
    assert fetched is not None
    assert fetched.simulation_id == created.simulation_id


def test_get_simulation_returns_none_for_missing_id(tmp_sim_dir):
    manager = make_manager(tmp_sim_dir)
    result = manager.get_simulation("sim_doesnotexist")
    assert result is None


def test_get_simulation_loads_from_disk(tmp_sim_dir):
    """A fresh SimulationManager should reload state from disk."""
    from app.services.simulation_manager import SimulationManager
    with patch("app.services.simulation_manager.SimulationManager.SIMULATION_DATA_DIR", str(tmp_sim_dir)):
        mgr1 = SimulationManager()
        created = mgr1.create_simulation(project_id="p1", graph_id="g1")
        sim_id = created.simulation_id

        # Create a second independent instance (empty in-memory cache)
        mgr2 = SimulationManager()
        loaded = mgr2.get_simulation(sim_id)

    assert loaded is not None
    assert loaded.project_id == "p1"


# ---------------------------------------------------------------------------
# list_simulations
# ---------------------------------------------------------------------------

def test_list_simulations_empty_when_none_created(tmp_sim_dir):
    manager = make_manager(tmp_sim_dir)
    result = manager.list_simulations()
    assert result == []


def test_list_simulations_returns_all(tmp_sim_dir):
    manager = make_manager(tmp_sim_dir)
    manager.create_simulation(project_id="p1", graph_id="g1")
    manager.create_simulation(project_id="p2", graph_id="g2")
    result = manager.list_simulations()
    assert len(result) == 2


def test_list_simulations_filters_by_project(tmp_sim_dir):
    manager = make_manager(tmp_sim_dir)
    manager.create_simulation(project_id="p1", graph_id="g1")
    manager.create_simulation(project_id="p2", graph_id="g2")
    manager.create_simulation(project_id="p1", graph_id="g3")
    result = manager.list_simulations(project_id="p1")
    assert len(result) == 2
    assert all(s.project_id == "p1" for s in result)


def test_list_simulations_ignores_dotfiles(tmp_sim_dir):
    """Hidden files/dirs like .DS_Store must not appear in listings."""
    # Create a hidden file inside the sim dir
    ds_store = os.path.join(str(tmp_sim_dir), ".DS_Store")
    with open(ds_store, "w") as f:
        f.write("")
    manager = make_manager(tmp_sim_dir)
    result = manager.list_simulations()
    assert result == []


# ---------------------------------------------------------------------------
# to_simple_dict / to_dict
# ---------------------------------------------------------------------------

def test_simulation_state_to_dict_has_required_keys(tmp_sim_dir):
    manager = make_manager(tmp_sim_dir)
    state = manager.create_simulation(project_id="p1", graph_id="g1")
    d = state.to_dict()
    for key in ("simulation_id", "project_id", "graph_id", "status",
                "entities_count", "profiles_count", "created_at", "updated_at"):
        assert key in d, f"Missing key: {key}"


def test_simulation_state_to_simple_dict_omits_verbose_fields(tmp_sim_dir):
    manager = make_manager(tmp_sim_dir)
    state = manager.create_simulation(project_id="p1", graph_id="g1")
    simple = state.to_simple_dict()
    # Runtime fields not needed in the simplified view
    assert "twitter_status" not in simple
    assert "reddit_status" not in simple
    assert "current_round" not in simple
