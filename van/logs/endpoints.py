from fastapi import APIRouter, Request

log_urls = APIRouter(prefix='/logs')


@log_urls.get('/hi')
async def schedule_page(request: Request):
    return 'hello'