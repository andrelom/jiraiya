import os
import re
import logging
import json

from typing import List, Dict, Any

from jiraiya.shared.api import JiraAPIClient
from jiraiya.shared.file import save_to_file
from jiraiya.shared.markdown import ADFToMarkdownConverter


logger = logging.getLogger(__name__)

class SprintCrawler:
    """
    Orchestrates fetching sprint tickets from Jira and saving them to files.
    """

    CUSTOM_FIELD_PREFIX = "customfield_"

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

    def _process_ticket(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a ticket to extract its title, description, and custom fields of type "doc".

        Args:
            ticket (Dict[str, Any]): A dictionary representing the Jira ticket.

        Returns:
            Dict[str, Any]: A dictionary containing the task title, description, and custom fields.
        """
        id = ticket.get("key", "N/A")
        fields = ticket.get("fields", {})
        title = fields.get("summary", "N/A")
        description = fields.get("description")

        # Only include custom fields that are of type "doc", as they are the only ones
        # that are candidates for markdown conversion, and similar to the description field.
        customfields = [
            {"field_key": key, "field_value": value}
            for key, value in fields.items()
            if key.startswith(self.CUSTOM_FIELD_PREFIX) and isinstance(value, dict) and value.get("type") == "doc"
        ]

        return {
            "id": id,
            "title": title,
            "description": description,
            "customfields": customfields,
        }

    def _convert_description_to_markdown(
        self, id: str, title: str, description: Any, customfields: List[Dict[str, Any]]
    ) -> str:
        """
        Convert a description JSON structure to Markdown format.

        Args:
            id (str): The ticket ID.
            title (str): The task title.
            description (Any): The description dictionary.
            customfields (List[Dict[str, Any]]): List of custom fields.

        Returns:
            str: The Markdown representation of the description.
        """
        markdown_lines = [f"# {id} - {title}"]

        if description:
            try:
                converter = ADFToMarkdownConverter(description)
                markdown_lines.append(converter.convert())
            except Exception as e:
                logger.error("Error converting description: %s", e)
                markdown_lines.append("Error converting description.")

        if customfields:
            for field in customfields:
                field_key = field.get("field_key", "Unknown Field ID")
                field_value = field.get("field_value")

                try:
                    converter = ADFToMarkdownConverter(field_value)
                    markdown_lines.append(converter.convert())
                except Exception as e:
                    logger.error("Error processing custom field %s: %s", field_key, e)
                    markdown_lines.append(f"Error processing field {field_key}.")

        if not description and not customfields:
            markdown_lines.append("N/A")

        output = "\n\n".join(markdown_lines).strip()
        output = re.sub(r'\n{3,}', '\n\n', output)
        output = f"{output}\n"
        return output

    def _save_ticket(self, ticket: Dict[str, Any]) -> None:
        """
        Save a processed ticket to JSON and Markdown files.

        Args:
            ticket (Dict[str, Any]): A dictionary representing the Jira ticket.
        """
        try:
            processed_ticket = self._process_ticket(ticket)

            id = processed_ticket.get("id", "unknown")
            title = processed_ticket["title"]
            description = processed_ticket.get("description")
            customfields = processed_ticket.get("customfields", [])

            json_path = os.path.join(self.output_folder, "json", f"{id}.json")
            markdown_path = os.path.join(self.output_folder, "md", f"{id}.md")

            json_content = json.dumps(processed_ticket, indent=4)
            save_to_file(json_path, json_content)
            logger.info("Saved ticket as JSON: %s", json_path)

            markdown_content = self._convert_description_to_markdown(id, title, description, customfields)
            save_to_file(markdown_path, markdown_content)
            logger.info("Saved ticket as Markdown: %s", markdown_path)

        except Exception as e:
            logger.error("Failed to save ticket %s: %s", ticket.get("key", "unknown"), e)

    def start(self) -> None:
        """
        Fetch and save all sprint tickets.
        """
        logger.info("Starting SprintCrawler...")

        try:
            fields = ",".join(
                ["summary", "description"] +
                [field["id"] for field in self.jira_client.get_available_fields() if field["id"].startswith(self.CUSTOM_FIELD_PREFIX)]
            )

            jql = f'sprint = "{self.jira_sprint_id}"'
            issues = self.jira_client.fetch_issues(jql, fields=fields)

            if not issues:
                logger.warning("No issues found for the specified sprint.")
                return

            for ticket in issues:
                self._save_ticket(ticket)

            logger.info("Successfully processed %d tickets.", len(issues))

        except Exception as e:
            logger.error("Error during SprintCrawler execution: %s", e)
