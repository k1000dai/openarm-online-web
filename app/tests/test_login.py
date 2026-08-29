# Copyright 2026 Enactic, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.main import app
from app.models import User
from app.security import get_sub


def _anonymous_client() -> TestClient:
    return TestClient(app, follow_redirects=False)


def test_login_page(session: Session):
    response = _anonymous_client().get("/login/")
    assert response.status_code == 200
    assert "Login as guest" in response.text


def test_login_guest(session: Session):
    response = _anonymous_client().post("/login/guest")
    assert response.status_code == 303
    assert response.headers["location"] == "/"

    users = session.exec(select(User)).all()
    assert len(users) == 1
    # The cookie logs the browser in as the created guest user.
    assert get_sub(response.cookies["access_token"]) == str(users[0].id)


def test_login_guest_creates_user_per_login(session: Session):
    client = _anonymous_client()
    client.post("/login/guest")
    client.post("/login/guest")

    assert len(session.exec(select(User)).all()) == 2
