from fastapi import APIRouter, Depends, Request, HTTPException, Query
from sqlalchemy.orm import Session, aliased
from typing import List
from ..database import get_db
from ..models import Concept, ConceptAncestor, ConceptRelationship, Relationship
from ..schemas import ConceptDetail
from fastapi.templating import Jinja2Templates

router = APIRouter(
    prefix="/concept",
    tags=["concept"]
)

templates = Jinja2Templates(directory="app/templates")

@router.get("/{concept_id}", response_model=ConceptDetail)
def get_concept(
    request: Request,
    concept_id: int,
    db: Session = Depends(get_db)
):
    concept = db.query(Concept).filter(Concept.concept_id == concept_id).first()
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")
    
    # Get Ancestors
    # Join ConceptAncestor with Concept to get names
    AncestorConcept = aliased(Concept)
    ancestors = db.query(
        ConceptAncestor,
        AncestorConcept.concept_name,
        AncestorConcept.vocabulary_id,
        AncestorConcept.concept_code
    ).join(
        AncestorConcept, ConceptAncestor.ancestor_concept_id == AncestorConcept.concept_id
    ).filter(
        ConceptAncestor.descendant_concept_id == concept_id,
        ConceptAncestor.ancestor_concept_id != concept_id # Exclude self
    ).order_by(
        ConceptAncestor.min_levels_of_separation
    ).all()
    
    # Get Descendants (limit to direct children or top 50 to avoid explosion)
    DescendantConcept = aliased(Concept)
    descendants = db.query(
        ConceptAncestor,
        DescendantConcept.concept_name,
        DescendantConcept.vocabulary_id,
        DescendantConcept.concept_code
    ).join(
        DescendantConcept, ConceptAncestor.descendant_concept_id == DescendantConcept.concept_id
    ).filter(
        ConceptAncestor.ancestor_concept_id == concept_id,
        ConceptAncestor.descendant_concept_id != concept_id, # Exclude self
        ConceptAncestor.min_levels_of_separation == 1 # Direct children only for now
    ).all()
    
    # Get Relationships
    relationships = db.query(ConceptRelationship).filter(
        ConceptRelationship.concept_id_1 == concept_id
    ).all()

    context = {
        "request": request,
        "concept": concept,
        "ancestors": ancestors,
        "descendants": descendants,
        "relationships": relationships
    }

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse("concept_detail.html", context)

    return templates.TemplateResponse("concept_detail.html", context) # Always return HTML for this route for now, or separate API


@router.get("/{concept_id}/similar")
def find_similar_concepts(
    request: Request,
    concept_id: int,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Find concepts related via 'Maps to' and 'Mapped from' relationships."""
    # Alias for the related concept
    RelatedConcept = aliased(Concept)

    # Query relationships where current concept is source (concept_id_1)
    # Focus on 'Maps to' relationships
    outgoing = db.query(
        ConceptRelationship.relationship_id,
        RelatedConcept.concept_id,
        RelatedConcept.concept_name,
        RelatedConcept.vocabulary_id,
        RelatedConcept.concept_code,
        RelatedConcept.standard_concept
    ).join(
        RelatedConcept, ConceptRelationship.concept_id_2 == RelatedConcept.concept_id
    ).join(
        Relationship, ConceptRelationship.relationship_id == Relationship.relationship_id
    ).filter(
        ConceptRelationship.concept_id_1 == concept_id,
        ConceptRelationship.relationship_id.in_(['Maps to', 'Mapped from']),
        ConceptRelationship.invalid_reason.is_(None)  # Only valid relationships
    ).limit(limit).all()

    # Query relationships where current concept is target (concept_id_2)
    # Get reverse 'Maps to' (i.e., 'Mapped from')
    incoming = db.query(
        ConceptRelationship.relationship_id,
        RelatedConcept.concept_id,
        RelatedConcept.concept_name,
        RelatedConcept.vocabulary_id,
        RelatedConcept.concept_code,
        RelatedConcept.standard_concept
    ).join(
        RelatedConcept, ConceptRelationship.concept_id_1 == RelatedConcept.concept_id
    ).join(
        Relationship, ConceptRelationship.relationship_id == Relationship.relationship_id
    ).filter(
        ConceptRelationship.concept_id_2 == concept_id,
        ConceptRelationship.relationship_id.in_(['Maps to', 'Mapped from']),
        ConceptRelationship.invalid_reason.is_(None)
    ).limit(limit).all()

    # Combine results and deduplicate by concept_id
    # Use a dict to keep only unique concepts (keyed by concept_id)
    seen_concepts = {}
    for row in outgoing + incoming:
        concept_id_key = row[1]  # concept_id is at index 1
        if concept_id_key not in seen_concepts:
            seen_concepts[concept_id_key] = row

    # Convert back to list and apply limit
    related_concepts = list(seen_concepts.values())[:limit]

    context = {
        "request": request,
        "related_concepts": related_concepts,
        "concept_id": concept_id
    }

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse("similar_concepts.html", context)

    # For API requests, return structured data
    return [{"relationship_id": r[0], "concept_id": r[1], "concept_name": r[2],
             "vocabulary_id": r[3], "concept_code": r[4], "standard_concept": r[5]}
            for r in related_concepts]


@router.get("/{concept_id}/descendants/search")
def search_descendants(
    request: Request,
    concept_id: int,
    q: str = Query("", min_length=0),
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Search within descendants of a concept."""
    # Early return for empty queries
    if not q or len(q.strip()) == 0:
        if request.headers.get("HX-Request"):
            return templates.TemplateResponse("hierarchy_search_results.html", {
                "request": request,
                "results": [],
                "query": q
            })
        return []

    # Get all descendant concept IDs (direct children only - level 1)
    # First get the IDs as a list
    descendant_ids = [row[0] for row in db.query(ConceptAncestor.descendant_concept_id).filter(
        ConceptAncestor.ancestor_concept_id == concept_id,
        ConceptAncestor.min_levels_of_separation == 1  # Direct children only
    ).all()]

    # If no descendants found, return empty results
    if not descendant_ids:
        if request.headers.get("HX-Request"):
            return templates.TemplateResponse("hierarchy_search_results.html", {
                "request": request,
                "results": [],
                "query": q,
                "ancestor_id": concept_id
            })
        return []

    # Search within those descendants
    DescendantConcept = aliased(Concept)
    results = db.query(
        DescendantConcept.concept_id,
        DescendantConcept.concept_name,
        DescendantConcept.vocabulary_id,
        DescendantConcept.domain_id,
        DescendantConcept.concept_code,
        DescendantConcept.standard_concept
    ).filter(
        DescendantConcept.concept_id.in_(descendant_ids),
        DescendantConcept.concept_name.ilike(f"%{q}%")
    ).limit(limit).all()

    context = {
        "request": request,
        "results": results,
        "query": q,
        "ancestor_id": concept_id
    }

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse("hierarchy_search_results.html", context)

    return [{"concept_id": r[0], "concept_name": r[1], "vocabulary_id": r[2],
             "domain_id": r[3], "concept_code": r[4], "standard_concept": r[5]}
            for r in results]
