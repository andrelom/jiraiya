"""
A shared module for interacting with the Jira API.
"""

import logging
import httpx

from typing import List, Dict


logger = logging.getLogger(__name__)

class JiraAPIClient:
    """
    A client for interacting with the Jira API.
    """

    def __init__(self, base_url: str, email: str, api_token: str) -> None:
        """
        Initialize the Jira API client.

        Args:
            base_url (str): The base URL of the Jira instance.
            email (str): The email of the user for authentication.
            api_token (str): The API token for authentication.
        """
        self.base_url = base_url
        self.auth = (email, api_token)
        self.headers = {"Accept": "application/json"}

    def fetch_issues(
        self, jql: str, fields: str = "summary,description", expand: str = "renderedFields"
    ) -> List[Dict]:
        """
        Fetch issues from Jira based on a JQL query.

        Args:
            jql (str): Jira Query Language string for filtering issues.
            fields (str): Comma-separated list of fields to retrieve. Defaults to "summary,description".
            expand (str): Comma-separated list of fields to expand. Defaults to "renderedFields".

        Returns:
            List[Dict]: A list of issues retrieved from Jira.

        Raises:
            httpx.RequestError: If there is an error connecting to the Jira API.
            httpx.HTTPStatusError: If the Jira API returns an error response.
        """
        endpoint = f"{self.base_url}/rest/api/3/search"
        params = {"jql": jql, "fields": fields, "expand": expand}

        try:
            with httpx.Client(auth=self.auth) as client:
                response = client.get(endpoint, headers=self.headers, params=params)
                response.raise_for_status()
                return response.json().get("issues", [])
        except httpx.RequestError as exc:
            logger.error("An error occurred while connecting to Jira: %s", exc)
            raise
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Invalid response from Jira: %s - %s",
                exc.response.status_code,
                exc.response.text,
            )
            raise

    def get_available_fields(self) -> List[Dict]:
        """
        Fetch the list of all available fields in the Jira instance.

        Returns:
            List[Dict]: A list of field dictionaries with keys like 'id' and 'name'.
        """
        endpoint = f"{self.base_url}/rest/api/3/field"
        try:
            with httpx.Client(auth=self.auth) as client:
                response = client.get(endpoint, headers=self.headers)
                response.raise_for_status()
                return response.json()
        except httpx.RequestError as exc:
            logger.error("An error occurred while connecting to Jira: %s", exc)
            raise
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Invalid response from Jira: %s - %s",
                exc.response.status_code,
                exc.response.text,
            )
            raise
