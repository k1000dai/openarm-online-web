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

from urllib.parse import quote

from pydantic import Field, PostgresDsn, computed_field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    # These are the default values.
    # They are overridden by the values of environment variables.
    SITE_NAME: str = "OpenArm Online"

    # Deployed application version shown in the footer. Normally a Git
    # commit ID baked into the production image via the REVISION build
    # argument. Empty means the footer shows no version (e.g. in
    # development).
    REVISION: str = ""

    POSTGRES_SERVER: str = "db"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "openarm_online"
    POSTGRES_USER: str = "openarm_online"
    POSTGRES_PASSWORD: str = "openarm-online"

    SECRET_KEY: str

    API_KEY_PREFIX: str = "openarm-online-key-"
    HMAC_KEY: str

    API_KEY_HEADER_NAME: str = "X-API-KEY"

    S3_ENDPOINT_URL: str | None = None
    S3_ACCESS_KEY_ID: str | None = None
    S3_SECRET_ACCESS_KEY: str | None = None
    S3_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "openarm-online"

    # WebRTC offers older than this are stale: the browser stops polling
    # for an answer after about a minute, so nobody is waiting for them
    # anymore.
    WEBRTC_OFFER_TTL: int = Field(default=120, ge=1)  # seconds

    # Cloudflare Realtime TURN. When both are set, the teleoperation
    # pages and the runner are handed short-lived TURN credentials
    # minted through the Cloudflare API, so teleoperation also works
    # between peers that cannot connect directly. Empty or "disabled"
    # means STUN only ("disabled" stands in for empty in Secrets
    # Manager, which cannot store an empty value).
    CLOUDFLARE_TURN_KEY_ID: str = ""
    CLOUDFLARE_TURN_API_TOKEN: str = ""
    # Lifetime of the minted TURN credentials.
    TURN_CREDENTIAL_TTL: int = Field(default=86400, ge=600)  # seconds

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return str(
            PostgresDsn.build(
                scheme="postgresql+psycopg",
                username=self.POSTGRES_USER,
                password=quote(self.POSTGRES_PASSWORD, safe=""),
                host=self.POSTGRES_SERVER,
                port=self.POSTGRES_PORT,
                path=self.POSTGRES_DB,
            )
        )


settings = Settings()
