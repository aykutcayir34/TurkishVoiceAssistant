"""``python -m sohbet`` giriş noktası."""

from __future__ import annotations

import uvicorn

from sohbet.config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "sohbet.app:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
