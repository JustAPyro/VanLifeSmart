import os
from fastapi import APIRouter, Request, Response

log_urls = APIRouter(prefix='/logs')


@log_urls.get('/hi')
async def schedule_page(request: Request):
    return 'hello'


@log_urls.delete('/{log_name}.json')
async def delete_log(log_name: str):
    # TODO: AUTHENTICATION VALIDATION
    try:
        open(f'{os.getenv("VLS_LOCATION")}/van/logs/{log_name}.txt', 'w').close()
        return Response(status_code=200)
    except OSError:
        return Response(status_code=400)
