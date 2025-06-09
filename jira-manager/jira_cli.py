import os
from typing import List, Dict, Optional
from jira import JIRA
from dotenv import load_dotenv
import typer
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm

app = typer.Typer(help="Jira Story Creator CLI")
console = Console()

class JiraStoryManager:
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
                
                if not line.startswith(' '):
                    current_assignee = line
                else:
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

    def create_stories(self, stories: List[Dict]) -> List[str]:
        created_issues = []
        for story in stories:
            issue_dict = {
                'project': {'key': self.project_key},
                'summary': story['description'],
                'description': f"Assigned to: {story['assignee']}\nStory Points: {story['story_points']}",
                'issuetype': {'name': 'Story'},
                'customfield_10016': int(story['story_points'])
            }
            
            try:
                new_issue = self.jira.create_issue(fields=issue_dict)
                created_issues.append(new_issue.key)
            except Exception as e:
                console.print(f"[red]Error creating story '{story['description']}': {str(e)}[/red]")
        
        return created_issues

    def validate_stories(self, issue_keys: List[str]) -> Dict[str, bool]:
        validation_results = {}
        for key in issue_keys:
            try:
                issue = self.jira.issue(key)
                validation_results[key] = {
                    'exists': True,
                    'summary': issue.fields.summary,
                    'assignee': issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned',
                    'story_points': getattr(issue.fields, 'customfield_10016', 'Not set')
                }
            except Exception as e:
                validation_results[key] = {
                    'exists': False,
                    'error': str(e)
                }
        return validation_results

def display_stories(stories: List[Dict], title: str = "Stories"):
    table = Table(title=title)
    table.add_column("Assignee", style="cyan")
    table.add_column("Description", style="green")
    table.add_column("Story Points", style="yellow")
    
    for story in stories:
        table.add_row(
            story['assignee'],
            story['description'],
            story['story_points']
        )
    
    console.print(table)

def display_validation_results(results: Dict[str, Dict]):
    table = Table(title="Validation Results")
    table.add_column("Issue Key", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="yellow")
    
    for key, result in results.items():
        if result['exists']:
            table.add_row(
                key,
                "[green]✓ Valid[/green]",
                f"Summary: {result['summary']}\nAssignee: {result['assignee']}\nStory Points: {result['story_points']}"
            )
        else:
            table.add_row(
                key,
                "[red]✗ Invalid[/red]",
                f"Error: {result['error']}"
            )
    
    console.print(table)

@app.command()
def read_stories(
    file_path: str = typer.Argument(..., help="Path to the stories file"),
    display: bool = typer.Option(True, help="Display the parsed stories")
):
    """Read and parse stories from a file."""
    try:
        manager = JiraStoryManager()
        stories = manager.parse_stories_file(file_path)
        console.print(f"\n[green]Successfully parsed {len(stories)} stories from {file_path}[/green]")
        
        if display:
            display_stories(stories)
        
        return stories
    except Exception as e:
        console.print(f"[red]Error reading stories: {str(e)}[/red]")
        raise typer.Exit(1)

@app.command()
def create_stories(
    file_path: str = typer.Argument(..., help="Path to the stories file"),
    confirm: bool = typer.Option(True, help="Ask for confirmation before creating stories")
):
    """Create stories in Jira from a file."""
    try:
        manager = JiraStoryManager()
        stories = manager.parse_stories_file(file_path)
        
        display_stories(stories, "Stories to be created")
        
        if confirm and not Confirm.ask("Do you want to create these stories?"):
            console.print("[yellow]Operation cancelled by user[/yellow]")
            return
        
        created_issues = manager.create_stories(stories)
        console.print(f"\n[green]Successfully created {len(created_issues)} stories[/green]")
        
        return created_issues
    except Exception as e:
        console.print(f"[red]Error creating stories: {str(e)}[/red]")
        raise typer.Exit(1)

@app.command()
def validate_stories(
    issue_keys: List[str] = typer.Argument(..., help="List of Jira issue keys to validate")
):
    """Validate that stories exist in Jira."""
    try:
        manager = JiraStoryManager()
        results = manager.validate_stories(issue_keys)
        display_validation_results(results)
        
        valid_count = sum(1 for result in results.values() if result['exists'])
        console.print(f"\n[green]Validation complete: {valid_count}/{len(issue_keys)} stories are valid[/green]")
        
        return results
    except Exception as e:
        console.print(f"[red]Error validating stories: {str(e)}[/red]")
        raise typer.Exit(1)

if __name__ == "__main__":
    app() 