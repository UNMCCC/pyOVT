from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session, aliased
from typing import List
from ..database import get_db
from ..models import Concept, ConceptAncestor, ConceptRelationship
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
