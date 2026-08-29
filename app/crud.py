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

from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlmodel import paginate as model_paginate

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, update
from sqlmodel import Session, select

from app.models import (
    ApiKey,
    Task,
    TeleoperationKind,
    User,
    WebRTCAnswer,
    WebRTCOffer,
)
from app.security import generate_api_key, get_hex_digest


def create_api_key(*, session: Session, name: str) -> tuple[ApiKey, str]:
    key = generate_api_key()
    api_key = ApiKey(hashed_key=get_hex_digest(key), name=name)
    session.add(api_key)
    session.flush()
    return api_key, key


def find_api_key_by_hash(*, session: Session, hashed_key: str) -> ApiKey | None:
    return session.exec(select(ApiKey).where(ApiKey.hashed_key == hashed_key)).first()


def find_user(*, session, id: int) -> User | None:
    return session.get(User, id)


# Everyone may log in: a login just creates an anonymous guest user.
def create_guest_user(*, session: Session) -> User:
    user = User()
    session.add(user)
    session.flush()
    return user


def create_tasks(*, session: Session, data: list[dict]):
    tasks = [Task.model_validate(d) for d in data]
    session.add_all(tasks)
    session.flush()


def update_tasks(*, session: Session, data: list[dict]):
    for v in data:
        Task.model_validate(v)
    session.execute(update(Task), data)
    session.flush()


def find_task(*, session, id: int) -> Task | None:
    return session.get(Task, id)


def get_tasks(*, session: Session) -> list[Task]:
    return session.exec(select(Task).order_by(Task.id)).all()


def get_paginated_tasks(*, session: Session, params: Params) -> Page[Task]:
    return model_paginate(session, select(Task).order_by(Task.id), params)


def delete_stale_webrtc_offers(*, session: Session, ttl: timedelta):
    cutoff = datetime.now(timezone.utc) - ttl
    stale_offer_ids = select(WebRTCOffer.id).where(WebRTCOffer.created_at < cutoff)
    session.execute(
        delete(WebRTCAnswer).where(WebRTCAnswer.offer_id.in_(stale_offer_ids))
    )
    session.execute(delete(WebRTCOffer).where(WebRTCOffer.created_at < cutoff))
    session.flush()


def create_webrtc_offer(
    *, session: Session, task_id: int, sdp: str, kind: TeleoperationKind
) -> WebRTCOffer:
    offer = WebRTCOffer(task_id=task_id, sdp=sdp, kind=kind)
    session.add(offer)
    session.flush()
    return offer


def find_webrtc_offer(*, session: Session, id: int) -> WebRTCOffer | None:
    return session.get(WebRTCOffer, id)


def find_webrtc_answer_by_offer_id(
    *, session: Session, offer_id: int
) -> WebRTCAnswer | None:
    statement = select(WebRTCAnswer).where(WebRTCAnswer.offer_id == offer_id)
    return session.exec(statement).one_or_none()


def get_pending_webrtc_offers(
    *, session: Session, task_id: int, kind: TeleoperationKind
) -> list[WebRTCOffer]:
    statement = (
        select(WebRTCOffer)
        .outerjoin(WebRTCAnswer, WebRTCAnswer.offer_id == WebRTCOffer.id)
        .where(WebRTCOffer.task_id == task_id)
        .where(WebRTCOffer.kind == kind)
        .where(WebRTCAnswer.id == None)  # noqa: E711
        .order_by(WebRTCOffer.id)
    )
    return session.exec(statement).all()


def delete_webrtc_offer(*, session: Session, offer: WebRTCOffer):
    answer = find_webrtc_answer_by_offer_id(session=session, offer_id=offer.id)
    if answer is not None:
        session.delete(answer)
    session.delete(offer)
    session.flush()


def create_webrtc_answer(*, session: Session, offer_id: int, sdp: str) -> WebRTCAnswer:
    answer = WebRTCAnswer(offer_id=offer_id, sdp=sdp)
    session.add(answer)
    session.flush()
    return answer
