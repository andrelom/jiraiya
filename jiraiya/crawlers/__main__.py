import questionary

from jiraiya import settings

from .sprint_crawler import SprintCrawler


def main():
    choice = questionary.select(
        "Select an option:",
        choices=[
            "Sprint Crawler",
            "Exit"
        ]
    ).ask()

    if choice == "Sprint Crawler":
        sprint()
    elif choice == "Exit":
        print("Exiting...")
        exit()

def sprint():
    crawler = SprintCrawler(
        jira_url=settings.jira_url,
        jira_email=settings.jira_email,
        jira_api_token=settings.jira_api_token,
        jira_sprint_id=settings.jira_sprint_id,
        jira_output_folder=settings.jira_output_folder
    )
    crawler.start()

if __name__ == "__main__":
    main()
