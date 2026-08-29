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

from app.deps import may_teleoperate
from app.models import Runtime, Task, User


def _mujoco_task() -> Task:
    return Task(name="task", prompt="prompt", runtime=Runtime.MUJOCO)


def _openarm_cell_task() -> Task:
    return Task(
        name="task",
        prompt="prompt",
        runtime=Runtime.OPENARM_CELL,
        reset_docker_tag="reset/image:latest",
    )


# MuJoCo runs in simulation, so anyone may teleoperate it.
def test_may_teleoperate_mujoco_anonymous():
    assert may_teleoperate(_mujoco_task(), None)


# Every other runtime drives a real robot, so it requires logging in.
def test_may_teleoperate_openarm_cell_anonymous():
    assert not may_teleoperate(_openarm_cell_task(), None)


def test_may_teleoperate_openarm_cell_logged_in(user: User):
    assert may_teleoperate(_openarm_cell_task(), user)
