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

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app import crud
from app.deps import SessionDep
from app.settings import settings
from app.templates import templates
from app.security import create_access_token

router = APIRouter(prefix="/login", include_in_schema=False)


@router.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        request,
        "login.html",
        {
            "site_name": settings.SITE_NAME,
        },
    )


# Everyone may log in: no account is needed, a login just creates an
# anonymous guest user so a session is still identified.
@router.post("/guest")
def login_guest(session: SessionDep):
    user = crud.create_guest_user(session=session)
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="access_token",
        value=create_access_token(str(user.id)),
        httponly=True,
        samesite="lax",
        path="/",
    )
    return response
