from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

endpoints = APIRouter()
template_path = os.path.abspath(f'{os.getenv("VLS_INSTALL")}/van/static/templates')
templates = Jinja2Templates(directory=template_path)


@endpoints.get('/logs.html', response_class=HTMLResponse)
async def log_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name='logs.html')


@endpoints.get('/data.html', response_class=HTMLResponse)
async def data_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name='data.html'
    )
