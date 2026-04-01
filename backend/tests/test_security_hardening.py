"""
Tests for security hardening changes introduced in session 3:
- Traceback field is stripped from non-debug JSON error responses
- CORS_ORIGINS config is parsed correctly from env vars
- _world_sim_results eviction prevents unbounded growth
"""

import json
import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Traceback stripping middleware
# ---------------------------------------------------------------------------

@pytest.fixture
def production_app():
    """Flask app in non-debug (production) mode."""
    with patch("app.storage.Neo4jStorage") as MockStorage:
        MockStorage.return_value = MagicMock()
        with patch.dict("os.environ", {"FLASK_DEBUG": "false"}):
            from app.config import Config
            # Force debug off for this test
            original_debug = Config.DEBUG
            Config.DEBUG = False
            from app import create_app
            flask_app = create_app()
            flask_app.config["TESTING"] = True
            flask_app.config["DEBUG"] = False

            # Add a test route that returns traceback in its JSON body
            @flask_app.route("/test-error-route")
            def test_error_route():
                from flask import jsonify
                return jsonify({
                    "success": False,
                    "error": "something broke",
                    "traceback": "Traceback (most recent call last): ...\nValueError: oops"
                }), 500

            yield flask_app
            Config.DEBUG = original_debug


@pytest.fixture
def production_client(production_app):
    return production_app.test_client()


def test_traceback_stripped_in_production(production_client):
    """In non-debug mode, the 'traceback' field must be removed from JSON responses."""
    res = production_client.get("/test-error-route")
    data = res.get_json()
    assert "traceback" not in data


def test_error_message_preserved_in_production(production_client):
    """The 'error' field must still be present after stripping 'traceback'."""
    res = production_client.get("/test-error-route")
    data = res.get_json()
    assert data["error"] == "something broke"


@pytest.fixture
def debug_app():
    """Flask app in debug mode — tracebacks should be preserved."""
    with patch("app.storage.Neo4jStorage") as MockStorage:
        MockStorage.return_value = MagicMock()
        from app.config import Config
        original_debug = Config.DEBUG
        Config.DEBUG = True
        from app import create_app
        flask_app = create_app()
        flask_app.config["TESTING"] = True
        flask_app.config["DEBUG"] = True

        @flask_app.route("/test-debug-error")
        def test_debug_error():
            from flask import jsonify
            return jsonify({
                "success": False,
                "error": "oops",
                "traceback": "Traceback: ..."
            }), 500

        yield flask_app
        Config.DEBUG = original_debug


@pytest.fixture
def debug_client(debug_app):
    return debug_app.test_client()


def test_traceback_preserved_in_debug_mode(debug_client):
    """In debug mode, the 'traceback' field must NOT be stripped."""
    res = debug_client.get("/test-debug-error")
    data = res.get_json()
    assert "traceback" in data


# ---------------------------------------------------------------------------
# CORS_ORIGINS config parsing
# ---------------------------------------------------------------------------

def test_cors_origins_default_is_wildcard():
    """Default CORS_ORIGINS must be '*' for local-dev convenience."""
    with patch.dict("os.environ", {}, clear=False):
        # Remove CORS_ORIGINS from env if present
        import os
        os.environ.pop("CORS_ORIGINS", None)
        # Reimport to pick up fresh env
        import importlib
        import app.config as cfg_mod
        importlib.reload(cfg_mod)
        assert cfg_mod.Config.CORS_ORIGINS == "*"


def test_cors_origins_reads_from_env():
    """When CORS_ORIGINS is set, Config should reflect it."""
    import importlib
    import app.config as cfg_mod
    with patch.dict("os.environ", {"CORS_ORIGINS": "http://localhost:3000"}):
        importlib.reload(cfg_mod)
        assert cfg_mod.Config.CORS_ORIGINS == "http://localhost:3000"


# ---------------------------------------------------------------------------
# World simulation result eviction
# ---------------------------------------------------------------------------

def test_evict_world_sim_results_removes_finished_entries():
    """When _world_sim_results exceeds the cap, finished entries are evicted."""
    from app.api.simulation import _evict_world_sim_results, _world_sim_lock
    import app.api.simulation as sim_api

    # Save original state
    original = dict(sim_api._world_sim_results)
    original_max = sim_api._WORLD_SIM_MAX_ENTRIES

    try:
        sim_api._WORLD_SIM_MAX_ENTRIES = 5
        sim_api._world_sim_results.clear()

        # Fill with completed entries beyond the cap
        for i in range(6):
            sim_api._world_sim_results[f"world_{i}"] = {"status": "completed"}

        with _world_sim_lock:
            _evict_world_sim_results()

        # After eviction, count should be below cap
        assert len(sim_api._world_sim_results) < 6
    finally:
        sim_api._world_sim_results.clear()
        sim_api._world_sim_results.update(original)
        sim_api._WORLD_SIM_MAX_ENTRIES = original_max


def test_evict_does_not_remove_running_entries():
    """Running entries must NOT be evicted."""
    from app.api.simulation import _evict_world_sim_results, _world_sim_lock
    import app.api.simulation as sim_api

    original = dict(sim_api._world_sim_results)
    original_max = sim_api._WORLD_SIM_MAX_ENTRIES

    try:
        sim_api._WORLD_SIM_MAX_ENTRIES = 3
        sim_api._world_sim_results.clear()

        # 2 running + 2 completed = 4 entries (exceeds cap of 3)
        sim_api._world_sim_results["running_1"] = {"status": "running"}
        sim_api._world_sim_results["running_2"] = {"status": "running"}
        sim_api._world_sim_results["done_1"] = {"status": "completed"}
        sim_api._world_sim_results["done_2"] = {"status": "completed"}

        with _world_sim_lock:
            _evict_world_sim_results()

        # Running entries must still be present
        assert "running_1" in sim_api._world_sim_results
        assert "running_2" in sim_api._world_sim_results
    finally:
        sim_api._world_sim_results.clear()
        sim_api._world_sim_results.update(original)
        sim_api._WORLD_SIM_MAX_ENTRIES = original_max


def test_evict_noop_when_under_cap():
    """No eviction should occur if the dict is within the cap."""
    from app.api.simulation import _evict_world_sim_results, _world_sim_lock
    import app.api.simulation as sim_api

    original = dict(sim_api._world_sim_results)
    original_max = sim_api._WORLD_SIM_MAX_ENTRIES

    try:
        sim_api._WORLD_SIM_MAX_ENTRIES = 100
        sim_api._world_sim_results.clear()
        sim_api._world_sim_results["w1"] = {"status": "completed"}
        sim_api._world_sim_results["w2"] = {"status": "failed"}

        with _world_sim_lock:
            _evict_world_sim_results()

        assert len(sim_api._world_sim_results) == 2
    finally:
        sim_api._world_sim_results.clear()
        sim_api._world_sim_results.update(original)
        sim_api._WORLD_SIM_MAX_ENTRIES = original_max
