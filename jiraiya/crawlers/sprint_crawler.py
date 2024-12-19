import os
import logging
import json

from typing import Dict, List

from jiraiya.shared.api import JiraAPIClient
from jiraiya.shared.file import save_to_file
from jiraiya.shared.markdown import ADFToMarkdownConverter

logger = logging.getLogger(__name__)


class SprintCrawler:
    """
    Orchestrates fetching sprint tickets from Jira and saving them to files.
    """

    def __init__(
        self,
        jira_url: str,
        jira_email: str,
        jira_api_token: str,
        jira_sprint_id: str,
        jira_output_folder: str,
    ) -> None:
        """
        Initialize the SprintCrawler.

        Args:
            jira_url (str): The base URL of the Jira instance.
            jira_email (str): The email for Jira authentication.
            jira_api_token (str): The API token for Jira authentication.
            jira_sprint_id (str): The ID of the sprint to fetch tickets for.
            jira_output_folder (str): The folder to save fetched tickets.
        """
        self.jira_client = JiraAPIClient(jira_url, jira_email, jira_api_token)
        self.jira_sprint_id = jira_sprint_id
        self.output_folder = jira_output_folder

    def _process_ticket(self, ticket: Dict) -> Dict:
        """
        Process a ticket to combine its description and custom fields of type "doc".

        Args:
            ticket (Dict): A dictionary representing the Jira ticket.

        Returns:
            Dict: A dictionary containing the task title and combined description.
        """
        title = ticket["fields"].get("summary", "No Title")
        description = ticket["fields"].get("description")

        combined_description = {
            "original_description": description,
            "custom_fields": [],
        }

        for key, value in ticket["fields"].items():
            if key.startswith("customfield_") and isinstance(value, dict):
                if value.get("type") == "doc":
                    converter = ADFToMarkdownConverter(value)
                    custom_text = converter.convert()
                    if custom_text:
                        combined_description["custom_fields"].append(custom_text)

        return {
            "title": title,
            "description": combined_description,
        }

    def _convert_description_to_markdown(self, description: Dict) -> str:
        """
        Convert a description JSON structure to Markdown format.

        Args:
            description (Dict): The description dictionary.

        Returns:
            str: The Markdown representation of the description.
        """
        markdown_lines = []

        original_description = description.get("original_description")
        if original_description:
            converter = ADFToMarkdownConverter(original_description)
            original_description_md = converter.convert()
            markdown_lines.append(f"### Original Description\n\n{original_description_md}\n")

        custom_fields = description.get("custom_fields", [])
        if custom_fields:
            markdown_lines.append("### Custom Fields\n")
            for idx, field in enumerate(custom_fields, start=1):
                markdown_lines.append(f"#### Field {idx}\n\n{field}\n")

        return "\n".join(markdown_lines)

    def _save_ticket(self, ticket: Dict) -> None:
        """
        Save a processed ticket to JSON and Markdown files.

        Args:
            ticket (Dict): A dictionary representing the Jira ticket.
        """
        processed_ticket = self._process_ticket(ticket)
        ticket_id = ticket["key"]

        # Save JSON file.
        json_file_path = os.path.join(self.output_folder, f"{ticket_id}.json")
        try:
            content = json.dumps(processed_ticket, indent=4)
            save_to_file(json_file_path, content)
            logger.info("Saved ticket %s to %s", ticket_id, json_file_path)
        except Exception as e:
            logger.error("Failed to save ticket %s as JSON: %s", ticket_id, str(e))

        # Save Markdown file.
        markdown_file_path = os.path.join(self.output_folder, f"{ticket_id}.md")
        try:
            markdown_content = self._convert_description_to_markdown(processed_ticket["description"])
            save_to_file(markdown_file_path, markdown_content)
            logger.info("Saved ticket %s to %s", ticket_id, markdown_file_path)
        except Exception as e:
            logger.error("Failed to save ticket %s as Markdown: %s", ticket_id, str(e))

    def start(self) -> None:
        """
        Fetch and save all sprint tickets.
        """
        logger.info("Starting SprintCrawler...")

        fields = "summary,description," + ",".join(
            field["id"]
            for field in self.jira_client.get_available_fields()
            if field["id"].startswith("customfield_")
        )

        jql = f'sprint = "{self.jira_sprint_id}"'
        issues = self.jira_client.fetch_issues(jql, fields=fields)

        if not issues:
            logger.warning("No issues found for the specified sprint.")
            return

        for ticket in issues:
            self._save_ticket(ticket)

        logger.info(
            "Successfully saved %d tickets to %s.", len(issues), self.output_folder
        )
