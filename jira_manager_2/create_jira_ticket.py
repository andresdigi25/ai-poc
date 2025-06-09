#!/usr/bin/env python3
"""
Simple Jira Ticket Creation Example

This script demonstrates how to create a single Jira ticket using the REST API
without any additional packages beyond requests.

Usage:
    python create_jira_ticket.py

Requirements:
    - requests
    - python-dotenv (optional, for loading .env file)
"""

import os
import json
import requests
from requests.auth import HTTPBasicAuth

# Try to load from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("python-dotenv not installed. Using environment variables directly.")

# Jira connection details
JIRA_URL = os.getenv('JIRA_URL', 'https://your-domain.atlassian.net')
JIRA_EMAIL = os.getenv('JIRA_EMAIL', 'your-email@example.com')
JIRA_API_TOKEN = os.getenv('JIRA_TOKEN', 'your-api-token')
JIRA_PROJECT_KEY = os.getenv('JIRA_PROJECT_KEY', 'PROJ')

def create_jira_ticket(summary, description, issue_type="Task"):
    """
    Create a new Jira ticket using the REST API.
    
    Args:
        summary (str): The ticket summary/title
        description (str): The ticket description
        issue_type (str): The type of issue (Task, Bug, Story, etc.)
        
    Returns:
        dict: The response from the API if successful, empty dict otherwise
    """
    url = f"{JIRA_URL}/rest/api/3/issue"
    
    # Authentication
    auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
    
    # Headers
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # Payload with ticket details
    payload = json.dumps({
        "fields": {
            "project": {
                "key": JIRA_PROJECT_KEY
            },
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": description
                            }
                        ]
                    }
                ]
            },
            "issuetype": {
                "name": issue_type
            }
        }
    })
    
    # Make the API request
    response = requests.post(
        url,
        data=payload,
        headers=headers,
        auth=auth
    )
    
    # Check if the request was successful
    if response.status_code == 201:
        print(f"✅ Ticket created successfully!")
        print(f"   Key: {response.json().get('key')}")
        print(f"   URL: {JIRA_URL}/browse/{response.json().get('key')}")
        return response.json()
    else:
        print(f"❌ Failed to create ticket: {response.status_code}")
        print(f"   Error: {response.text}")
        return {}

def main():
    """Main function to demonstrate Jira ticket creation."""
    # Check if credentials are set
    if JIRA_URL == 'https://your-domain.atlassian.net' or JIRA_API_TOKEN == 'your-api-token':
        print("⚠️  Please set your Jira credentials in the .env file or environment variables.")
        print("   See .env.example for the required variables.")
        return
    
    print("🎫 Creating a Jira ticket...")
    
    # Example ticket details
    summary = "API Test Ticket"
    description = "This ticket was created using the Jira REST API."
    issue_type = "Task"  # Common types: Task, Bug, Story, Epic
    
    # Create the ticket
    create_jira_ticket(summary, description, issue_type)

if __name__ == "__main__":
    main()
