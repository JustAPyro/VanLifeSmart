from fastapi import APIRouter

schedule_urls = APIRouter()


@schedule_urls.get("/stuff")
async def read_users():
    return [{"username": "Rick"}, {"username": "Morty"}]
