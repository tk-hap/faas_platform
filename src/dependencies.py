from fastapi import Request
from aiohttp import ClientSession


def http_session(request: Request) -> ClientSession:
    return request.app.state.http_session
