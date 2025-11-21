from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text
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
    q: str = Query(..., min_length=1),
    vocabulary_id: Optional[str] = None,
    domain_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(Concept)

    # Fuzzy search using pg_trgm
    # We use the '%' operator for similarity threshold matching if available,
    # or order by similarity.
    # For simplicity and robustness, we'll filter by ILIKE for exact/partial matches
    # OR use the similarity function for ordering.
    
    # Check if we want to use strict fuzzy matching or just sorting.
    # Let's try to use the similarity function for sorting.
    
    # Note: pg_trgm must be installed.
    # We can use `func.similarity(Concept.concept_name, q)`
    
    # Filter by query
    # We'll use a combination: ILIKE for broad matching OR similarity > threshold
    # But standard ILIKE is faster for prefixes.
    # Let's do: ILIKE %q% OR similarity > 0.3
    
    # For now, let's stick to ILIKE for filtering + Similarity for sorting to ensure performance
    # unless the user specifically asked for "fuzzy matching" which usually implies handling typos.
    # To handle typos, we need the % operator or similarity > threshold.
    
    # Using raw SQL fragment for the similarity operator '%' might be tricky with pure ORM
    # so we use `op`
    
    # query = query.filter(Concept.concept_name.op("%")(q)) # This is the similarity operator in pg_trgm
    
    # Let's use a hybrid approach:
    # 1. Exact match (highest priority)
    # 2. Starts with
    # 3. Contains
    # 4. Fuzzy (similarity)
    
    # Since we want to return a list, let's just order by similarity.
    # But we need to filter first to avoid scanning the whole table if possible.
    # If we rely PURELY on similarity, it might be slow without an index.
    # Assuming there is a GIN index on concept_name using gin_trgm_ops.
    
    # If no index, this will be slow.
    # Let's assume the user wants powerful search.
    
    query = query.filter(Concept.concept_name.op("%")(q))
    
    if vocabulary_id:
        query = query.filter(Concept.vocabulary_id == vocabulary_id)
    if domain_id:
        query = query.filter(Concept.domain_id == domain_id)
        
    query = query.order_by(func.similarity(Concept.concept_name, q).desc())
    
    results = query.limit(limit).all()
    
    # If HTMX request, return partial
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse("search_results.html", {"request": request, "results": results})
    
    # If JSON request (API), return list
    return results
