"""Pytest configuration and shared fixtures for testing the OHDSI Vocabulary Tool.

This test suite uses a live PostgreSQL database with OHDSI CDM vocabulary data.
Tests are designed to work with any standard OHDSI vocabulary database instance.
"""

from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.main import app
from app.database import get_db
from app.models import Concept, Vocabulary, Domain


# Test database configuration
# Uses the same database connection as the application
# Tests are read-only to ensure database safety
@pytest.fixture(scope="session")
def db_engine():
    """
    Create a database engine for the test session.

    Uses the same database connection as the application.
    This is a session-scoped fixture to avoid recreating the engine for each test.

    Returns:
        Engine: SQLAlchemy database engine
    """
    from app.database import engine
    return engine


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """
    Create a database session with transaction rollback for test isolation.

    Each test gets a fresh database session within a transaction that is
    rolled back after the test completes. This ensures tests don't modify
    the database and maintains isolation between tests.

    Args:
        db_engine: Database engine fixture

    Yields:
        Session: SQLAlchemy database session
    """
    # Create a connection and begin a transaction
    connection = db_engine.connect()
    transaction = connection.begin()

    # Create a session bound to this connection
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestSessionLocal()

    try:
        yield session
    finally:
        # Rollback the transaction to undo any changes
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Create a FastAPI test client with a real database session.

    The database session is wrapped in a transaction that rolls back
    after each test, ensuring test isolation.

    Args:
        db_session: Database session fixture

    Yields:
        TestClient: FastAPI test client with overridden database dependency
    """
    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass  # Session cleanup handled by db_session fixture

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def sample_concept_id(db_engine) -> int:
    """
    Get a valid concept ID from the database for testing.

    Queries the database for a standard SNOMED concept to use in tests.
    Falls back to any standard concept if SNOMED is not available.

    Args:
        db_engine: Database engine fixture

    Returns:
        int: A valid concept ID from the database
    """
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestSessionLocal()

    try:
        # Try to get a SNOMED standard concept
        concept = session.query(Concept).filter(
            Concept.vocabulary_id == "SNOMED",
            Concept.standard_concept == "S",
            Concept.domain_id == "Condition"
        ).first()

        # Fallback to any standard concept
        if not concept:
            concept = session.query(Concept).filter(
                Concept.standard_concept == "S"
            ).first()

        if not concept:
            pytest.skip("No standard concepts found in database")

        return concept.concept_id
    finally:
        session.close()


@pytest.fixture(scope="session")
def sample_vocabulary_id(db_engine) -> str:
    """
    Get a valid vocabulary ID from the database for testing.

    Args:
        db_engine: Database engine fixture

    Returns:
        str: A valid vocabulary ID from the database
    """
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestSessionLocal()

    try:
        vocab = session.query(Vocabulary).first()
        if not vocab:
            pytest.skip("No vocabularies found in database")
        return vocab.vocabulary_id
    finally:
        session.close()


@pytest.fixture(scope="session")
def sample_domain_id(db_engine) -> str:
    """
    Get a valid domain ID from the database for testing.

    Args:
        db_engine: Database engine fixture

    Returns:
        str: A valid domain ID from the database
    """
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestSessionLocal()

    try:
        domain = session.query(Domain).first()
        if not domain:
            pytest.skip("No domains found in database")
        return domain.domain_id
    finally:
        session.close()


@pytest.fixture(scope="session")
def concept_with_hierarchy(db_engine) -> int:
    """
    Get a concept ID that has both ancestors and descendants for testing hierarchy.

    Args:
        db_engine: Database engine fixture

    Returns:
        int: A concept ID that has hierarchical relationships
    """
    from app.models import ConceptAncestor

    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestSessionLocal()

    try:
        # Find a concept that appears both as ancestor and descendant
        # This ensures it has both parents and children in the hierarchy
        ancestor_concept_ids = session.query(
            ConceptAncestor.descendant_concept_id
        ).filter(
            ConceptAncestor.min_levels_of_separation > 0
        ).distinct().limit(100).all()

        for (concept_id,) in ancestor_concept_ids:
            # Check if this concept also has descendants
            has_descendants = session.query(ConceptAncestor).filter(
                ConceptAncestor.ancestor_concept_id == concept_id,
                ConceptAncestor.min_levels_of_separation == 1
            ).first()

            if has_descendants:
                # Verify the concept exists
                concept = session.query(Concept).filter(
                    Concept.concept_id == concept_id
                ).first()
                if concept:
                    return concept_id

        # Fallback to any concept with ancestors
        result = session.query(ConceptAncestor.descendant_concept_id).filter(
            ConceptAncestor.min_levels_of_separation > 0
        ).first()

        if result:
            return result[0]

        pytest.skip("No concepts with hierarchy found in database")
    finally:
        session.close()


@pytest.fixture(scope="session")
def searchable_term(db_engine) -> str:
    """
    Get a searchable term from the database that returns results.

    Args:
        db_engine: Database engine fixture

    Returns:
        str: A search term that should return results
    """
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestSessionLocal()

    try:
        # Get a concept name that we can search for
        concept = session.query(Concept).filter(
            Concept.standard_concept == "S"
        ).first()

        if not concept or not concept.concept_name:
            pytest.skip("No searchable concepts found in database")

        # Return the first word of the concept name as a search term
        words = concept.concept_name.split()
        return words[0] if words else concept.concept_name[:10]
    finally:
        session.close()


@pytest.fixture(scope="session")
def standard_concept_term(db_engine) -> str:
    """
    Get a search term that matches a standard concept (standard_concept = 'S').

    Args:
        db_engine: Database engine fixture

    Returns:
        str: A search term for a standard concept
    """
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestSessionLocal()

    try:
        # Get a standard concept
        concept = session.query(Concept).filter(
            Concept.standard_concept == "S"
        ).first()

        if not concept or not concept.concept_name:
            pytest.skip("No standard concepts found in database")

        # Return a distinctive part of the name that should uniquely identify it
        words = concept.concept_name.split()
        return words[0] if words else concept.concept_name[:10]
    finally:
        session.close()


@pytest.fixture(scope="session")
def non_standard_concept_term(db_engine) -> str:
    """
    Get a search term that matches a non-standard concept.

    Args:
        db_engine: Database engine fixture

    Returns:
        str: A search term for a non-standard concept, or None if none exist
    """
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestSessionLocal()

    try:
        # Get a non-standard concept (where standard_concept is NULL or 'C' for classification)
        concept = session.query(Concept).filter(
            Concept.standard_concept.in_(['C', None])
        ).first()

        if not concept or not concept.concept_name:
            return None  # Return None instead of skipping - some tests need this

        # Return a distinctive part of the name
        words = concept.concept_name.split()
        return words[0] if words else concept.concept_name[:10]
    finally:
        session.close()


@pytest.fixture(scope="session")
def concept_with_typo(db_engine) -> tuple[str, str]:
    """
    Get a concept name and a version with a typo for testing fuzzy matching.

    Args:
        db_engine: Database engine fixture

    Returns:
        tuple: (correct_term, typo_term) - the correct search term and a version with a typo
    """
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestSessionLocal()

    try:
        # Get a concept with a name long enough to introduce a typo
        concept = session.query(Concept).filter(
            Concept.standard_concept == "S"
        ).first()

        if not concept or not concept.concept_name or len(concept.concept_name) < 5:
            pytest.skip("No suitable concepts found for typo testing")

        correct_term = concept.concept_name.split()[0] if concept.concept_name.split() else concept.concept_name[:10]

        # Create a typo by swapping two characters or removing a character
        if len(correct_term) >= 4:
            # Remove a character from the middle
            typo_term = correct_term[:len(correct_term)//2] + correct_term[len(correct_term)//2 + 1:]
        else:
            typo_term = correct_term[:-1]  # Just remove last character

        return (correct_term, typo_term)
    finally:
        session.close()


@pytest.fixture(scope="session")
def concept_with_maps_to_relationship(db_engine) -> int:
    """
    Get a concept with 'Maps to' relationships for testing.

    Args:
        db_engine: Database engine fixture

    Returns:
        int: A concept ID that has 'Maps to' relationships
    """
    from app.models import ConceptRelationship

    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestSessionLocal()

    try:
        # Find concept with Maps to relationships
        relationship = session.query(ConceptRelationship).filter(
            ConceptRelationship.relationship_id == 'Maps to',
            ConceptRelationship.invalid_reason.is_(None)
        ).first()

        if not relationship:
            pytest.skip("No 'Maps to' relationships found")

        return relationship.concept_id_1
    finally:
        session.close()
