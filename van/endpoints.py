import asyncio
import os
import timeit
from typing import Annotated

from fastapi import APIRouter, Form
from fastapi import Depends
from fastapi import Request
from fastapi.exceptions import HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.websockets import WebSocket
from geopy.exc import GeocoderUnavailable
from geopy.geocoders import Nominatim
from sqlalchemy import desc
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from van.database import get_db
from models import GPSData, TomorrowIO
from van.scheduling.tools import get_scheduler, schedule_info

endpoints = APIRouter()
template_path = os.path.abspath(f'{os.getenv("VLS_INSTALL")}/van/static/templates')
templates = Jinja2Templates(directory=template_path)


@endpoints.get('/control.html', response_class=HTMLResponse)
async def control_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name='control.html'
    )


@endpoints.get('/hub.html', response_class=HTMLResponse)
async def hub_page(request: Request, database=Depends(get_db)):
    last_weather: TomorrowIO = database.query(TomorrowIO).order_by(desc('utc_time')).first()
    last_gps = database.query(GPSData).order_by(desc('utc_time')).first()

    weather_location = f'{last_weather.gps_data.latitude}, {last_weather.gps_data.longitude}'
    geolocator = Nominatim(user_agent=__name__)

    tio_count = database.query(TomorrowIO).count()
    gps_count = database.query(GPSData).count()
    try:
        weather_location = geolocator.reverse(f'{last_weather.gps_data.latitude}, {last_weather.gps_data.longitude}',
                                              zoom=10)
    except GeocoderUnavailable:
        pass  # Just continue and use the original weather location

    weather_time = last_weather.utc_time.astimezone().strftime("%m/%d/%Y, %I:%M:%S %p")
    gps_time = last_gps.utc_time.astimezone().strftime("%m/%d/%Y, %I:%M:%S %p")

    return templates.TemplateResponse(
        request=request,
        name='hub.html',
        context={'last_weather': last_weather.as_dict(),
                 'weather_location': weather_location,
                 'weather_time': weather_time,
                 'last_gps': last_gps.as_dict(),
                 'gps_time': gps_time,
                 'tio_count': tio_count,
                 'gps_count': gps_count}
    )


@endpoints.get('/logs.html', response_class=HTMLResponse)
async def log_page(request: Request):
    log_files = os.listdir(os.getenv('VLS_DATA_PATH') + '/logs')
    log_sizes = []

    for log in log_files:
        try:
            size = os.stat(f'{os.getenv("VLS_DATA_PATH")}/logs/{log}').st_size / 1024
        except FileNotFoundError:
            size = 0

        log_sizes.append({
            'name': log,
            'size': size
        })

    context = {'title': 'log.txt', 'log_sizes': log_sizes}
    return templates.TemplateResponse(
        request=request,
        name='logs.html',
        context=context)


@endpoints.websocket('/ws/logs')
async def websocket_endpoint_log(websocket: WebSocket):
    await websocket.accept()

    # Define the process for reading logs
    async def log_reader(n=5):
        # Create an output object for each log file we can find
        log_files = os.listdir(os.getenv('VLS_DATA_PATH') + '/logs')
        output = {log: {'log': []} for log in log_files}
        for log in log_files:
            log_file = f'{os.getenv("VLS_DATA_PATH")}/logs/{log}'
            try:
                with open(log_file, 'r') as file:
                    for line in file.readlines()[-n:]:
                        html_line = f'<p>{line}</p>'
                        output[log]['log'].append(html_line)

                    file.seek(0, os.SEEK_END)
                    size = file.tell()
                    ftype = 'b'

                    if size // 1024 != 0:
                        size = size / 1024
                        ftype = 'kb'

                    if size // 1024 != 0:
                        size = size / 1024
                        ftype = 'mb'

                    if size // 1024 != 0:
                        size = size / 1024
                        ftype = 'gb'

                    output[log]['size'] = size
                    output[log]['size_type'] = ftype


            except OSError:
                with open(log_file, 'w') as file:
                    pass

        return output

    try:
        while True:
            await asyncio.sleep(1)
            logs = await log_reader(30)
            await websocket.send_json(logs)
    except Exception as e:
        raise e
    finally:
        await websocket.close()


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


@endpoints.get('/tio.html', response_class=HTMLResponse)
async def tio_page(request: Request, database: Annotated[Session, Depends(get_db)]):
    tio_query = database.query(TomorrowIO)
    all_headers = TomorrowIO.__table__.columns.keys()
    print(all_headers)
    headers = TomorrowIO.__table__.columns.keys()
    data = [row.as_list() for row in tio_query.all()]
    return templates.TemplateResponse(
        request=request,
        name='data.html',
        context={
            'data_type': 'TomorrowIO',
            'all_headers': all_headers,
            'headers': headers,
            'data': data
        }
    )


@endpoints.get('/schedule.html', response_class=HTMLResponse)
async def schedule_page(request: Request, scheduler=Depends(get_scheduler)):
    jobs = scheduler.get_jobs()
    return templates.TemplateResponse(
        request=request,
        name="schedule.html",
        context={'schedules': [schedule_info(job) for job in jobs]}
    )


@endpoints.post('/schedule.json', response_class=HTMLResponse)
async def schedule_json(request: Request,
                        scheduler=Depends(get_scheduler),
                        scheduler_id=Annotated[str, Form()],
                        new_interval=Annotated[str, Form()]):
    jobs = scheduler.get_jobs()
    return templates.TemplateResponse(
        request=request,
        name="schedule.html",
        context={'schedules': [schedule_info(job) for job in jobs]}
    )


@endpoints.post('schedule.json', response_class=JSONResponse)
async def change_schedule_json(request: Request):
    print(request)
    return 'hi'


# This is imported and loaded in the main server.py code as an exception handler
async def not_found_exception_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse(
        request=request,
        status_code=404,
        name='404.html'
    )
