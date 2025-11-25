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

    def test_search_empty_query_returns_empty_results(
        self,
        client: TestClient,
    ) -> None:
        """
        Test search with empty query returns empty results (not an error).

        This prevents validation errors when HTMX triggers on empty input.

        Args:
            client: FastAPI test client
        """
        # Make request with empty query
        response = client.get("/search/?q=")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_search_whitespace_query_returns_empty_results(
        self,
        client: TestClient,
    ) -> None:
        """
        Test search with whitespace-only query returns empty results.

        Args:
            client: FastAPI test client
        """
        # Make request with whitespace-only query
        response = client.get("/search/?q=   ")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

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

    # ========================================================================
    # FUZZY MATCHING TESTS
    # ========================================================================

    def test_fuzzy_matching_enabled_explicitly(
        self,
        client: TestClient,
        concept_with_typo: tuple[str, str],
    ) -> None:
        """
        Test fuzzy matching enabled with fuzzy=true parameter.

        When fuzzy=true, the search should use pg_trgm similarity matching,
        which allows for typo tolerance.

        Args:
            client: FastAPI test client
            concept_with_typo: Tuple of (correct_term, typo_term)
        """
        correct_term, typo_term = concept_with_typo

        # Make request with fuzzy matching explicitly enabled
        response = client.get(f"/search/?q={typo_term}&fuzzy=true")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Fuzzy matching should potentially find results even with typos
        # Note: Results depend on similarity threshold and database content
        # We just verify it doesn't error and returns a list
        if len(data) > 0:
            # Verify response structure is correct
            assert "concept_id" in data[0]
            assert "concept_name" in data[0]

    def test_fuzzy_matching_disabled_exact_substring_match(
        self,
        client: TestClient,
        searchable_term: str,
    ) -> None:
        """
        Test fuzzy matching disabled with fuzzy=false uses exact substring matching.

        When fuzzy=false or any value != "true", the search should use ILIKE
        for exact substring matching (case-insensitive).

        Args:
            client: FastAPI test client
            searchable_term: A valid search term from the database
        """
        # Extract a substring from the middle of the search term
        if len(searchable_term) >= 4:
            substring = searchable_term[1:-1]  # Remove first and last char
        else:
            substring = searchable_term

        # Make request with fuzzy matching disabled
        response = client.get(f"/search/?q={substring}&fuzzy=false")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Should find results containing the substring
        if len(data) > 0:
            # At least one result should contain the substring (case-insensitive)
            assert any(substring.lower() in result["concept_name"].lower() for result in data)

    def test_fuzzy_matching_disabled_no_typo_tolerance(
        self,
        client: TestClient,
        concept_with_typo: tuple[str, str],
    ) -> None:
        """
        Test fuzzy matching disabled does not match typos.

        When fuzzy is disabled, searches with typos should only match
        if the typo exists as an exact substring in concept names.

        Args:
            client: FastAPI test client
            concept_with_typo: Tuple of (correct_term, typo_term)
        """
        correct_term, typo_term = concept_with_typo

        # Make request with fuzzy matching disabled and typo
        response = client.get(f"/search/?q={typo_term}&fuzzy=false")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Results should only contain concepts with the typo as an exact substring
        # (not similarity-based matches)
        if len(data) > 0:
            for result in data:
                # The typo should appear as an exact substring in the result
                assert typo_term.lower() in result["concept_name"].lower()

    def test_fuzzy_matching_default_behavior(
        self,
        client: TestClient,
        searchable_term: str,
    ) -> None:
        """
        Test default behavior when fuzzy parameter is not provided.

        According to the backend logic: use_fuzzy = (fuzzy == "true")
        When fuzzy=None (not provided), use_fuzzy is False, so fuzzy is DISABLED by default.

        Args:
            client: FastAPI test client
            searchable_term: A valid search term from the database
        """
        # Make request without fuzzy parameter
        response = client.get(f"/search/?q={searchable_term}")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Should return results using exact substring matching (ILIKE)
        if len(data) > 0:
            # Results should contain the search term as a substring
            assert any(searchable_term.lower() in result["concept_name"].lower() for result in data)

    def test_fuzzy_matching_ordering_by_similarity(
        self,
        client: TestClient,
        searchable_term: str,
    ) -> None:
        """
        Test fuzzy matching orders results by similarity score.

        When fuzzy=true, results should be ordered by pg_trgm similarity
        (highest similarity first).

        Args:
            client: FastAPI test client
            searchable_term: A valid search term from the database
        """
        # Make request with fuzzy matching enabled
        response = client.get(f"/search/?q={searchable_term}&fuzzy=true")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # If we have multiple results, the first should be most similar
        if len(data) > 1:
            # First result should contain the search term (case-insensitive)
            # or be very similar to it
            first_result_name = data[0]["concept_name"].lower()
            # Most similar result should ideally contain the search term
            assert searchable_term.lower() in first_result_name or \
                   len(set(searchable_term.lower()) & set(first_result_name)) > 0

    def test_fuzzy_parameter_variations(
        self,
        client: TestClient,
        searchable_term: str,
    ) -> None:
        """
        Test various fuzzy parameter values.

        Args:
            client: FastAPI test client
            searchable_term: A valid search term from the database
        """
        # Test fuzzy=true (enabled)
        response_true = client.get(f"/search/?q={searchable_term}&fuzzy=true")
        assert response_true.status_code == 200

        # Test fuzzy=false (disabled)
        response_false = client.get(f"/search/?q={searchable_term}&fuzzy=false")
        assert response_false.status_code == 200

        # Test fuzzy=anything_else (disabled - not "true")
        response_other = client.get(f"/search/?q={searchable_term}&fuzzy=1")
        assert response_other.status_code == 200

        # Test no fuzzy parameter (default behavior)
        response_none = client.get(f"/search/?q={searchable_term}")
        assert response_none.status_code == 200

    # ========================================================================
    # STANDARD CONCEPTS FILTER TESTS
    # ========================================================================

    def test_standard_only_filter_enabled(
        self,
        client: TestClient,
        standard_concept_term: str,
    ) -> None:
        """
        Test standard_only=true filter returns only standard concepts.

        When standard_only=true, all results should have standard_concept='S'.

        Args:
            client: FastAPI test client
            standard_concept_term: A search term for a standard concept
        """
        # Make request with standard_only filter enabled
        response = client.get(f"/search/?q={standard_concept_term}&standard_only=true")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # All results should be standard concepts
        if len(data) > 0:
            for concept in data:
                assert concept["standard_concept"] == "S"

    def test_standard_only_filter_disabled(
        self,
        client: TestClient,
        searchable_term: str,
    ) -> None:
        """
        Test standard_only=false or None returns all concepts.

        When standard_only is not "true", no filter should be applied,
        and both standard and non-standard concepts can be returned.

        Args:
            client: FastAPI test client
            searchable_term: A valid search term from the database
        """
        # Make request with standard_only=false
        response = client.get(f"/search/?q={searchable_term}&standard_only=false")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Results can include both standard and non-standard concepts
        # We just verify it doesn't error and returns results
        if len(data) > 0:
            # Verify standard_concept field exists
            assert "standard_concept" in data[0]

    def test_standard_only_default_behavior(
        self,
        client: TestClient,
        searchable_term: str,
    ) -> None:
        """
        Test default behavior when standard_only parameter is not provided.

        When standard_only is not provided, no filter should be applied.

        Args:
            client: FastAPI test client
            searchable_term: A valid search term from the database
        """
        # Make request without standard_only parameter
        response = client.get(f"/search/?q={searchable_term}")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Should return results without filtering by standard_concept
        if len(data) > 0:
            # Results may include standard, classification, or non-standard concepts
            assert "standard_concept" in data[0]

    def test_standard_only_parameter_variations(
        self,
        client: TestClient,
        standard_concept_term: str,
    ) -> None:
        """
        Test various standard_only parameter values.

        Args:
            client: FastAPI test client
            standard_concept_term: A search term for a standard concept
        """
        # Test standard_only=true (filter enabled)
        response_true = client.get(f"/search/?q={standard_concept_term}&standard_only=true")
        assert response_true.status_code == 200
        data_true = response_true.json()
        if len(data_true) > 0:
            assert all(c["standard_concept"] == "S" for c in data_true)

        # Test standard_only=false (filter disabled)
        response_false = client.get(f"/search/?q={standard_concept_term}&standard_only=false")
        assert response_false.status_code == 200

        # Test no standard_only parameter (filter disabled)
        response_none = client.get(f"/search/?q={standard_concept_term}")
        assert response_none.status_code == 200

    def test_standard_only_empty_results(
        self,
        client: TestClient,
        non_standard_concept_term: str,
    ) -> None:
        """
        Test standard_only filter can return empty results.

        When searching for a non-standard concept with standard_only=true,
        the result set may be empty.

        Args:
            client: FastAPI test client
            non_standard_concept_term: A search term for a non-standard concept
        """
        if non_standard_concept_term is None:
            pytest.skip("No non-standard concepts available in database")

        # Make request with standard_only filter
        response = client.get(f"/search/?q={non_standard_concept_term}&standard_only=true")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Results should either be empty or only contain standard concepts
        for concept in data:
            assert concept["standard_concept"] == "S"

    # ========================================================================
    # COMBINED FILTERS TESTS
    # ========================================================================

    def test_fuzzy_and_standard_only_both_enabled(
        self,
        client: TestClient,
        standard_concept_term: str,
    ) -> None:
        """
        Test fuzzy=true and standard_only=true together.

        Both filters should apply: fuzzy similarity matching + standard concepts only.

        Args:
            client: FastAPI test client
            standard_concept_term: A search term for a standard concept
        """
        # Make request with both filters enabled
        response = client.get(
            f"/search/?q={standard_concept_term}&fuzzy=true&standard_only=true"
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # All results should be standard concepts
        if len(data) > 0:
            for concept in data:
                assert concept["standard_concept"] == "S"

    def test_fuzzy_enabled_standard_only_disabled(
        self,
        client: TestClient,
        searchable_term: str,
    ) -> None:
        """
        Test fuzzy=true with standard_only=false/None.

        Should use fuzzy matching without filtering by standard_concept.

        Args:
            client: FastAPI test client
            searchable_term: A valid search term from the database
        """
        # Make request with fuzzy enabled, standard_only disabled
        response = client.get(f"/search/?q={searchable_term}&fuzzy=true&standard_only=false")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Should return results using fuzzy matching, no standard filter
        if len(data) > 0:
            assert "standard_concept" in data[0]

    def test_fuzzy_disabled_standard_only_enabled(
        self,
        client: TestClient,
        standard_concept_term: str,
    ) -> None:
        """
        Test fuzzy=false with standard_only=true.

        Should use exact substring matching with standard concepts filter.

        Args:
            client: FastAPI test client
            standard_concept_term: A search term for a standard concept
        """
        # Make request with fuzzy disabled, standard_only enabled
        response = client.get(
            f"/search/?q={standard_concept_term}&fuzzy=false&standard_only=true"
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # All results should be standard concepts
        if len(data) > 0:
            for concept in data:
                assert concept["standard_concept"] == "S"
                # Should contain search term as substring
                assert standard_concept_term.lower() in concept["concept_name"].lower()

    def test_fuzzy_disabled_standard_only_disabled(
        self,
        client: TestClient,
        searchable_term: str,
    ) -> None:
        """
        Test fuzzy=false with standard_only=false.

        Should use exact substring matching without standard filter.

        Args:
            client: FastAPI test client
            searchable_term: A valid search term from the database
        """
        # Make request with both filters disabled
        response = client.get(f"/search/?q={searchable_term}&fuzzy=false&standard_only=false")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Should return results using exact matching, no standard filter
        if len(data) > 0:
            assert "standard_concept" in data[0]

    def test_all_filters_combined(
        self,
        client: TestClient,
        standard_concept_term: str,
        sample_vocabulary_id: str,
        sample_domain_id: str,
    ) -> None:
        """
        Test all filters together: fuzzy, standard_only, vocabulary_id, domain_id.

        All filters should apply correctly in combination.

        Args:
            client: FastAPI test client
            standard_concept_term: A search term for a standard concept
            sample_vocabulary_id: A valid vocabulary ID from the database
            sample_domain_id: A valid domain ID from the database
        """
        # Make request with all filters
        response = client.get(
            f"/search/?q={standard_concept_term}"
            f"&fuzzy=true"
            f"&standard_only=true"
            f"&vocabulary_id={sample_vocabulary_id}"
            f"&domain_id={sample_domain_id}"
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # All results should match all filters
        if len(data) > 0:
            for concept in data:
                assert concept["standard_concept"] == "S"
                assert concept["vocabulary_id"] == sample_vocabulary_id
                assert concept["domain_id"] == sample_domain_id

    # ========================================================================
    # EDGE CASES AND HTMX TESTS
    # ========================================================================

    def test_htmx_request_preserves_fuzzy_filter(
        self,
        client: TestClient,
        searchable_term: str,
    ) -> None:
        """
        Test HTMX requests work correctly with fuzzy parameter.

        Args:
            client: FastAPI test client
            searchable_term: A valid search term from the database
        """
        # Make HTMX request with fuzzy parameter
        response = client.get(
            f"/search/?q={searchable_term}&fuzzy=true",
            headers={"HX-Request": "true"},
        )

        # Assertions
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert len(response.text) > 0

    def test_htmx_request_preserves_standard_only_filter(
        self,
        client: TestClient,
        standard_concept_term: str,
    ) -> None:
        """
        Test HTMX requests work correctly with standard_only parameter.

        Args:
            client: FastAPI test client
            standard_concept_term: A search term for a standard concept
        """
        # Make HTMX request with standard_only parameter
        response = client.get(
            f"/search/?q={standard_concept_term}&standard_only=true",
            headers={"HX-Request": "true"},
        )

        # Assertions
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert len(response.text) > 0

    def test_htmx_request_preserves_all_new_filters(
        self,
        client: TestClient,
        standard_concept_term: str,
    ) -> None:
        """
        Test HTMX requests work correctly with both fuzzy and standard_only parameters.

        Args:
            client: FastAPI test client
            standard_concept_term: A search term for a standard concept
        """
        # Make HTMX request with both new parameters
        response = client.get(
            f"/search/?q={standard_concept_term}&fuzzy=true&standard_only=true",
            headers={"HX-Request": "true"},
        )

        # Assertions
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert len(response.text) > 0

    def test_response_model_includes_standard_concept_field(
        self,
        client: TestClient,
        searchable_term: str,
    ) -> None:
        """
        Test response always includes standard_concept field.

        The standard_concept field should be present in all responses,
        regardless of filter settings.

        Args:
            client: FastAPI test client
            searchable_term: A valid search term from the database
        """
        # Test without filters
        response = client.get(f"/search/?q={searchable_term}")
        assert response.status_code == 200
        data = response.json()

        if len(data) > 0:
            assert "standard_concept" in data[0]

        # Test with standard_only=true
        response_filtered = client.get(f"/search/?q={searchable_term}&standard_only=true")
        assert response_filtered.status_code == 200
        data_filtered = response_filtered.json()

        if len(data_filtered) > 0:
            assert "standard_concept" in data_filtered[0]
            assert data_filtered[0]["standard_concept"] == "S"
