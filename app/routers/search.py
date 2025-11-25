from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text, case
from typing import Optional, List
from ..database import get_db
from ..models import Concept
from ..schemas import ConceptBase
from fastapi.templating import Jinja2Templates

router = APIRouter(
    prefix="/search",
    tags=["search"]
)

templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_model=List[ConceptBase])
def search_concepts(
    request: Request,
    q: str = Query("", min_length=0),
    vocabulary_id: Optional[str] = None,
    domain_id: Optional[str] = None,
    fuzzy: Optional[str] = None,
    standard_only: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    # Early return for empty queries
    if not q or len(q.strip()) == 0:
        if request.headers.get("HX-Request"):
            return templates.TemplateResponse("search_results.html", {"request": request, "results": []})
        return []

    query = db.query(Concept)

    # Decide between fuzzy and exact matching based on checkbox
    use_fuzzy = (fuzzy == "true")

    if use_fuzzy:
        # FUZZY MATCHING: Use pg_trgm similarity (current behavior)
        query = query.filter(Concept.concept_name.op("%")(q))
        query = query.order_by(func.similarity(Concept.concept_name, q).desc())
    else:
        # EXACT/PARTIAL MATCHING: Use ILIKE for case-insensitive substring matching
        search_pattern = f"%{q}%"
        query = query.filter(Concept.concept_name.ilike(search_pattern))

        # Order by exact match first, then alphabetically
        query = query.order_by(
            case(
                (func.lower(Concept.concept_name) == q.lower(), 1),
                else_=2
            ),
            Concept.concept_name
        )

    # Apply existing filters
    if vocabulary_id:
        query = query.filter(Concept.vocabulary_id == vocabulary_id)
    if domain_id:
        query = query.filter(Concept.domain_id == domain_id)

    # Apply standard concepts filter (NEW)
    if standard_only == "true":
        query = query.filter(Concept.standard_concept == 'S')
    
    results = query.limit(limit).all()
    
    # If HTMX request, return partial
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse("search_results.html", {"request": request, "results": results})
    
    # If JSON request (API), return list
    return results
