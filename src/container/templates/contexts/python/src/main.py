import importlib
import json
import os
import time
import uuid
from typing import Callable, Any

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import (
    JSONResponse,
    PlainTextResponse,
    Response as StarletteResponse,
)
from starlette.routing import Route
from starlette.middleware.cors import CORSMiddleware

from runtime_models import (
    Event,
    Context,
    Response as FnResponse,
)

HANDLER_MODULE = os.getenv("FAAS_HANDLER_MODULE", "handler")
HANDLER_SYMBOL = os.getenv("FAAS_HANDLER_SYMBOL", "handler")
FUNCTION_ID = os.getenv("FAAS_FUNCTION_ID", "unknown")


def _load_handler() -> Callable[[Event, Context], Any]:
    mod = importlib.import_module(HANDLER_MODULE)
    fn = getattr(mod, HANDLER_SYMBOL, None)
    if not callable(fn):
        raise RuntimeError(
            f"Handler symbol '{HANDLER_SYMBOL}' not callable in module '{HANDLER_MODULE}'"
        )
    return fn


handler = _load_handler()


async def invoke(request: Request) -> StarletteResponse:
    started = time.perf_counter()
    request_id = str(uuid.uuid4())
    body = await request.body()
    event = Event(
        method=request.method,
        path=request.url.path,
        headers={k.lower(): v for k, v in request.headers.items()},
        query=dict(request.query_params),
        body=body if body else None,
    )
    ctx = Context(function_id=FUNCTION_ID, request_id=request_id)
    try:
        result = handler(event, ctx)
        if isinstance(result, FnResponse):
            payload = result.body
            status = result.status_code
            headers = result.headers
        elif isinstance(result, tuple) and len(result) in (2, 3):
            payload = result[0]
            status = result[1]
            headers = result[2] if len(result) == 3 else {}
        else:
            payload = result
            status = 200
            headers = {}
        dur_ms = (time.perf_counter() - started) * 1000
        log_line = {
            "level": "info",
            "msg": "request_ok",
            "function_id": FUNCTION_ID,
            "request_id": request_id,
            "status": status,
            "duration_ms": round(dur_ms, 2),
        }
        print(json.dumps(log_line), flush=True)
        return JSONResponse(payload, status_code=status, headers=headers)
    except Exception as exc:  # noqa: BLE001
        dur_ms = (time.perf_counter() - started) * 1000
        log_line = {
            "level": "error",
            "msg": "request_error",
            "function_id": FUNCTION_ID,
            "request_id": request_id,
            "error": repr(exc),
            "duration_ms": round(dur_ms, 2),
        }
        print(json.dumps(log_line), flush=True)
        return JSONResponse({"error": "internal"}, status_code=500)


async def health(_: Request) -> StarletteResponse:
    return PlainTextResponse("OK", status_code=200)


async def ready(_: Request) -> StarletteResponse:
    # Could add async readiness checks here
    return PlainTextResponse("READY", status_code=200)


routes = [
    Route("/", invoke, methods=["GET", "POST", "PUT", "DELETE", "PATCH"]),
    Route("/healthz", health, methods=["GET"]),
    Route("/readyz", ready, methods=["GET"]),
]

app = Starlette(debug=False, routes=routes)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
