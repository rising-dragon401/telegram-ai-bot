from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# Import routers

from routers import tg_settting
from routers import tg_messaging
from routers import wa_messaging

app = FastAPI()

# TODO: add specific origins here
origins = [ "*" ]

app.add_middleware(
  CORSMiddleware,
  allow_origins=origins,
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

# Add routers to app
app.include_router(tg_messaging.router)
app.include_router(tg_settting.router)
app.include_router(wa_messaging.router)

# Root route
@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
	exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
	print(f"{request}: {exc_str}")
	content = {'status_code': 10422, 'message': exc_str, 'data': None}
	return JSONResponse(content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)