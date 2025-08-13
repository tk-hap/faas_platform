from fastapi import Request, Depends
from aiohttp import ClientSession
from typing import Annotated


def http_session(request: Request) -> ClientSession:
    return request.app.state.http_session


HttpSession = Annotated[ClientSession, Depends(http_session)]
