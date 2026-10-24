import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from postgrest.exceptions import APIError

from src.controllers.UserController import user_controller_router

app = FastAPI(title='User accounts')
app.include_router(user_controller_router, prefix='/users', tags=['Users'])
frontend = Path(__file__).resolve().parent / 'frontend'
app.mount('/static', StaticFiles(directory=frontend), name='static')


@app.get('/', include_in_schema=False)
def index():
    return FileResponse(frontend / 'index.html')


@app.exception_handler(APIError)
async def database_error(request: Request, error: APIError):
    logging.getLogger(__name__).error('Database request failed (code %s)', error.code)
    return JSONResponse(status_code=503, content={'detail': 'Database request failed. Check the server database configuration and tables.'})
