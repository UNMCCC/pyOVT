from sqlalchemy import Column, Integer, String, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base

class Concept(Base):
    __tablename__ = "concept"

    concept_id = Column(Integer, primary_key=True, index=True)
    concept_name = Column(String, index=True)
    domain_id = Column(String, ForeignKey("domain.domain_id"), index=True)
    vocabulary_id = Column(String, ForeignKey("vocabulary.vocabulary_id"), index=True)
    concept_class_id = Column(String, ForeignKey("concept_class.concept_class_id"), index=True)
    standard_concept = Column(String)
    concept_code = Column(String, index=True)
    valid_start_date = Column(Date)
    valid_end_date = Column(Date)
    invalid_reason = Column(String)

    # Relationships
    domain = relationship("Domain")
    vocabulary = relationship("Vocabulary")
    concept_class = relationship("ConceptClass")

class Vocabulary(Base):
    __tablename__ = "vocabulary"

    vocabulary_id = Column(String, primary_key=True, index=True)
    vocabulary_name = Column(String)
    vocabulary_reference = Column(String)
    vocabulary_version = Column(String)
    vocabulary_concept_id = Column(Integer)

class Domain(Base):
    __tablename__ = "domain"

    domain_id = Column(String, primary_key=True, index=True)
    domain_name = Column(String)
    domain_concept_id = Column(Integer)

class ConceptClass(Base):
    __tablename__ = "concept_class"

    concept_class_id = Column(String, primary_key=True, index=True)
    concept_class_name = Column(String)
    concept_class_concept_id = Column(Integer)

class ConceptRelationship(Base):
    __tablename__ = "concept_relationship"

    concept_id_1 = Column(Integer, ForeignKey("concept.concept_id"), primary_key=True)
    concept_id_2 = Column(Integer, ForeignKey("concept.concept_id"), primary_key=True)
    relationship_id = Column(String, ForeignKey("relationship.relationship_id"), primary_key=True)
    valid_start_date = Column(Date)
    valid_end_date = Column(Date)
    invalid_reason = Column(String)

    # Relationships
    concept_1 = relationship("Concept", foreign_keys=[concept_id_1])
    concept_2 = relationship("Concept", foreign_keys=[concept_id_2])
    relationship = relationship("Relationship")

class Relationship(Base):
    __tablename__ = "relationship"
    
    relationship_id = Column(String, primary_key=True)
    relationship_name = Column(String)
    is_hierarchical = Column(String)
    defines_ancestry = Column(String)
    reverse_relationship_id = Column(String)
    relationship_concept_id = Column(Integer)

class ConceptAncestor(Base):
    __tablename__ = "concept_ancestor"

    ancestor_concept_id = Column(Integer, ForeignKey("concept.concept_id"), primary_key=True)
    descendant_concept_id = Column(Integer, ForeignKey("concept.concept_id"), primary_key=True)
    min_levels_of_separation = Column(Integer)
    max_levels_of_separation = Column(Integer)

    # Relationships
    ancestor = relationship("Concept", foreign_keys=[ancestor_concept_id])
    descendant = relationship("Concept", foreign_keys=[descendant_concept_id])
