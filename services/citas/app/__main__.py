import logging
import os

import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

uvicorn.run(
    "app.main:app",
    host="0.0.0.0",
    port=int(os.environ.get("PORT", "8080")),
    log_level="info",
)
