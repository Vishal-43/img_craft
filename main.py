from typing import Union
import re
from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.status import HTTP_303_SEE_OTHER

# Assuming the corrected database class is in database.py
# Import the new PasswordManager

# --- Configuration and Initialization ---

SECRET_KEY = "@tuzi$layki$nahi$bhava@" # Replace with a strong, randomly generated key in production


app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
# Assuming 'static' directory exists in the same location as your website.py
app.mount("/static", StaticFiles(directory="static"), name="static")

# Assuming 'templates' directory exists in the same location as your website.py
templates = Jinja2Templates(directory="templates")




