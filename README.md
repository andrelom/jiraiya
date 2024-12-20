# Jiraiya

A tool designed to crawl Jira tickets and export them as local files in JSON and Markdown formats.

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

## Atlassian Document Format

This project tries to implement the [Atlassian Document Format](https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/) as a way to serialize Jira tickets into Markdown format.
