from typing import Annotated

from fastapi import APIRouter, Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session
from database import get_db
from fastapi import Depends
import os

endpoints = APIRouter()
template_path = os.path.abspath(f'{os.getenv("VLS_INSTALL")}/van/static/templates')
templates = Jinja2Templates(directory=template_path)


@endpoints.get('/logs.html', response_class=HTMLResponse)
async def log_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name='logs.html')


@endpoints.get('/sql.html', response_class=HTMLResponse)
async def sql_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name='sql.html'
    )


@endpoints.post('/sql.html', response_class=HTMLResponse)
async def post_sql_page(request: Request, sql_query: Annotated[str, Form()],
                        database: Annotated[Session, Depends(get_db)]):
    print(sql_query)
    print(database)
    return templates.TemplateResponse(
        request=request,
        name='sql.html'
    )


# This is imported and loaded in the main server.py code as an exception handler
async def not_found_exception_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse(
        request=request,
        name='404.html'
    )
