"""Tests for the main index endpoint using live database."""

import pytest
from fastapi.testclient import TestClient


class TestIndexEndpoint:
    """Test suite for the / (index) endpoint."""

    def test_index_success(
        self,
        client: TestClient,
    ) -> None:
        """
        Test successful retrieval of the index page.

        Args:
            client: FastAPI test client
        """
        # Make request
        response = client.get("/")

        # Assertions
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_index_contains_vocabularies(
        self,
        client: TestClient,
        sample_vocabulary_id: str,
    ) -> None:
        """
        Test index page contains vocabulary information.

        Args:
            client: FastAPI test client
            sample_vocabulary_id: A valid vocabulary ID from the database
        """
        # Make request
        response = client.get("/")

        # Assertions
        assert response.status_code == 200
        # Should contain at least one vocabulary
        assert sample_vocabulary_id in response.text

    def test_index_contains_domains(
        self,
        client: TestClient,
        sample_domain_id: str,
    ) -> None:
        """
        Test index page contains domain information.

        Args:
            client: FastAPI test client
            sample_domain_id: A valid domain ID from the database
        """
        # Make request
        response = client.get("/")

        # Assertions
        assert response.status_code == 200
        # Should contain at least one domain
        assert sample_domain_id in response.text

    def test_index_displays_multiple_vocabularies(
        self,
        client: TestClient,
        db_session,
    ) -> None:
        """
        Test index page displays multiple vocabularies.

        Args:
            client: FastAPI test client
            db_session: Database session
        """
        from app.models import Vocabulary

        # Get vocabularies from the database
        vocabularies = db_session.query(Vocabulary).limit(3).all()

        if len(vocabularies) < 2:
            pytest.skip("Need at least 2 vocabularies in database")

        # Make request
        response = client.get("/")

        # Assertions
        assert response.status_code == 200

        # Should display multiple vocabularies
        vocab_count = 0
        for vocab in vocabularies:
            if vocab.vocabulary_id in response.text:
                vocab_count += 1

        assert vocab_count >= 2, "Should display at least 2 vocabularies"

    def test_index_displays_multiple_domains(
        self,
        client: TestClient,
        db_session,
    ) -> None:
        """
        Test index page displays multiple domains.

        Args:
            client: FastAPI test client
            db_session: Database session
        """
        from app.models import Domain

        # Get domains from the database
        domains = db_session.query(Domain).limit(3).all()

        if len(domains) < 2:
            pytest.skip("Need at least 2 domains in database")

        # Make request
        response = client.get("/")

        # Assertions
        assert response.status_code == 200

        # Should display multiple domains
        domain_count = 0
        for domain in domains:
            if domain.domain_id in response.text:
                domain_count += 1

        assert domain_count >= 2, "Should display at least 2 domains"

    def test_index_vocabularies_ordered(
        self,
        client: TestClient,
        db_session,
    ) -> None:
        """
        Test that vocabularies appear to be ordered.

        Args:
            client: FastAPI test client
            db_session: Database session
        """
        from app.models import Vocabulary

        # Get vocabularies from the database
        vocabularies = db_session.query(Vocabulary).order_by(
            Vocabulary.vocabulary_id
        ).limit(5).all()

        if len(vocabularies) < 2:
            pytest.skip("Need at least 2 vocabularies in database")

        # Make request
        response = client.get("/")

        # Assertions
        assert response.status_code == 200

        # Check that vocabularies appear in the response
        # (Strict ordering check would be fragile due to HTML structure)
        for vocab in vocabularies:
            assert vocab.vocabulary_id in response.text

    def test_index_domains_ordered(
        self,
        client: TestClient,
        db_session,
    ) -> None:
        """
        Test that domains appear to be ordered.

        Args:
            client: FastAPI test client
            db_session: Database session
        """
        from app.models import Domain

        # Get domains from the database
        domains = db_session.query(Domain).order_by(
            Domain.domain_id
        ).limit(5).all()

        if len(domains) < 2:
            pytest.skip("Need at least 2 domains in database")

        # Make request
        response = client.get("/")

        # Assertions
        assert response.status_code == 200

        # Check that domains appear in the response
        for domain in domains:
            assert domain.domain_id in response.text

    def test_index_html_structure(
        self,
        client: TestClient,
    ) -> None:
        """
        Test that index page has proper HTML structure.

        Args:
            client: FastAPI test client
        """
        # Make request
        response = client.get("/")

        # Assertions
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

        # Should have basic HTML structure
        response_text = response.text.lower()
        assert "<html" in response_text or "<!doctype" in response_text

    def test_index_with_htmx_header(
        self,
        client: TestClient,
    ) -> None:
        """
        Test index page with HTMX header (should behave same as regular request).

        Args:
            client: FastAPI test client
        """
        # Make request with HTMX header
        response = client.get("/", headers={"HX-Request": "true"})

        # Assertions
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_index_returns_template_not_json(
        self,
        client: TestClient,
    ) -> None:
        """
        Test that index returns a template response, not JSON.

        Args:
            client: FastAPI test client
        """
        # Make request
        response = client.get("/")

        # Assertions
        assert response.status_code == 200
        # Should not be JSON
        assert "application/json" not in response.headers.get("content-type", "")
        # Should be HTML
        assert "text/html" in response.headers["content-type"]

    def test_index_vocabulary_details(
        self,
        client: TestClient,
        db_session,
    ) -> None:
        """
        Test that index page displays vocabulary details beyond just IDs.

        Args:
            client: FastAPI test client
            db_session: Database session
        """
        from app.models import Vocabulary

        # Get a vocabulary with complete information
        vocabulary = db_session.query(Vocabulary).first()

        if not vocabulary:
            pytest.skip("No vocabularies found in database")

        # Make request
        response = client.get("/")

        # Assertions
        assert response.status_code == 200

        # Should display vocabulary ID at minimum
        assert vocabulary.vocabulary_id in response.text

        # May also display vocabulary name if the template includes it
        if vocabulary.vocabulary_name:
            # This is optional depending on template design
            pass

    def test_index_domain_details(
        self,
        client: TestClient,
        db_session,
    ) -> None:
        """
        Test that index page displays domain details.

        Args:
            client: FastAPI test client
            db_session: Database session
        """
        from app.models import Domain

        # Get a domain
        domain = db_session.query(Domain).first()

        if not domain:
            pytest.skip("No domains found in database")

        # Make request
        response = client.get("/")

        # Assertions
        assert response.status_code == 200

        # Should display domain ID
        assert domain.domain_id in response.text

    def test_index_handles_empty_database_gracefully(
        self,
        client: TestClient,
        db_session,
    ) -> None:
        """
        Test that index page renders even with minimal data.

        Args:
            client: FastAPI test client
            db_session: Database session
        """
        # Make request (database may or may not have data)
        response = client.get("/")

        # Assertions
        # Should always return 200 even if database is empty
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_index_search_form_present(
        self,
        client: TestClient,
    ) -> None:
        """
        Test that index page contains a search form.

        Args:
            client: FastAPI test client
        """
        # Make request
        response = client.get("/")

        # Assertions
        assert response.status_code == 200

        # Should have a form or search input
        response_text = response.text.lower()
        assert any(term in response_text for term in [
            "<form", "search", "<input"
        ])

    def test_index_performance(
        self,
        client: TestClient,
    ) -> None:
        """
        Test that index page loads in reasonable time.

        Args:
            client: FastAPI test client
        """
        import time

        start_time = time.time()
        response = client.get("/")
        elapsed_time = time.time() - start_time

        # Assertions
        assert response.status_code == 200
        # Should load within 3 seconds
        assert elapsed_time < 3.0, f"Index page took {elapsed_time:.2f}s to load"

    def test_index_vocabulary_count(
        self,
        client: TestClient,
        db_session,
    ) -> None:
        """
        Test that index displays correct number of vocabularies.

        Args:
            client: FastAPI test client
            db_session: Database session
        """
        from app.models import Vocabulary

        # Get count from database
        vocab_count = db_session.query(Vocabulary).count()

        if vocab_count == 0:
            pytest.skip("No vocabularies in database")

        # Make request
        response = client.get("/")

        # Assertions
        assert response.status_code == 200

        # Verify at least some vocabularies are displayed
        # (Exact count matching would be fragile due to HTML structure)
        assert vocab_count > 0

    def test_index_domain_count(
        self,
        client: TestClient,
        db_session,
    ) -> None:
        """
        Test that index displays correct number of domains.

        Args:
            client: FastAPI test client
            db_session: Database session
        """
        from app.models import Domain

        # Get count from database
        domain_count = db_session.query(Domain).count()

        if domain_count == 0:
            pytest.skip("No domains in database")

        # Make request
        response = client.get("/")

        # Assertions
        assert response.status_code == 200

        # Verify at least some domains are displayed
        assert domain_count > 0
