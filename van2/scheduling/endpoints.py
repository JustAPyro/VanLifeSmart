import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from van2.scheduling.tools import scheduler, schedule_info


schedule_urls = APIRouter(prefix='/schedule')

template_path = os.path.abspath(f'{os.getenv("VLS_LOCATION")}/van2/static/templates')
templates = Jinja2Templates(directory=template_path)


@schedule_urls.get('.html', response_class=HTMLResponse)
async def schedule_page(request: Request):
    print(f'endpoints-page => {scheduler}')
    return str(len(scheduler.get_jobs()))


