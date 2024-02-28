import asyncio
import os
from fastapi import APIRouter, Request, Response, WebSocket
from fastapi.templating import Jinja2Templates

log_urls = APIRouter(prefix='/logs')
template_path = os.path.abspath(f'{os.getenv("VLS_LOCATION")}/van/static/templates')
templates = Jinja2Templates(directory=template_path)


async def log_reader(n=5):
    log_colors = {
        'log': {
            '[SKIP_REPORT]': '<p class="text-danger">',
            '[OKAY_REPORT]': '<p class="text-success">'
        }
    }
    logs = ['log', 'APScheduler', 'Webserver']
    output = {log: {'log': []} for log in logs}

    for log in logs:
        log_file = f'{os.getenv("VLS_LOCATION")}/van/logs/{log}.txt'
        coloring = log_colors.get(log)
        try:
            with open(log_file, 'r') as file:
                for line in file.readlines()[-n:]:
                    text = '<p>'
                    if coloring:
                        for trigger_text, tag in coloring.items():
                            if trigger_text in line:
                                text = tag
                    text = text + f'{line}</p><br/>'
                    output[log]['log'].append(text)

                file.seek(0, os.SEEK_END)
                output[log]['size'] = file.tell()
        except OSError:
            with open(log_file, 'w') as file:
                pass

    return output



@log_urls.get('/hi')
async def schedule_page(request: Request):
    return 'hello'


@log_urls.websocket('/ws/logs')
async def websocket_endpoint_log(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            await asyncio.sleep(1)
            logs = await log_reader(30)
            await websocket.send_json(logs)
    except Exception as e:
        raise e
    finally:
        await websocket.close()


@log_urls.get('.html')
async def get_log(request: Request):
    logs = ['log', 'APScheduler', 'Webserver']
    log_sizes = []

    for log in logs:
        try:
            size = os.stat(f'{os.getenv("VLS_LOCATION")}/van/logs/{log}.txt').st_size / 1024
        except FileNotFoundError:
            size = 0

        log_sizes.append({
            'name': log,
            'size': size
        })

    context = {'title': 'log.txt', 'log_sizes': log_sizes}
    return templates.TemplateResponse('log_viewer.html', {'request': request, 'context': context})


@log_urls.delete('/{log_name}.json')
async def delete_log(log_name: str):
    # TODO: AUTHENTICATION VALIDATION
    try:
        open(f'{os.getenv("VLS_LOCATION")}/van/logs/{log_name}.txt', 'w').close()
        return Response(status_code=200)
    except OSError:
        return Response(status_code=400)
