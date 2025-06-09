# Jira API Examples

This repository contains examples of how to create tickets in Jira using the Jira API with Python.

## Overview

This repository includes two main examples:

1. `create_jira_ticket.py` - A simple script that demonstrates how to create a single Jira ticket using just the REST API
2. `jira_api_example.py` - A comprehensive example that demonstrates various ways to interact with the Jira API, including:

- Creating basic issues/tickets
- Creating issues with custom fields
- Adding attachments to issues
- Creating linked issues
- Updating existing issues
- Searching for issues using JQL (Jira Query Language)

The examples use both the direct REST API approach and the Python `jira` package, which provides a more convenient interface.

## Prerequisites

- Python 3.6+
- A Jira account with API access
- Required Python packages:
  - `jira`: High-level Jira API wrapper
  - `requests`: For direct REST API calls
  - `python-dotenv`: For loading environment variables

## Installation

1. Clone this repository or download the files.

2. Install the required packages:

```bash
pip install jira requests python-dotenv
```

## Configuration

1. Create a `.env` file in the same directory as the script with the following content:

```
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_TOKEN=your-api-token
JIRA_PROJECT_KEY=PROJ
```

Replace the values with your actual Jira information:
- `JIRA_URL`: Your Jira instance URL
- `JIRA_EMAIL`: Your Jira account email
- `JIRA_TOKEN`: Your Jira API token
- `JIRA_PROJECT_KEY`: The key of the project where you want to create issues

### Getting a Jira API Token

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a name (e.g., "Jira API Examples")
4. Copy the token and paste it in your `.env` file

## Usage

Run either of the example scripts:

```bash
# Simple ticket creation example
python create_jira_ticket.py

# Comprehensive examples
python jira_api_example.py
```

The `jira_api_example.py` script will execute all the examples sequentially, creating several test issues in your Jira project.

## Simple Example

The `create_jira_ticket.py` script provides a minimal example of creating a Jira ticket using only the REST API and the `requests` library. This is useful if you just need basic ticket creation functionality without additional dependencies.

```python
create_jira_ticket(
    summary="API Test Ticket",
    description="This ticket was created using the Jira REST API.",
    issue_type="Task"
)
```

## Comprehensive Examples

### 1. Creating a Basic Issue (REST API)

This example shows how to create a simple task using direct REST API calls with the `requests` library:

```python
jira_example.create_issue_rest_api(
    summary="Test Issue via REST API",
    description="This is a test issue created using the Jira REST API directly.",
    issue_type="Task"
)
```

### 2. Creating a Basic Issue (jira package)

This example demonstrates creating a task using the `jira` package, which provides a more convenient interface:

```python
issue1 = jira_example.create_issue_with_jira_package(
    summary="Test Issue via jira package",
    description="This is a test issue created using the jira package.",
    issue_type="Task"
)
```

### 3. Creating an Issue with Custom Fields

This example shows how to create a story with custom fields like story points, priority, and components:

```python
issue2 = jira_example.create_issue_with_custom_fields(
    summary="Test Story with Custom Fields",
    description="This is a test story with custom fields like story points.",
    story_points=5,
    priority="High",
    components=["Backend", "API"]
)
```

### 4. Creating Linked Issues

This example demonstrates creating two related issues and linking them together:

```python
issues = jira_example.create_linked_issues(
    summary1="Parent Task",
    summary2="Subtask",
    link_type="Relates"
)
```

### 5. Updating an Issue

This example shows how to update an existing issue's fields and status:

```python
jira_example.update_issue(
    issue_key=issue1.key,
    summary="Updated Test Issue",
    description="This description has been updated.",
    status="In Progress"
)
```

### 6. Searching for Issues

This example demonstrates how to search for issues using JQL (Jira Query Language):

```python
jira_example.search_issues(
    f"project = {JIRA_PROJECT_KEY} AND created >= -1d ORDER BY created DESC"
)
```

## Customizing the Examples

### Custom Fields

The field ID for story points (`customfield_10016`) may be different in your Jira instance. To find the correct field ID:

1. Create a test issue with story points in your Jira instance
2. Use the Jira API to get the issue details and look for the field ID that contains the story points value

### Issue Types and Workflows

The available issue types and workflow transitions depend on your Jira configuration. You may need to adjust the examples to match your specific setup.

## Additional Resources

- [Jira REST API Documentation](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/)
- [Python Jira Library Documentation](https://jira.readthedocs.io/en/master/)
- [Jira Query Language (JQL) Reference](https://support.atlassian.com/jira-software-cloud/docs/advanced-search-reference-jql-fields/)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
