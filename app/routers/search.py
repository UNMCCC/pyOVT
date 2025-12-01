from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text, case, or_
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

    # Start with base query
    query = db.query(Concept)

    # Decide between fuzzy and exact matching
    use_fuzzy = (fuzzy == "true")
    q_lower = q.lower()

    if use_fuzzy:
        # FUZZY MODE: Only fuzzy match on concept_name
        # Use exact matching for concept_code (more precise)
        query = query.filter(
            or_(
                Concept.concept_name.op("%")(q),
                Concept.concept_code.ilike(f"%{q}%")
            )
        )

        # Calculate similarity for name only
        name_similarity = func.similarity(Concept.concept_name, q)

        # Order by: exact code match first, then name similarity
        query = query.order_by(
            case(
                (func.lower(Concept.concept_code) == q_lower, 1),
                else_=0
            ).desc(),
            name_similarity.desc(),
            Concept.concept_name
        )

    else:
        # EXACT/PARTIAL MODE: Search both fields with ILIKE
        search_pattern = f"%{q}%"

        query = query.filter(
            or_(
                Concept.concept_name.ilike(search_pattern),
                Concept.concept_code.ilike(search_pattern)
            )
        )

        # Smart ranking algorithm:
        # 1. Exact code match (highest priority)
        # 2. Exact name match
        # 3. Code starts with query
        # 4. Name starts with query
        # 5. Standard concepts vs non-standard
        # 6. Alphabetical by name

        query = query.order_by(
            case((func.lower(Concept.concept_code) == q_lower, 1), else_=0).desc(),
            case((func.lower(Concept.concept_name) == q_lower, 1), else_=0).desc(),
            case((func.lower(Concept.concept_code).startswith(q_lower), 1), else_=0).desc(),
            case((func.lower(Concept.concept_name).startswith(q_lower), 1), else_=0).desc(),
            case((Concept.standard_concept == 'S', 1), else_=0).desc(),
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
    
    # If HTMX request, return partial with query for match detection
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse("search_results.html", {
            "request": request,
            "results": results,
            "query": q,  # Pass query to template for match type detection
            "limit": limit  # Pass limit to template for display
        })

    # If JSON request (API), return list
    return results
