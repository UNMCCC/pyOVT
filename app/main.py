from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from .database import get_db, engine, Base
from .routers import search, concept
from .models import Vocabulary, Domain

# Create tables if they don't exist (though we expect them to exist in CDM)
# Base.metadata.create_all(bind=engine) 

app = FastAPI(
    title="OHDSI Vocabulary Tool",
    description="A tool to browse and search OHDSI standardized vocabularies.",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(search.router)
app.include_router(concept.router)

templates = Jinja2Templates(directory="app/templates")

@app.get("/")
def index(request: Request, db: Session = Depends(get_db)):
    # Fetch vocabularies and domains for filters
    vocabularies = db.query(Vocabulary).order_by(Vocabulary.vocabulary_id).all()
    domains = db.query(Domain).order_by(Domain.domain_id).all()
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "vocabularies": vocabularies,
        "domains": domains
    })
