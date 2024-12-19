import os
import logging
import json

from typing import Dict

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

    def _process_ticket(self, ticket: Dict) -> Dict:
        """
        Process a ticket to combine its description and custom fields of type "doc".

        Args:
            ticket (Dict): A dictionary representing the Jira ticket.

        Returns:
            Dict: A dictionary containing the task title and combined description.
        """
        title = ticket.get("fields", {}).get("summary", "No Title")
        description = ticket.get("fields", {}).get("description")

        combined_description = {
            "original_description": description,
            "custom_fields": [],
        }

        for key, value in ticket.get("fields", {}).items():
            if key.startswith(self.CUSTOM_FIELD_PREFIX) and isinstance(value, dict):
                if value.get("type") == "doc":
                    combined_description["custom_fields"].append({
                        "field_id": key,
                        "field_value": value,
                    })

        return {"title": title, "description": combined_description}

    def _convert_description_to_markdown(
        self, description: Dict, title: str
    ) -> str:
        """
        Convert a description JSON structure to Markdown format.

        Args:
            description (Dict): The description dictionary.
            title (str): The task title.

        Returns:
            str: The Markdown representation of the description.
        """
        markdown_lines = [f"# {title}\n"]

        if original_description := description.get("original_description"):
            try:
                converter = ADFToMarkdownConverter(original_description)
                markdown_lines.append("### Original Description\n")
                markdown_lines.append(converter.convert())
            except Exception as e:
                logger.error("Error converting original description: %s", e)
                markdown_lines.append("Error converting original description.\n")

        custom_fields = description.get("custom_fields", [])
        if custom_fields:
            markdown_lines.append("\n### Custom Fields\n")
            for field in custom_fields:
                field_id = field.get("field_id", "Unknown Field ID")
                field_value = field.get("field_value")

                markdown_lines.append(f"#### {field_id}\n")
                if isinstance(field_value, dict):
                    try:
                        converter = ADFToMarkdownConverter(field_value)
                        markdown_lines.append(converter.convert())
                    except Exception as e:
                        markdown_lines.append(f"Error processing field: {e}\n")
                else:
                    markdown_lines.append("Unsupported field structure.\n")

        return "\n".join(markdown_lines)

    def _save_ticket(self, ticket: Dict) -> None:
        """
        Save a processed ticket to JSON and Markdown files.

        Args:
            ticket (Dict): A dictionary representing the Jira ticket.
        """
        try:
            processed_ticket = self._process_ticket(ticket)
            ticket_id = ticket["key"]
            title = processed_ticket["title"]

            json_path = os.path.join(self.output_folder, "json", f"{ticket_id}.json")
            save_to_file(json_path, json.dumps(processed_ticket, indent=4))
            logger.info("Saved ticket as JSON: %s", json_path)

            markdown_path = os.path.join(self.output_folder, "md", f"{ticket_id}.md")
            markdown_content = self._convert_description_to_markdown(
                processed_ticket["description"], title
            )
            save_to_file(markdown_path, markdown_content)
            logger.info("Saved ticket as Markdown: %s", markdown_path)

        except Exception as e:
            logger.error("Failed to save ticket %s: %s", ticket.get("key", "Unknown"), e)

    def start(self) -> None:
        """
        Fetch and save all sprint tickets.
        """
        logger.info("Starting SprintCrawler...")

        try:
            fields = "summary,description," + ",".join(
                field["id"]
                for field in self.jira_client.get_available_fields()
                if field["id"].startswith(self.CUSTOM_FIELD_PREFIX)
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
