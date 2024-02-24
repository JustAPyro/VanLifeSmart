from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import APIRouter, Depends
import os

from .tools import get_scheduler, schedule_info
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request

schedule_urls = APIRouter(prefix='/schedule')

template_path = os.path.abspath(f'{os.getenv("VLS_LOCATION")}/van/static/templates')
templates = Jinja2Templates(directory=template_path)


@schedule_urls.get('.html', response_class=HTMLResponse)
async def schedule_page(request: Request, scheduler: AsyncIOScheduler = Depends(get_scheduler)):
    return templates.TemplateResponse(
        request=request, name="schedules.html", context={'schedules': [schedule_info(job) for job in scheduler.get_jobs()]}
    )


@schedule_urls.get('.json')
async def all_schedules(scheduler: AsyncIOScheduler = Depends(get_scheduler)):
    return [schedule_info(job) for job in scheduler.get_jobs()]


@schedule_urls.get('/{schedule_id}.json')
async def schedule(schedule_id: str, scheduler: AsyncIOScheduler = Depends(get_scheduler)):
    return schedule_info(scheduler.get_job(schedule_id))
