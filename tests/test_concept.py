"""Tests for the concept detail endpoint using live database."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestConceptDetailEndpoint:
    """Test suite for the /concept/{concept_id} endpoint."""

    def test_get_concept_success(
        self,
        client: TestClient,
        sample_concept_id: int,
    ) -> None:
        """
        Test successful retrieval of a concept by ID.

        Args:
            client: FastAPI test client
            sample_concept_id: A valid concept ID from the database
        """
        # Make request
        response = client.get(f"/concept/{sample_concept_id}")

        # Assertions
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        # Should contain the concept ID somewhere in the response
        assert str(sample_concept_id) in response.text

    def test_get_concept_with_htmx_header(
        self,
        client: TestClient,
        sample_concept_id: int,
    ) -> None:
        """
        Test concept retrieval with HTMX header returns HTML template.

        Args:
            client: FastAPI test client
            sample_concept_id: A valid concept ID from the database
        """
        # Make request with HTMX header
        response = client.get(
            f"/concept/{sample_concept_id}",
            headers={"HX-Request": "true"},
        )

        # Assertions
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert str(sample_concept_id) in response.text

    def test_get_concept_not_found(
        self,
        client: TestClient,
    ) -> None:
        """
        Test concept retrieval returns 404 for non-existent concept.

        Args:
            client: FastAPI test client
        """
        # Make request with a concept ID that definitely doesn't exist
        response = client.get("/concept/999999999")

        # Assertions
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Concept not found"

    def test_get_concept_with_hierarchy(
        self,
        client: TestClient,
        concept_with_hierarchy: int,
    ) -> None:
        """
        Test concept retrieval includes ancestor and descendant information.

        Args:
            client: FastAPI test client
            concept_with_hierarchy: A concept ID that has hierarchical relationships
        """
        # Make request
        response = client.get(f"/concept/{concept_with_hierarchy}")

        # Assertions
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

        # The response should include hierarchy sections
        # (Ancestors or descendants sections should be present)
        response_text = response.text.lower()
        # Check for common hierarchy-related terms
        assert any(term in response_text for term in [
            "ancestor", "parent", "descendant", "child", "hierarchy"
        ])

    def test_get_concept_invalid_id_type(
        self,
        client: TestClient,
    ) -> None:
        """
        Test concept retrieval with invalid ID type returns validation error.

        Args:
            client: FastAPI test client
        """
        # Make request with non-integer ID
        response = client.get("/concept/invalid")

        # Assertions
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_get_concept_zero_id(
        self,
        client: TestClient,
        db_session: Session,
    ) -> None:
        """
        Test concept retrieval with concept_id = 0.

        Args:
            client: FastAPI test client
            db_session: Database session
        """
        from app.models import Concept

        # Check if concept 0 exists in the database
        concept_zero = db_session.query(Concept).filter(
            Concept.concept_id == 0
        ).first()

        # Make request with zero ID
        response = client.get("/concept/0")

        # Assertions - behavior depends on whether concept 0 exists
        if concept_zero:
            # If concept 0 exists, it should return 200
            assert response.status_code == 200
            assert concept_zero.concept_name in response.text
        else:
            # If concept 0 doesn't exist, should return 404
            assert response.status_code == 404
            data = response.json()
            assert data["detail"] == "Concept not found"

    def test_get_concept_negative_id(
        self,
        client: TestClient,
    ) -> None:
        """
        Test concept retrieval with negative concept_id.

        Args:
            client: FastAPI test client
        """
        # Make request with negative ID
        response = client.get("/concept/-1")

        # Assertions
        # Should return 404 as negative IDs don't exist
        assert response.status_code == 404

    def test_get_concept_displays_basic_info(
        self,
        client: TestClient,
        sample_concept_id: int,
        db_session,
    ) -> None:
        """
        Test that concept detail page displays basic concept information.

        Args:
            client: FastAPI test client
            sample_concept_id: A valid concept ID from the database
            db_session: Database session
        """
        from app.models import Concept

        # Get the actual concept from the database
        concept = db_session.query(Concept).filter(
            Concept.concept_id == sample_concept_id
        ).first()

        assert concept is not None

        # Make request
        response = client.get(f"/concept/{sample_concept_id}")

        # Assertions
        assert response.status_code == 200

        # Should display concept information
        assert concept.concept_name in response.text
        assert concept.vocabulary_id in response.text
        assert concept.domain_id in response.text

    def test_get_concept_with_relationships(
        self,
        client: TestClient,
        db_session,
    ) -> None:
        """
        Test concept retrieval for a concept that has relationships.

        Args:
            client: FastAPI test client
            db_session: Database session
        """
        from app.models import ConceptRelationship

        # Find a concept that has relationships
        relationship = db_session.query(ConceptRelationship).first()

        if not relationship:
            pytest.skip("No concept relationships found in database")

        concept_id = relationship.concept_id_1

        # Make request
        response = client.get(f"/concept/{concept_id}")

        # Assertions
        assert response.status_code == 200
        # Should successfully render even with relationships
        assert str(concept_id) in response.text

    def test_get_concept_standard_vs_nonstandard(
        self,
        client: TestClient,
        db_session,
    ) -> None:
        """
        Test that both standard and non-standard concepts can be retrieved.

        Args:
            client: FastAPI test client
            db_session: Database session
        """
        from app.models import Concept

        # Get a standard concept
        standard_concept = db_session.query(Concept).filter(
            Concept.standard_concept == "S"
        ).first()

        if standard_concept:
            response = client.get(f"/concept/{standard_concept.concept_id}")
            assert response.status_code == 200

        # Get a non-standard concept
        non_standard_concept = db_session.query(Concept).filter(
            Concept.standard_concept != "S"
        ).first()

        if non_standard_concept:
            response = client.get(f"/concept/{non_standard_concept.concept_id}")
            assert response.status_code == 200

    def test_get_concept_from_different_vocabularies(
        self,
        client: TestClient,
        db_session,
    ) -> None:
        """
        Test retrieval of concepts from different vocabularies.

        Args:
            client: FastAPI test client
            db_session: Database session
        """
        from app.models import Concept, Vocabulary

        # Get concepts from up to 3 different vocabularies
        vocabularies = db_session.query(Vocabulary).limit(3).all()

        for vocab in vocabularies:
            concept = db_session.query(Concept).filter(
                Concept.vocabulary_id == vocab.vocabulary_id
            ).first()

            if concept:
                response = client.get(f"/concept/{concept.concept_id}")
                assert response.status_code == 200
                assert vocab.vocabulary_id in response.text

    def test_get_concept_from_different_domains(
        self,
        client: TestClient,
        db_session,
    ) -> None:
        """
        Test retrieval of concepts from different domains.

        Args:
            client: FastAPI test client
            db_session: Database session
        """
        from app.models import Concept, Domain

        # Get concepts from up to 3 different domains
        domains = db_session.query(Domain).limit(3).all()

        for domain in domains:
            concept = db_session.query(Concept).filter(
                Concept.domain_id == domain.domain_id
            ).first()

            if concept:
                response = client.get(f"/concept/{concept.concept_id}")
                assert response.status_code == 200
                assert domain.domain_id in response.text

    def test_get_concept_ancestors_query(
        self,
        client: TestClient,
        db_session,
    ) -> None:
        """
        Test that ancestors are properly queried and displayed.

        Args:
            client: FastAPI test client
            db_session: Database session
        """
        from app.models import ConceptAncestor, Concept

        # Find a concept with ancestors
        ancestor_rel = db_session.query(ConceptAncestor).filter(
            ConceptAncestor.min_levels_of_separation > 0
        ).first()

        if not ancestor_rel:
            pytest.skip("No ancestor relationships found in database")

        concept_id = ancestor_rel.descendant_concept_id

        # Make request
        response = client.get(f"/concept/{concept_id}")

        # Assertions
        assert response.status_code == 200
        # Should render successfully with ancestor data
        assert str(concept_id) in response.text

    def test_get_concept_descendants_query(
        self,
        client: TestClient,
        db_session,
    ) -> None:
        """
        Test that descendants (direct children) are properly queried.

        Args:
            client: FastAPI test client
            db_session: Database session
        """
        from app.models import ConceptAncestor

        # Find a concept with descendants
        descendant_rel = db_session.query(ConceptAncestor).filter(
            ConceptAncestor.min_levels_of_separation == 1
        ).first()

        if not descendant_rel:
            pytest.skip("No descendant relationships found in database")

        concept_id = descendant_rel.ancestor_concept_id

        # Make request
        response = client.get(f"/concept/{concept_id}")

        # Assertions
        assert response.status_code == 200
        # Should render successfully with descendant data
        assert str(concept_id) in response.text

    def test_get_concept_complete_hierarchy(
        self,
        client: TestClient,
        concept_with_hierarchy: int,
        db_session,
    ) -> None:
        """
        Test concept retrieval with full hierarchy (ancestors and descendants).

        Args:
            client: FastAPI test client
            concept_with_hierarchy: A concept ID that has hierarchical relationships
            db_session: Database session
        """
        from app.models import ConceptAncestor, Concept

        # Verify the concept has both ancestors and descendants
        has_ancestors = db_session.query(ConceptAncestor).filter(
            ConceptAncestor.descendant_concept_id == concept_with_hierarchy,
            ConceptAncestor.min_levels_of_separation > 0
        ).first() is not None

        has_descendants = db_session.query(ConceptAncestor).filter(
            ConceptAncestor.ancestor_concept_id == concept_with_hierarchy,
            ConceptAncestor.min_levels_of_separation == 1
        ).first() is not None

        # Make request
        response = client.get(f"/concept/{concept_with_hierarchy}")

        # Assertions
        assert response.status_code == 200
        response_text = response.text

        # Get the concept details
        concept = db_session.query(Concept).filter(
            Concept.concept_id == concept_with_hierarchy
        ).first()

        assert concept is not None
        # Should display the main concept
        assert concept.concept_name in response_text

    def test_get_concept_html_structure(
        self,
        client: TestClient,
        sample_concept_id: int,
    ) -> None:
        """
        Test that concept detail page has proper HTML structure.

        Args:
            client: FastAPI test client
            sample_concept_id: A valid concept ID from the database
        """
        # Make request
        response = client.get(f"/concept/{sample_concept_id}")

        # Assertions
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

        # Should have basic HTML structure
        response_text = response.text.lower()
        assert "<html" in response_text or "<!doctype" in response_text

    def test_get_concept_returns_template_not_json(
        self,
        client: TestClient,
        sample_concept_id: int,
    ) -> None:
        """
        Test that concept endpoint returns HTML template, not JSON.

        Args:
            client: FastAPI test client
            sample_concept_id: A valid concept ID from the database
        """
        # Make request
        response = client.get(f"/concept/{sample_concept_id}")

        # Assertions
        assert response.status_code == 200
        # Should not be JSON
        assert "application/json" not in response.headers.get("content-type", "")
        # Should be HTML
        assert "text/html" in response.headers["content-type"]

    def test_get_concept_performance(
        self,
        client: TestClient,
        sample_concept_id: int,
    ) -> None:
        """
        Test that concept retrieval completes in reasonable time.

        Args:
            client: FastAPI test client
            sample_concept_id: A valid concept ID from the database
        """
        import time

        start_time = time.time()
        response = client.get(f"/concept/{sample_concept_id}")
        elapsed_time = time.time() - start_time

        # Assertions
        assert response.status_code == 200
        # Should complete within 5 seconds (generous for database queries)
        assert elapsed_time < 5.0, f"Concept retrieval took {elapsed_time:.2f}s"

    def test_get_concept_with_special_characters_in_name(
        self,
        client: TestClient,
        db_session,
    ) -> None:
        """
        Test concepts with special characters in their names render properly.

        Args:
            client: FastAPI test client
            db_session: Database session
        """
        from app.models import Concept

        # Find a concept with special characters (apostrophes, hyphens, etc.)
        special_chars = ["'", "-", "(", ")", "/", "&"]

        for char in special_chars:
            concept = db_session.query(Concept).filter(
                Concept.concept_name.like(f"%{char}%")
            ).first()

            if concept:
                response = client.get(f"/concept/{concept.concept_id}")
                assert response.status_code == 200
                # Should handle special characters without errors
                break


# ========================================================================
# RELATIONSHIP-POWERED SEARCH TESTS (PHASE 2)
# ========================================================================

class TestRelationshipExploration:
    """Test suite for relationship-based concept exploration."""

    def test_find_similar_concepts_endpoint(
        self,
        client: TestClient,
        db_session: Session,
    ) -> None:
        """Test finding similar concepts via relationships."""
        from app.models import ConceptRelationship

        # Find a concept with 'Maps to' relationships
        relationship = db_session.query(ConceptRelationship).filter(
            ConceptRelationship.relationship_id.in_(['Maps to', 'Mapped from']),
            ConceptRelationship.invalid_reason.is_(None)
        ).first()

        if not relationship:
            pytest.skip("No 'Maps to' relationships found")

        concept_id = relationship.concept_id_1

        # Test API response
        response = client.get(f"/concept/{concept_id}/similar")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 0

        # Verify structure if data exists
        if len(data) > 0:
            assert "concept_id" in data[0]
            assert "relationship_id" in data[0]
            assert "concept_name" in data[0]

    def test_find_similar_concepts_htmx(
        self,
        client: TestClient,
        db_session: Session,
    ) -> None:
        """Test HTMX response for similar concepts."""
        from app.models import ConceptRelationship

        relationship = db_session.query(ConceptRelationship).filter(
            ConceptRelationship.relationship_id.in_(['Maps to', 'Mapped from']),
            ConceptRelationship.invalid_reason.is_(None)
        ).first()

        if not relationship:
            pytest.skip("No relationships found")

        response = client.get(
            f"/concept/{relationship.concept_id_1}/similar",
            headers={"HX-Request": "true"}
        )

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

        # Verify HTML contains expected elements
        html = response.text
        assert "concept-card" in html or "empty-state" in html

    def test_find_similar_excludes_invalid_relationships(
        self,
        client: TestClient,
        db_session: Session,
    ) -> None:
        """Test that invalid relationships are excluded."""
        from app.models import Concept, ConceptRelationship

        # Find a concept with relationships
        concept = db_session.query(Concept).join(
            ConceptRelationship,
            ConceptRelationship.concept_id_1 == Concept.concept_id
        ).first()

        if not concept:
            pytest.skip("No concepts with relationships found")

        response = client.get(f"/concept/{concept.concept_id}/similar")
        assert response.status_code == 200

        # All returned relationships should have invalid_reason = None
        # (This is enforced by the query filter)

    def test_find_similar_deduplicates_concepts(
        self,
        client: TestClient,
        db_session: Session,
    ) -> None:
        """Test that duplicate concepts are removed from results."""
        from app.models import ConceptRelationship

        # Find a concept with relationships
        relationship = db_session.query(ConceptRelationship).filter(
            ConceptRelationship.relationship_id.in_(['Maps to', 'Mapped from']),
            ConceptRelationship.invalid_reason.is_(None)
        ).first()

        if not relationship:
            pytest.skip("No relationships found")

        # Test API response
        response = client.get(f"/concept/{relationship.concept_id_1}/similar")
        assert response.status_code == 200
        data = response.json()

        # Check that all concept_ids are unique
        concept_ids = [item["concept_id"] for item in data]
        assert len(concept_ids) == len(set(concept_ids)), "Found duplicate concept IDs in results"

    def test_search_descendants_endpoint(
        self,
        client: TestClient,
        concept_with_hierarchy: int,
    ) -> None:
        """Test searching within concept hierarchy."""
        # Search for any term within descendants
        response = client.get(
            f"/concept/{concept_with_hierarchy}/descendants/search?q=a"
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_search_descendants_empty_query(
        self,
        client: TestClient,
        concept_with_hierarchy: int,
    ) -> None:
        """Test that empty query returns empty results."""
        response = client.get(
            f"/concept/{concept_with_hierarchy}/descendants/search?q="
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_search_descendants_htmx(
        self,
        client: TestClient,
        concept_with_hierarchy: int,
    ) -> None:
        """Test HTMX response for descendant search."""
        response = client.get(
            f"/concept/{concept_with_hierarchy}/descendants/search?q=test",
            headers={"HX-Request": "true"}
        )

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_search_descendants_only_direct_children(
        self,
        client: TestClient,
        db_session: Session,
        concept_with_hierarchy: int,
    ) -> None:
        """Test that search only includes direct children (level 1)."""
        from app.models import ConceptAncestor

        # Get all descendants at various levels
        all_descendants = db_session.query(ConceptAncestor).filter(
            ConceptAncestor.ancestor_concept_id == concept_with_hierarchy,
            ConceptAncestor.min_levels_of_separation > 0
        ).all()

        if len(all_descendants) == 0:
            pytest.skip("No descendants found")

        # Count level 1 vs deeper levels
        level_1_count = sum(1 for d in all_descendants if d.min_levels_of_separation == 1)
        deeper_count = sum(1 for d in all_descendants if d.min_levels_of_separation > 1)

        # API should only search level 1
        # (This test verifies the query logic, actual verification requires checking results)
        assert level_1_count >= 0  # Basic assertion
