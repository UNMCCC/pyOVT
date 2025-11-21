from pydantic import BaseModel
from typing import Optional, List
from datetime import date

class ConceptBase(BaseModel):
    concept_id: int
    concept_name: str
    domain_id: str
    vocabulary_id: str
    concept_class_id: str
    standard_concept: Optional[str] = None
    concept_code: str
    valid_start_date: Optional[date] = None
    valid_end_date: Optional[date] = None
    invalid_reason: Optional[str] = None

    class Config:
        from_attributes = True

class ConceptDetail(ConceptBase):
    pass

class ConceptAncestor(BaseModel):
    ancestor_concept_id: int
    min_levels_of_separation: int
    max_levels_of_separation: int
    ancestor_name: Optional[str] = None
    ancestor_vocabulary_id: Optional[str] = None
    ancestor_concept_code: Optional[str] = None

class ConceptDescendant(BaseModel):
    descendant_concept_id: int
    min_levels_of_separation: int
    max_levels_of_separation: int
    descendant_name: Optional[str] = None
    descendant_vocabulary_id: Optional[str] = None
    descendant_concept_code: Optional[str] = None

class SearchResult(BaseModel):
    total: int
    results: List[ConceptBase]
