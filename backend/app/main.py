from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse

from app.auth.router import router as auth_router
from app.events.router import router as events_router

app = FastAPI(title="RSVP System", docs_url="/api/docs", openapi_url="/api/openapi.json")


@app.middleware("http")
async def csrf_guard(request: Request, call_next):
    # Cookie auth + SameSite=Lax; additionally require a custom header on writes, which
    # cross-site forms cannot set. The frontend client always sends it.
    if request.method not in ("GET", "HEAD", "OPTIONS") and request.headers.get("x-requested-with") != "rsvp":
        return JSONResponse({"detail": "csrf"}, status_code=403)
    return await call_next(request)


app.include_router(auth_router)
app.include_router(events_router)


@app.get("/api/health")
def health():
    return {"ok": True}


STATIC = Path(__file__).resolve().parent.parent / "static"  # built frontend (Docker image only)
if STATIC.is_dir():

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        if path.startswith("api/"):
            raise HTTPException(404)
        file = (STATIC / path).resolve()
        if file.is_file() and file.is_relative_to(STATIC):
            return FileResponse(file)
        return FileResponse(STATIC / "index.html")
