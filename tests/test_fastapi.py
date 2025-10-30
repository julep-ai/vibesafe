"""Tests for vibesafe.fastapi integration helper."""

from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from vibesafe.fastapi import mount


def _set_test_config(monkeypatch, test_config):
    from vibesafe import config as config_module

    config_module._config = test_config


def test_mount_on_router(test_config, monkeypatch):
    _set_test_config(monkeypatch, test_config)

    router = APIRouter()
    mount(router)

    app = FastAPI()
    app.include_router(router)

    client = TestClient(app)

    resp = client.get("/_vibesafe/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

    version = client.get("/_vibesafe/version")
    assert version.status_code == 200
    payload = version.json()
    assert payload["env"] == "dev"
    assert "version" in payload


def test_mount_on_app_with_custom_prefix(test_config, monkeypatch):
    _set_test_config(monkeypatch, test_config)

    app = FastAPI()
    mount(app, prefix="/.well-known/vibesafe")

    client = TestClient(app)

    resp = client.get("/.well-known/vibesafe/health")
    assert resp.status_code == 200

    resp = client.get("/.well-known/vibesafe/version")
    assert resp.status_code == 200
    assert resp.json()["env"] == "dev"
