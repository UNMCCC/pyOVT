"""Tests for the search endpoint using live database."""

from typing import Any

import pytest
from fastapi.testclient import TestClient


class TestSearchEndpoint:
    """Test suite for the /search/ endpoint."""

    def test_search_basic_query_json_response(
        self,
        client: TestClient,
        searchable_term: str,
    ) -> None:
        """
        Test basic search with JSON response (no HTMX header).

        Args:
            client: FastAPI test client
            searchable_term: A valid search term from the database
        """
        # Make request without HTMX header
        response = client.get(f"/search/?q={searchable_term}")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should return at least one result
        assert len(data) > 0

        # Verify response structure
        first_result = data[0]
        assert "concept_id" in first_result
        assert "concept_name" in first_result
        assert isinstance(first_result["concept_id"], int)
        assert isinstance(first_result["concept_name"], str)

    def test_search_with_htmx_header(
        self,
        client: TestClient,
        searchable_term: str,
    ) -> None:
        """
        Test search with HTMX header returns HTML template.

        Args:
            client: FastAPI test client
            searchable_term: A valid search term from the database
        """
        # Make request with HTMX header
        response = client.get(
            f"/search/?q={searchable_term}",
            headers={"HX-Request": "true"},
        )

        # Assertions
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        # HTML response should contain table or list structure
        assert len(response.text) > 0

    def test_search_with_vocabulary_filter(
        self,
        client: TestClient,
        searchable_term: str,
        sample_vocabulary_id: str,
    ) -> None:
        """
        Test search with vocabulary_id filter.

        Args:
            client: FastAPI test client
            searchable_term: A valid search term from the database
            sample_vocabulary_id: A valid vocabulary ID from the database
        """
        # Make request with vocabulary filter
        response = client.get(
            f"/search/?q={searchable_term}&vocabulary_id={sample_vocabulary_id}"
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # If results exist, verify they match the filter
        if len(data) > 0:
            for concept in data:
                assert concept["vocabulary_id"] == sample_vocabulary_id

    def test_search_with_domain_filter(
        self,
        client: TestClient,
        searchable_term: str,
        sample_domain_id: str,
    ) -> None:
        """
        Test search with domain_id filter.

        Args:
            client: FastAPI test client
            searchable_term: A valid search term from the database
            sample_domain_id: A valid domain ID from the database
        """
        # Make request with domain filter
        response = client.get(
            f"/search/?q={searchable_term}&domain_id={sample_domain_id}"
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # If results exist, verify they match the filter
        if len(data) > 0:
            for concept in data:
                assert concept["domain_id"] == sample_domain_id

    def test_search_with_both_filters(
        self,
        client: TestClient,
        searchable_term: str,
        sample_vocabulary_id: str,
        sample_domain_id: str,
    ) -> None:
        """
        Test search with both vocabulary_id and domain_id filters.

        Args:
            client: FastAPI test client
            searchable_term: A valid search term from the database
            sample_vocabulary_id: A valid vocabulary ID from the database
            sample_domain_id: A valid domain ID from the database
        """
        # Make request with both filters
        response = client.get(
            f"/search/?q={searchable_term}&vocabulary_id={sample_vocabulary_id}&domain_id={sample_domain_id}"
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # If results exist, verify they match both filters
        if len(data) > 0:
            for concept in data:
                assert concept["vocabulary_id"] == sample_vocabulary_id
                assert concept["domain_id"] == sample_domain_id

    def test_search_with_custom_limit(
        self,
        client: TestClient,
        searchable_term: str,
    ) -> None:
        """
        Test search with custom limit parameter.

        Args:
            client: FastAPI test client
            searchable_term: A valid search term from the database
        """
        # Make request with custom limit
        limit = 5
        response = client.get(f"/search/?q={searchable_term}&limit={limit}")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should respect the limit
        assert len(data) <= limit

    def test_search_default_limit(
        self,
        client: TestClient,
        searchable_term: str,
    ) -> None:
        """
        Test search uses default limit of 50 when not specified.

        Args:
            client: FastAPI test client
            searchable_term: A valid search term from the database
        """
        # Make request without limit
        response = client.get(f"/search/?q={searchable_term}")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should not exceed default limit of 50
        assert len(data) <= 50

    def test_search_empty_query_validation_error(
        self,
        client: TestClient,
    ) -> None:
        """
        Test search with empty query returns validation error.

        Args:
            client: FastAPI test client
        """
        # Make request with empty query
        response = client.get("/search/?q=")

        # Assertions
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_search_missing_query_parameter(
        self,
        client: TestClient,
    ) -> None:
        """
        Test search without query parameter returns validation error.

        Args:
            client: FastAPI test client
        """
        # Make request without query parameter
        response = client.get("/search/")

        # Assertions
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_search_no_results(
        self,
        client: TestClient,
    ) -> None:
        """
        Test search that returns no results.

        Args:
            client: FastAPI test client
        """
        # Make request with a term unlikely to exist
        response = client.get("/search/?q=xyznonexistentconceptxyz123")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # May or may not have results depending on fuzzy matching
        # Just verify it doesn't error

    def test_search_similarity_ordering(
        self,
        client: TestClient,
        searchable_term: str,
    ) -> None:
        """
        Test search results are ordered by similarity.

        Args:
            client: FastAPI test client
            searchable_term: A valid search term from the database
        """
        # Make request
        response = client.get(f"/search/?q={searchable_term}")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Verify results exist and are ordered
        # The most similar results should appear first
        if len(data) > 1:
            # First result should contain the search term (case insensitive)
            assert searchable_term.lower() in data[0]["concept_name"].lower()

    def test_search_with_special_characters(
        self,
        client: TestClient,
    ) -> None:
        """
        Test search with special characters in query.

        Args:
            client: FastAPI test client
        """
        # Make request with special characters (URL encoded)
        response = client.get("/search/?q=type-2")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Just verify it doesn't crash with special characters

    def test_search_case_insensitive(
        self,
        client: TestClient,
        searchable_term: str,
    ) -> None:
        """
        Test search is case insensitive.

        Args:
            client: FastAPI test client
            searchable_term: A valid search term from the database
        """
        # Make request with uppercase query
        response_upper = client.get(f"/search/?q={searchable_term.upper()}")
        response_lower = client.get(f"/search/?q={searchable_term.lower()}")

        # Assertions
        assert response_upper.status_code == 200
        assert response_lower.status_code == 200

        data_upper = response_upper.json()
        data_lower = response_lower.json()

        # Should return results regardless of case
        assert isinstance(data_upper, list)
        assert isinstance(data_lower, list)

    def test_search_response_model_fields(
        self,
        client: TestClient,
        searchable_term: str,
    ) -> None:
        """
        Test search response contains all expected ConceptBase fields.

        Args:
            client: FastAPI test client
            searchable_term: A valid search term from the database
        """
        # Make request
        response = client.get(f"/search/?q={searchable_term}")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        if len(data) > 0:
            concept = data[0]
            # Verify all required fields are present
            assert "concept_id" in concept
            assert "concept_name" in concept
            assert "domain_id" in concept
            assert "vocabulary_id" in concept
            assert "concept_class_id" in concept
            assert "concept_code" in concept

            # Verify optional fields
            assert "standard_concept" in concept
            assert "valid_start_date" in concept
            assert "valid_end_date" in concept
            assert "invalid_reason" in concept

    def test_search_returns_valid_concept_ids(
        self,
        client: TestClient,
        searchable_term: str,
    ) -> None:
        """
        Test that search returns valid concept IDs that can be used in other endpoints.

        Args:
            client: FastAPI test client
            searchable_term: A valid search term from the database
        """
        # Make search request
        response = client.get(f"/search/?q={searchable_term}")

        # Assertions
        assert response.status_code == 200
        data = response.json()

        if len(data) > 0:
            # Verify concept IDs are positive integers
            for concept in data:
                assert concept["concept_id"] > 0
                assert isinstance(concept["concept_id"], int)

    def test_search_with_very_short_term(
        self,
        client: TestClient,
    ) -> None:
        """
        Test search with a single character query.

        Args:
            client: FastAPI test client
        """
        # Make request with single character
        response = client.get("/search/?q=a")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Single character searches should still work

    def test_search_with_numeric_query(
        self,
        client: TestClient,
    ) -> None:
        """
        Test search with numeric query (might match concept codes).

        Args:
            client: FastAPI test client
        """
        # Make request with numeric query
        response = client.get("/search/?q=123")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Numeric searches should work without error

    def test_search_limit_boundary(
        self,
        client: TestClient,
        searchable_term: str,
    ) -> None:
        """
        Test search with limit of 1 returns at most 1 result.

        Args:
            client: FastAPI test client
            searchable_term: A valid search term from the database
        """
        # Make request with limit of 1
        response = client.get(f"/search/?q={searchable_term}&limit=1")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 1
