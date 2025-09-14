from unittest.mock import Mock, patch

import pytest
import requests
from fastapi.testclient import TestClient

from src.api import app
from src.github_service import parse_repo_url

client = TestClient(app)

# Mock data for tests
MOCK_PULL_REQUESTS = [
    {
        "number": 123,
        "title": "Add new feature",
        "state": "open",
        "user": {"login": "testuser"},
        "created_at": "2025-08-25T10:00:00Z",
        "updated_at": "2025-08-25T12:00:00Z",
        "html_url": "https://github.com/owner/repo/pull/123",
    },
    {
        "number": 122,
        "title": "Fix bug",
        "state": "closed",
        "user": {"login": "anotheruser"},
        "created_at": "2025-08-24T09:00:00Z",
        "updated_at": "2025-08-24T11:00:00Z",
        "html_url": "https://github.com/owner/repo/pull/122",
    },
]

MOCK_CONTRIBUTORS = [
    {
        "login": "testuser",
        "contributions": 150,
        "html_url": "https://github.com/testuser",
        "avatar_url": "https://github.com/testuser.png",
    },
    {
        "login": "anotheruser",
        "contributions": 75,
        "html_url": "https://github.com/anotheruser",
        "avatar_url": "https://github.com/anotheruser.png",
    },
]


class TestHealthEndpoint:

    def test_health_check_returns_healthy_status(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestPullRequestsEndpoint:

    @patch('src.github_service.requests.get')
    def test_get_pull_requests_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = MOCK_PULL_REQUESTS
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        response = client.get("/pull-requests/2?repo=owner/repo")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["repository"] == "owner/repo"
        assert response_data["count"] == 2
        assert len(response_data["pull_requests"]) == 2
        assert response_data["pull_requests"][0]["number"] == 123
        assert response_data["pull_requests"][0]["title"] == "Add new feature"
        assert response_data["pull_requests"][0]["author"] == "testuser"

    @patch('src.github_service.requests.get')
    def test_get_pull_requests_with_github_url(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = MOCK_PULL_REQUESTS[:1]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        response = client.get("/pull-requests/1?repo=https://github.com/owner/repo")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["repository"] == "owner/repo"
        assert response_data["count"] == 1

    def test_get_pull_requests_missing_repo_parameter(self):
        response = client.get("/pull-requests/5")
        assert response.status_code == 422

    def test_get_pull_requests_invalid_repo_format(self):
        response = client.get("/pull-requests/5?repo=invalid-repo-format")
        assert response.status_code == 400
        assert "Invalid repo format" in response.json()["detail"]

    @patch('src.github_service.requests.get')
    def test_get_pull_requests_github_api_error(self, mock_get):
        mock_get.side_effect = requests.RequestException("API Error")

        response = client.get("/pull-requests/5?repo=owner/repo")
        assert response.status_code == 500
        assert "GitHub API error" in response.json()["detail"]


class TestPullRequestsByDateEndpoint:

    @patch('src.github_service.requests.get')
    def test_get_pull_requests_by_date_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {'items': MOCK_PULL_REQUESTS}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        response = client.get("/pull-requests-by-date?repo=owner/repo&start_date=2025-08-24&end_date=2025-08-25")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["repository"] == "owner/repo"
        assert response_data["date_range"] == "2025-08-24 to 2025-08-25"
        assert response_data["count"] == 2
        assert len(response_data["pull_requests"]) == 2

    def test_get_pull_requests_by_date_missing_parameters(self):
        response = client.get("/pull-requests-by-date?repo=owner/repo")
        assert response.status_code == 422

    @patch('src.github_service.requests.get')
    def test_get_pull_requests_by_date_invalid_date_format(self, mock_get):
        # Mock GitHub's 422 error response for invalid dates
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.RequestException("422 Client Error: Unprocessable Entity")
        mock_get.return_value = mock_response

        response = client.get("/pull-requests-by-date?repo=owner/repo&start_date=invalid-date&end_date=2025-08-25")
        assert response.status_code == 500
        assert "GitHub API error" in response.json()["detail"]

    def test_get_pull_requests_by_date_invalid_repo_format(self):
        response = client.get("/pull-requests-by-date?repo=invalid&start_date=2025-08-24&end_date=2025-08-25")
        assert response.status_code == 400
        assert "Invalid format" in response.json()["detail"]


class TestContributorsEndpoint:

    @patch('src.github_service.requests.get')
    def test_get_contributors_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = MOCK_CONTRIBUTORS
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        response = client.get("/contributors?repo=owner/repo")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["repository"] == "owner/repo"
        assert response_data["count"] == 2
        assert len(response_data["contributors"]) == 2
        assert response_data["contributors"][0]["login"] == "testuser"
        assert response_data["contributors"][0]["contributions"] == 150
        assert response_data["contributors"][1]["login"] == "anotheruser"
        assert response_data["contributors"][1]["contributions"] == 75

    @patch('src.github_service.requests.get')
    def test_get_contributors_with_github_url(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = MOCK_CONTRIBUTORS
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        response = client.get("/contributors?repo=https://github.com/owner/repo")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["repository"] == "owner/repo"

    def test_get_contributors_missing_repo_parameter(self):
        response = client.get("/contributors")
        assert response.status_code == 422

    def test_get_contributors_invalid_repo_format(self):
        response = client.get("/contributors?repo=invalid-format")
        assert response.status_code == 400
        assert "Invalid repo format" in response.json()["detail"]

    @patch('src.github_service.requests.get')
    def test_get_contributors_github_api_error(self, mock_get):
        mock_get.side_effect = requests.RequestException("API Error")

        response = client.get("/contributors?repo=owner/repo")
        assert response.status_code == 500
        assert "GitHub API error" in response.json()["detail"]


class TestHelperFunctions:

    def test_parse_repo_url_with_owner_repo_format(self):
        owner, repo_name = parse_repo_url("owner/repo")
        assert owner == "owner"
        assert repo_name == "repo"

    def test_parse_repo_url_with_github_url_format(self):
        owner, repo_name = parse_repo_url("https://github.com/owner/repo")
        assert owner == "owner"
        assert repo_name == "repo"

    def test_parse_repo_url_with_trailing_slash(self):
        owner, repo_name = parse_repo_url("https://github.com/owner/repo/")
        assert owner == "owner"
        assert repo_name == "repo"

    def test_parse_repo_url_with_invalid_format(self):
        with pytest.raises(ValueError, match="Invalid repository format"):
            parse_repo_url("invalid")

    def test_parse_repo_url_with_too_many_parts(self):
        with pytest.raises(ValueError, match="Invalid repository format"):
            parse_repo_url("owner/repo/extra/parts")
