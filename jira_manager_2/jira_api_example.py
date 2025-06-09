#!/usr/bin/env python3
"""
Jira API Example - Creating and Managing Tickets

This script demonstrates how to use the Jira API to create and manage tickets (issues)
using the Python jira library.

Prerequisites:
- Python 3.6+
- jira package: pip install jira
- requests package: pip install requests
- dotenv package: pip install python-dotenv

To use this script:
1. Create a .env file with your Jira credentials (see below)
2. Run the script: python jira_api_example.py
"""

import os
import base64
import json
from typing import Dict, List, Optional, Union, Any
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# Optional: If you want to use the jira package (recommended for most use cases)
try:
    from jira import JIRA
    JIRA_PACKAGE_AVAILABLE = True
except ImportError:
    JIRA_PACKAGE_AVAILABLE = False
    print("JIRA package not available. Some examples will be skipped.")
    print("Install with: pip install jira")

# Load environment variables from .env file
load_dotenv()

# Jira connection details
JIRA_URL = os.getenv('JIRA_URL', 'https://your-domain.atlassian.net')
JIRA_EMAIL = os.getenv('JIRA_EMAIL', 'your-email@example.com')
JIRA_API_TOKEN = os.getenv('JIRA_TOKEN', 'your-api-token')
JIRA_PROJECT_KEY = os.getenv('JIRA_PROJECT_KEY', 'PROJ')

# Check if credentials are set
if JIRA_URL == 'https://your-domain.atlassian.net' or JIRA_API_TOKEN == 'your-api-token':
    print("Please set your Jira credentials in the .env file.")
    print("Example .env file:")
    print("JIRA_URL=https://your-domain.atlassian.net")
    print("JIRA_EMAIL=your-email@example.com")
    print("JIRA_TOKEN=your-api-token")
    print("JIRA_PROJECT_KEY=PROJ")
    print("\nTo get your Jira API token:")
    print("1. Go to https://id.atlassian.com/manage-profile/security/api-tokens")
    print("2. Click 'Create API token'")
    print("3. Give it a name and copy the token")


class JiraApiExample:
    """Class demonstrating various Jira API operations."""
    
    def __init__(self):
        """Initialize the Jira API connection."""
        self.base_url = JIRA_URL
        self.auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Initialize the JIRA client if available
        self.jira = None
        if JIRA_PACKAGE_AVAILABLE:
            self.jira = JIRA(
                server=self.base_url,
                basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN)
            )
    
    def create_issue_rest_api(self, summary: str, description: str, 
                             issue_type: str = "Task") -> Dict:
        """
        Create a new issue using the REST API directly.
        
        Args:
            summary: Issue summary/title
            description: Issue description
            issue_type: Issue type (Task, Bug, Story, etc.)
            
        Returns:
            Dict containing the response from the API
        """
        url = f"{self.base_url}/rest/api/3/issue"
        
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
        
        response = requests.post(
            url,
            data=payload,
            headers=self.headers,
            auth=self.auth
        )
        
        if response.status_code == 201:
            print(f"Issue created successfully: {response.json().get('key')}")
            return response.json()
        else:
            print(f"Failed to create issue: {response.status_code}")
            print(response.text)
            return {}
    
    def create_issue_with_jira_package(self, summary: str, description: str, 
                                      issue_type: str = "Task") -> Optional[Any]:
        """
        Create a new issue using the jira package.
        
        Args:
            summary: Issue summary/title
            description: Issue description
            issue_type: Issue type (Task, Bug, Story, etc.)
            
        Returns:
            The created issue object or None if creation failed
        """
        if not self.jira:
            print("JIRA package not available. Skipping.")
            return None
        
        try:
            issue_dict = {
                'project': {'key': JIRA_PROJECT_KEY},
                'summary': summary,
                'description': description,
                'issuetype': {'name': issue_type},
            }
            
            new_issue = self.jira.create_issue(fields=issue_dict)
            print(f"Issue created successfully: {new_issue.key}")
            return new_issue
        except Exception as e:
            print(f"Error creating issue: {str(e)}")
            return None
    
    def create_issue_with_custom_fields(self, summary: str, description: str,
                                       story_points: int = 3,
                                       priority: str = "Medium",
                                       components: List[str] = None) -> Optional[Any]:
        """
        Create a new issue with custom fields.
        
        Args:
            summary: Issue summary/title
            description: Issue description
            story_points: Story points (for Scrum projects)
            priority: Priority level
            components: List of component names
            
        Returns:
            The created issue object or None if creation failed
        """
        if not self.jira:
            print("JIRA package not available. Skipping.")
            return None
        
        try:
            issue_dict = {
                'project': {'key': JIRA_PROJECT_KEY},
                'summary': summary,
                'description': description,
                'issuetype': {'name': 'Story'},
                'priority': {'name': priority},
                # Story points - the field ID may vary in your Jira instance
                'customfield_10016': story_points
            }
            
            # Add components if provided
            if components:
                issue_dict['components'] = [{'name': c} for c in components]
            
            new_issue = self.jira.create_issue(fields=issue_dict)
            print(f"Issue with custom fields created successfully: {new_issue.key}")
            return new_issue
        except Exception as e:
            print(f"Error creating issue with custom fields: {str(e)}")
            return None
    
    def create_issue_with_attachment(self, summary: str, description: str,
                                    file_path: str) -> Optional[Any]:
        """
        Create a new issue and add an attachment.
        
        Args:
            summary: Issue summary/title
            description: Issue description
            file_path: Path to the file to attach
            
        Returns:
            The created issue object or None if creation failed
        """
        if not self.jira:
            print("JIRA package not available. Skipping.")
            return None
        
        try:
            # First create the issue
            issue_dict = {
                'project': {'key': JIRA_PROJECT_KEY},
                'summary': summary,
                'description': description,
                'issuetype': {'name': 'Task'},
            }
            
            new_issue = self.jira.create_issue(fields=issue_dict)
            print(f"Issue created successfully: {new_issue.key}")
            
            # Then add the attachment
            if os.path.exists(file_path):
                attachment = self.jira.add_attachment(
                    issue=new_issue.key,
                    attachment=file_path
                )
                print(f"Attachment added: {attachment.filename}")
            else:
                print(f"File not found: {file_path}")
            
            return new_issue
        except Exception as e:
            print(f"Error creating issue with attachment: {str(e)}")
            return None
    
    def create_linked_issues(self, summary1: str, summary2: str, 
                           link_type: str = "Relates") -> List[Optional[Any]]:
        """
        Create two issues and link them together.
        
        Args:
            summary1: Summary for the first issue
            summary2: Summary for the second issue
            link_type: Type of link (Relates, Blocks, etc.)
            
        Returns:
            List containing the two created issue objects
        """
        if not self.jira:
            print("JIRA package not available. Skipping.")
            return [None, None]
        
        try:
            # Create first issue
            issue1_dict = {
                'project': {'key': JIRA_PROJECT_KEY},
                'summary': summary1,
                'description': f"This issue is linked to {summary2}",
                'issuetype': {'name': 'Task'},
            }
            
            issue1 = self.jira.create_issue(fields=issue1_dict)
            print(f"First issue created: {issue1.key}")
            
            # Create second issue
            issue2_dict = {
                'project': {'key': JIRA_PROJECT_KEY},
                'summary': summary2,
                'description': f"This issue is linked to {summary1}",
                'issuetype': {'name': 'Task'},
            }
            
            issue2 = self.jira.create_issue(fields=issue2_dict)
            print(f"Second issue created: {issue2.key}")
            
            # Create link between issues
            self.jira.create_issue_link(
                type=link_type,
                inwardIssue=issue1.key,
                outwardIssue=issue2.key
            )
            print(f"Issues linked: {issue1.key} {link_type} {issue2.key}")
            
            return [issue1, issue2]
        except Exception as e:
            print(f"Error creating linked issues: {str(e)}")
            return [None, None]
    
    def update_issue(self, issue_key: str, summary: str = None, 
                    description: str = None, status: str = None) -> bool:
        """
        Update an existing issue.
        
        Args:
            issue_key: The issue key (e.g., PROJ-123)
            summary: New summary (optional)
            description: New description (optional)
            status: New status (optional)
            
        Returns:
            True if update was successful, False otherwise
        """
        if not self.jira:
            print("JIRA package not available. Skipping.")
            return False
        
        try:
            issue = self.jira.issue(issue_key)
            update_dict = {}
            
            if summary:
                update_dict['summary'] = summary
            
            if description:
                update_dict['description'] = description
            
            if update_dict:
                issue.update(fields=update_dict)
                print(f"Issue {issue_key} updated with new fields")
            
            # Update status if provided
            if status:
                transitions = self.jira.transitions(issue)
                transition_id = None
                
                for t in transitions:
                    if t['name'].lower() == status.lower():
                        transition_id = t['id']
                        break
                
                if transition_id:
                    self.jira.transition_issue(issue, transition_id)
                    print(f"Issue {issue_key} transitioned to {status}")
                else:
                    print(f"Transition to {status} not available")
            
            return True
        except Exception as e:
            print(f"Error updating issue: {str(e)}")
            return False
    
    def search_issues(self, jql_query: str) -> List[Any]:
        """
        Search for issues using JQL (Jira Query Language).
        
        Args:
            jql_query: JQL query string
            
        Returns:
            List of matching issues
        """
        if not self.jira:
            print("JIRA package not available. Skipping.")
            return []
        
        try:
            issues = self.jira.search_issues(jql_query)
            print(f"Found {len(issues)} issues matching query: {jql_query}")
            
            for issue in issues:
                print(f"  {issue.key}: {issue.fields.summary}")
            
            return issues
        except Exception as e:
            print(f"Error searching issues: {str(e)}")
            return []


def main():
    """Main function to demonstrate Jira API usage."""
    jira_example = JiraApiExample()
    
    print("\n=== Creating a Basic Issue (REST API) ===")
    jira_example.create_issue_rest_api(
        summary="Test Issue via REST API",
        description="This is a test issue created using the Jira REST API directly.",
        issue_type="Task"
    )
    
    if JIRA_PACKAGE_AVAILABLE:
        print("\n=== Creating a Basic Issue (jira package) ===")
        issue1 = jira_example.create_issue_with_jira_package(
            summary="Test Issue via jira package",
            description="This is a test issue created using the jira package.",
            issue_type="Task"
        )
        
        print("\n=== Creating an Issue with Custom Fields ===")
        issue2 = jira_example.create_issue_with_custom_fields(
            summary="Test Story with Custom Fields",
            description="This is a test story with custom fields like story points.",
            story_points=5,
            priority="High",
            components=["Backend", "API"]
        )
        
        print("\n=== Creating Linked Issues ===")
        issues = jira_example.create_linked_issues(
            summary1="Parent Task",
            summary2="Subtask",
            link_type="Relates"
        )
        
        print("\n=== Updating an Issue ===")
        if issue1:
            jira_example.update_issue(
                issue_key=issue1.key,
                summary="Updated Test Issue",
                description="This description has been updated.",
                status="In Progress"  # This may need to be adjusted based on your workflow
            )
        
        print("\n=== Searching for Issues ===")
        jira_example.search_issues(f"project = {JIRA_PROJECT_KEY} AND created >= -1d ORDER BY created DESC")


if __name__ == "__main__":
    main()
