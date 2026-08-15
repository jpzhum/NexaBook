from __future__ import annotations

import secrets
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from .config import get_settings
from .export import export_books
from .providers import GoogleBooksProvider, OpenAIFallbackProvider, OpenLibraryProvider
from .repository import BookRepository
from .security import LoginLimiter, USER_KEY, csrf_token, verify_csrf
from .services import EnrichmentService


BASE = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE / "templates")


def create_app() -> FastAPI:
    settings = get_settings()
    repository = BookRepository(settings.database_path)
    repository.initialize()
    limiter = LoginLimiter()
    app = FastAPI(title="NexaBook", version="1.0.0", docs_url="/api/docs")
    app.add_middleware(SessionMiddleware, secret_key=settings.secret_key, https_only=settings.app_env == "production", same_site="lax")

    def context(request: Request, **values):
        return {"request": request, "csrf_token": csrf_token(request), **values}

    def require_user(request: Request):
        if settings.app_env == "development" and not settings.admin_username:
            return
        if not request.session.get(USER_KEY):
            raise HTTPException(status_code=303, headers={"Location": "/login"})

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/login", response_class=HTMLResponse)
    def login_page(request: Request):
        return templates.TemplateResponse(request, "login.html", context(request, error=None))

    @app.post("/login")
    def login(request: Request, username: str = Form(...), password: str = Form(...), csrf: str = Form(...)):
        verify_csrf(request, csrf)
        identity = request.client.host if request.client else "unknown"
        if not limiter.allowed(identity):
            return templates.TemplateResponse(request, "login.html", context(request, error="Too many attempts. Try again later."), status_code=429)
        valid = bool(settings.admin_username and settings.admin_password and secrets.compare_digest(username, settings.admin_username) and secrets.compare_digest(password, settings.admin_password))
        if not valid:
            limiter.failure(identity)
            return templates.TemplateResponse(request, "login.html", context(request, error="Invalid credentials."), status_code=401)
        limiter.success(identity)
        request.session[USER_KEY] = username
        return RedirectResponse("/", status_code=303)

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request):
        require_user(request)
        return templates.TemplateResponse(request, "index.html", context(request, books=repository.list_all(), message=None))

    @app.post("/books/enrich", response_class=HTMLResponse)
    def enrich(request: Request, isbn: str = Form(...), csrf: str = Form(...)):
        require_user(request); verify_csrf(request, csrf)
        providers = [GoogleBooksProvider(settings.google_books_api_key), OpenLibraryProvider()]
        if settings.enable_openai_fallback:
            providers.append(OpenAIFallbackProvider(settings.openai_api_key, settings.openai_model))
        try:
            book = EnrichmentService(providers).enrich(isbn)
        except ValueError as error:
            return templates.TemplateResponse(
                request, "index.html", context(request, books=repository.list_all(), message=str(error)), status_code=422
            )
        repository.add(book)
        return RedirectResponse("/", status_code=303)

    @app.post("/exports")
    def create_export(request: Request, file_type: str = Form("csv"), csrf: str = Form(...)):
        require_user(request); verify_csrf(request, csrf)
        try:
            target = export_books(repository.list_all(), settings.export_dir, file_type)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return FileResponse(target, filename=target.name)

    return app


from fastapi import HTTPException

app = create_app()
