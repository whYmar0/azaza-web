"""Тест уровня API."""

import pytest


@pytest.mark.django_db
def test_bad_field_value_returns_422(client):
    response = client.post(
        "/api/tasks", data={"name": "bad", "params": {"mode": "wrong-mode"}}, content_type="application/json"
    )
    assert response.status_code == 422
