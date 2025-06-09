import os
from typing import List, Dict
from jira import JIRA
from dotenv import load_dotenv

class JiraStoryCreator:
    def __init__(self):
        load_dotenv()
        self.jira_url = os.getenv('JIRA_URL')
        self.jira_email = os.getenv('JIRA_EMAIL')
        self.jira_token = os.getenv('JIRA_TOKEN')
        self.project_key = os.getenv('JIRA_PROJECT_KEY')
        
        if not all([self.jira_url, self.jira_email, self.jira_token, self.project_key]):
            raise ValueError("Missing required environment variables. Please check your .env file.")
        
        self.jira = JIRA(
            server=self.jira_url,
            basic_auth=(self.jira_email, self.jira_token)
        )

    def parse_stories_file(self, file_path: str) -> List[Dict]:
        stories = []
        current_assignee = None
        
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                
                # If line doesn't start with spaces, it's an assignee
                if not line.startswith(' '):
                    current_assignee = line
                else:
                    # Parse story line
                    parts = line.strip().split(':')
                    if len(parts) == 2:
                        description = parts[0].strip()
                        story_points = parts[1].strip()
                        stories.append({
                            'assignee': current_assignee,
                            'description': description,
                            'story_points': story_points
                        })
        
        return stories

    def create_stories(self, stories: List[Dict]):
        for story in stories:
            issue_dict = {
                'project': {'key': self.project_key},
                'summary': story['description'],
                'description': f"Assigned to: {story['assignee']}\nStory Points: {story['story_points']}",
                'issuetype': {'name': 'Story'},
                'customfield_10016': int(story['story_points'])  # Assuming 10016 is the Story Points field ID
            }
            
            try:
                new_issue = self.jira.create_issue(fields=issue_dict)
                print(f"Created story: {new_issue.key} - {story['description']}")
            except Exception as e:
                print(f"Error creating story '{story['description']}': {str(e)}")

def main():
    # Create .env file if it doesn't exist
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write("""JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_TOKEN=your-api-token
JIRA_PROJECT_KEY=PROJ""")
        print("Created .env file. Please fill in your Jira credentials.")
        return

    creator = JiraStoryCreator()
    
    # Get the input file path from user
    file_path = input("Enter the path to your stories file: ")
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    stories = creator.parse_stories_file(file_path)
    print(f"\nFound {len(stories)} stories to create.")
    
    confirm = input("Do you want to create these stories in Jira? (yes/no): ")
    if confirm.lower() == 'yes':
        creator.create_stories(stories)
        print("\nStories creation completed!")
    else:
        print("Operation cancelled.")

if __name__ == "__main__":
    main() 