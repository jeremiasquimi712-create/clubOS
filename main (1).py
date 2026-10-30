import re
import time

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from . import ai_service, mailer, services
from .database import Base, SessionLocal, engine, get_db
from .models import Postulacion

Base.metadata.create_all(engine)
with SessionLocal() as _db:
    services.seed_users(_db)
mailer.informar_estado()

app = FastAPI(title="ClubOS")
# Permite abrir index.html directamente o desde otro puerto (Live Server) y hablar con esta API local.
app.add_middleware(CORSMiddleware, allow_origin_regex=r"^(https?://(localhost|127\.0\.0\.1)(:\d+)?|null)$",
                   allow_methods=["GET", "POST"], allow_headers=["*"])
templates = Jinja2Templates(directory="app/templates")
IMG_TYPES = {"image/png", "image/jpeg"}
MAX_IMG = 8 * 1024 * 1024


async def _read_image(file: UploadFile | None):
    if file is None or not file.filename:
        return None, None
    if file.content_type not in IMG_TYPES:
        raise HTTPException(415, "Solo se aceptan imágenes .png o .jpg")
    data = await file.read()
    if len(data) > MAX_IMG:
        raise HTTPException(413, "Imagen mayor a 8 MB")
    return data, file.content_type


def _run(db: Session, text, img, mime):
    try:
        data = ai_service.extract_commitments(text, img, mime or "image/png")
    except Exception as err:
        raise HTTPException(502, f"Error de IA: {err}")
    return services.save_extraction(db, data)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/api/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    return services.dashboard(db)


@app.post("/upload/chat")
async def upload_chat(chat: UploadFile = File(...), flyer: UploadFile | None = File(None),
                      db: Session = Depends(get_db)):
    """Chat .txt (+ flyer opcional): Gemma cruza texto e imagen en una sola llamada multimodal."""
    if not chat.filename.lower().endswith(".txt"):
        raise HTTPException(415, "El historial debe ser un archivo .txt")
    text = (await chat.read()).decode("utf-8", errors="ignore")
    img, mime = await _read_image(flyer)
    return _run(db, text, img, mime)


@app.post("/upload/flyer")
async def upload_flyer(flyer: UploadFile = File(...), db: Session = Depends(get_db)):
    img, mime = await _read_image(flyer)
    return _run(db, None, img, mime)


@app.get("/api/correo/estado")
def correo_estado():
    """¿Están listos los avisos por correo? (para el indicador del header)."""
    return mailer.estado()


# ---------------- Postulaciones ("Quiero ser miembro") ----------------
class PostulacionIn(BaseModel):
    club: str = Field(max_length=40)
    nombre: str = Field(min_length=2, max_length=120)
    correo: str = Field(max_length=120)
    carrera: str = Field(min_length=2, max_length=120)
    motivacion: str = Field(min_length=5, max_length=1500)

    @field_validator("correo")
    @classmethod
    def _correo_valido(cls, v: str) -> str:
        v = v.strip()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", v):
            raise ValueError("Correo electrónico inválido")
        return v


_hits: dict[str, list[float]] = {}


def _limitar(ip: str, maximo: int = 10, ventana: int = 600):
    """Anti-spam simple en memoria: máx. 10 postulaciones cada 10 min por IP."""
    ahora = time.time()
    recientes = [t for t in _hits.get(ip, []) if ahora - t < ventana]
    if len(recientes) >= maximo:
        raise HTTPException(429, "Demasiadas postulaciones seguidas. Intenta en unos minutos.")
    _hits[ip] = recientes + [ahora]


@app.post("/api/postulaciones")
def crear_postulacion(p: PostulacionIn, request: Request, db: Session = Depends(get_db)):
    """Guarda la postulación en SQLite y avisa por correo a MAIL_TO."""
    _limitar(request.client.host if request.client else "desconocido")
    row = Postulacion(**p.model_dump())
    db.add(row)
    db.commit()

    asunto, cuerpo = mailer.formatear_postulacion(p.club, p.nombre, p.correo, p.carrera, p.motivacion)
    enviado, detalle = mailer.enviar_correo(asunto, cuerpo, reply_to=p.correo)
    row.correo_enviado = int(enviado)
    db.commit()
    return {"ok": True, "correo_enviado": enviado, "detalle_correo": detalle}
