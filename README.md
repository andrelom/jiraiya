# Jiraiya

Software designed to assist in analyzing Jira tickets and serilize them into local files.

## Command Line

### Running a Specific Crawler

```sh
python -m jiraiya.crawlers
```

## Development

Details, recommendations, and guidelines for project development.

### Getting Started

Activate the virtual environment and install the dependencies.

```sh
./activate.sh
```

or

```ps1
./Activate.ps1
```

### Project Dependencies

- `pydantic_settings`
- `httpx`
- `questionary`
- `jira`

## Atlassian Document Format

This project tries to implement the [Atlassian Document Format](https://developer.atlassian.com/cloud/jira/platform/apis/document/atlassian-document-format/) as a way to serialize Jira tickets into Markdown format.
