import uvicorn
if __name__ == '__main__':
    uvicorn.run('van.server:server', host='localhost')
