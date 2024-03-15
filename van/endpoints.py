import timeit
from typing import Annotated

from fastapi import APIRouter, Form
from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session
from database import get_db
from fastapi import Depends
from sqlalchemy.sql import text
from models import GPSData
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


@endpoints.post('/sql.json', response_class=JSONResponse)
async def sql_json(request: Request,
                   sql_query: Annotated[str, Form()],
                   database: Annotated[Session, Depends(get_db)]):
    # TODO: Add some safety here
    start = timeit.default_timer()
    statement = text(sql_query)
    results = database.execute(statement)
    headings = [key for key in results._metadata.keys]
    data = [[item for item in row] for row in results]
    total_time = timeit.default_timer() - start
    return JSONResponse(content={
        'insert': {
            'headings': headings,
            'data': data,
        },
        'rows': len(data),
        'time': total_time
    })


@endpoints.get('/gps.html', response_class=HTMLResponse)
async def gps_page(request: Request, database: Annotated[Session, Depends(get_db)]):
    gps_query = database.query(GPSData)
    all_headers = GPSData.__table__.columns.keys()
    headers = GPSData.__table__.columns.keys()
    data = [row.as_list() for row in gps_query.all()]
    return templates.TemplateResponse(
        request=request,
        name='data.html',
        context={
            'data_type': 'GPS',
            'all_headers': all_headers,
            'headers': headers,
            'data': data
        }
    )


# This is imported and loaded in the main server.py code as an exception handler
async def not_found_exception_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse(
        request=request,
        status_code=404,
        name='404.html'
    )
