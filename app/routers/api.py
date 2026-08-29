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

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.openapi.docs import get_swagger_ui_html

from fastapi_pagination import Page

from sqlalchemy.exc import IntegrityError

from app import crud, turn
from app.deps import CurrentApiKey, PaginationDep, SessionDep
from app.models import (
    PendingWebRTCOffer,
    PendingWebRTCOffers,
    Task,
    TeleoperationKind,
    WebRTCAnswer,
    WebRTCAnswerRequest,
)
from app.settings import settings

router = APIRouter(prefix="/api/v1")


@router.get("/tasks", response_model=Page[Task])
def api_get_tasks(session: SessionDep, api_key: CurrentApiKey, params: PaginationDep):
    return crud.get_paginated_tasks(session=session, params=params)


# The kind is part of the path, mirroring the browser-facing signaling
# endpoints: a runner polls for the kinds it can answer.
@router.get(
    "/tasks/{id}/teleoperation/{kind}/offers",
    response_model=PendingWebRTCOffers,
)
def api_get_pending_webrtc_offers(
    id: int, kind: TeleoperationKind, session: SessionDep, api_key: CurrentApiKey
):
    task = crud.find_task(session=session, id=id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Task({id}) not found"
        )
    offers = crud.get_pending_webrtc_offers(session=session, task_id=id, kind=kind)
    return PendingWebRTCOffers(
        ice_servers=turn.get_ice_servers(),
        offers=[
            PendingWebRTCOffer(
                id=offer.id,
                task_id=offer.task_id,
                kind=offer.kind,
                sdp=offer.sdp,
                created_at=offer.created_at,
                runtime=task.runtime,
            )
            for offer in offers
        ],
    )


@router.post("/teleoperation/offers/{id}/answer", response_model=WebRTCAnswer)
def api_create_webrtc_answer(
    id: int, payload: WebRTCAnswerRequest, session: SessionDep, api_key: CurrentApiKey
):
    offer = crud.find_webrtc_offer(session=session, id=id)
    if offer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"WebRTC offer({id}) not found",
        )
    try:
        return crud.create_webrtc_answer(session=session, offer_id=id, sdp=payload.sdp)
    except IntegrityError as err:
        # The unique index on offer_id rejects a second answer, including
        # one from a concurrent runner.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"WebRTC offer({id}) is already answered",
        ) from err


@router.get("/reference", include_in_schema=False)
def api_reference(request: Request):
    return get_swagger_ui_html(
        openapi_url=request.app.openapi_url,
        title=f"API reference - {settings.SITE_NAME}",
    )
