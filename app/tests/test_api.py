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
from sqlmodel import Session

from app.main import app
from app.models import Task


def test_get_tasks(session: Session, tasks: list[Task], client: TestClient):
    response = client.get("/api/v1/tasks")
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == [
        task.id for task in tasks
    ]


def test_get_tasks_requires_api_key(session: Session, tasks: list[Task]):
    response = TestClient(app, follow_redirects=False).get("/api/v1/tasks")
    assert response.status_code == 401
