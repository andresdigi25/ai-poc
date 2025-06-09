import os
from typing import List, Dict, Optional
from jira import JIRA
from dotenv import load_dotenv
import typer
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm
import ollama
import json

app = typer.Typer(help="Jira Story Creator with AI Enhancement")
console = Console()

class JiraAIStoryManager:
    def __init__(self):
        load_dotenv()
        self.jira_url = os.getenv('JIRA_URL')
        self.jira_email = os.getenv('JIRA_EMAIL')
        self.jira_token = os.getenv('JIRA_TOKEN')
        self.project_key = os.getenv('JIRA_PROJECT_KEY')
        self.model_name = os.getenv('OLLAMA_MODEL', 'mistral')
        
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
                            'story_points': story_points,
                            'enhanced': False
                        })
        
        return stories

    def enhance_story_with_ai(self, story: Dict) -> Dict:
        if story['enhanced']:
            return story

        prompt = f"""As a product manager, enhance the following user story with detailed acceptance criteria and technical considerations.
        The story is: "{story['description']}" with {story['story_points']} story points.
        
        Provide the response in the following JSON format:
        {{
            "enhanced_description": "A more detailed description of the story",
            "acceptance_criteria": ["List of acceptance criteria"],
            "technical_considerations": ["List of technical considerations"],
            "dependencies": ["List of dependencies if any"]
        }}
        
        Keep the response concise but comprehensive."""

        try:
            response = ollama.generate(
                model=self.model_name,
                prompt=prompt,
                stream=False
            )
            
            # Extract JSON from the response
            try:
                enhanced_data = json.loads(response['response'])
                story.update({
                    'enhanced_description': enhanced_data.get('enhanced_description', story['description']),
                    'acceptance_criteria': enhanced_data.get('acceptance_criteria', []),
                    'technical_considerations': enhanced_data.get('technical_considerations', []),
                    'dependencies': enhanced_data.get('dependencies', []),
                    'enhanced': True
                })
            except json.JSONDecodeError:
                console.print(f"[yellow]Warning: Could not parse AI response for story: {story['description']}[/yellow]")
                story['enhanced'] = False
                
        except Exception as e:
            console.print(f"[red]Error enhancing story with AI: {str(e)}[/red]")
            story['enhanced'] = False
        
        return story

    def create_stories(self, stories: List[Dict]) -> List[str]:
        created_issues = []
        for story in stories:
            # Create a detailed description combining all enhanced information
            description_parts = [
                f"Original Story: {story['description']}",
                f"Story Points: {story['story_points']}",
                f"Assignee: {story['assignee']}"
            ]
            
            if story['enhanced']:
                description_parts.extend([
                    "\nEnhanced Description:",
                    story['enhanced_description'],
                    "\nAcceptance Criteria:",
                    *[f"- {criteria}" for criteria in story['acceptance_criteria']],
                    "\nTechnical Considerations:",
                    *[f"- {consideration}" for consideration in story['technical_considerations']],
                    "\nDependencies:",
                    *[f"- {dependency}" for dependency in story['dependencies']]
                ])
            
            issue_dict = {
                'project': {'key': self.project_key},
                'summary': story['description'],
                'description': '\n'.join(description_parts),
                'issuetype': {'name': 'Story'},
                'customfield_10016': int(story['story_points'])
            }
            
            try:
                new_issue = self.jira.create_issue(fields=issue_dict)
                created_issues.append(new_issue.key)
            except Exception as e:
                console.print(f"[red]Error creating story '{story['description']}': {str(e)}[/red]")
        
        return created_issues

def display_stories(stories: List[Dict], title: str = "Stories"):
    table = Table(title=title)
    table.add_column("Assignee", style="cyan")
    table.add_column("Description", style="green")
    table.add_column("Story Points", style="yellow")
    table.add_column("Enhanced", style="magenta")
    
    for story in stories:
        table.add_row(
            story['assignee'],
            story['description'],
            story['story_points'],
            "✓" if story.get('enhanced', False) else "✗"
        )
    
    console.print(table)

def display_enhanced_story(story: Dict):
    console.print("\n[bold cyan]Enhanced Story Details[/bold cyan]")
    console.print(f"[bold]Original Description:[/bold] {story['description']}")
    console.print(f"[bold]Story Points:[/bold] {story['story_points']}")
    console.print(f"[bold]Assignee:[/bold] {story['assignee']}")
    
    if story.get('enhanced', False):
        console.print("\n[bold green]Enhanced Description:[/bold green]")
        console.print(story['enhanced_description'])
        
        console.print("\n[bold yellow]Acceptance Criteria:[/bold yellow]")
        for criteria in story['acceptance_criteria']:
            console.print(f"- {criteria}")
        
        console.print("\n[bold magenta]Technical Considerations:[/bold magenta]")
        for consideration in story['technical_considerations']:
            console.print(f"- {consideration}")
        
        if story['dependencies']:
            console.print("\n[bold red]Dependencies:[/bold red]")
            for dependency in story['dependencies']:
                console.print(f"- {dependency}")

@app.command()
def read_stories(
    file_path: str = typer.Argument(..., help="Path to the stories file"),
    display: bool = typer.Option(True, help="Display the parsed stories")
):
    """Read and parse stories from a file."""
    try:
        manager = JiraAIStoryManager()
        stories = manager.parse_stories_file(file_path)
        console.print(f"\n[green]Successfully parsed {len(stories)} stories from {file_path}[/green]")
        
        if display:
            display_stories(stories)
        
        return stories
    except Exception as e:
        console.print(f"[red]Error reading stories: {str(e)}[/red]")
        raise typer.Exit(1)

@app.command()
def enhance_stories(
    file_path: str = typer.Argument(..., help="Path to the stories file"),
    display: bool = typer.Option(True, help="Display enhanced stories")
):
    """Enhance stories using AI."""
    try:
        manager = JiraAIStoryManager()
        stories = manager.parse_stories_file(file_path)
        
        with console.status("[bold green]Enhancing stories with AI..."):
            for i, story in enumerate(stories, 1):
                console.print(f"\n[cyan]Enhancing story {i}/{len(stories)}: {story['description']}[/cyan]")
                enhanced_story = manager.enhance_story_with_ai(story)
                if display:
                    display_enhanced_story(enhanced_story)
        
        console.print(f"\n[green]Successfully enhanced {len(stories)} stories[/green]")
        return stories
    except Exception as e:
        console.print(f"[red]Error enhancing stories: {str(e)}[/red]")
        raise typer.Exit(1)

@app.command()
def create_stories(
    file_path: str = typer.Argument(..., help="Path to the stories file"),
    enhance: bool = typer.Option(True, help="Enhance stories with AI before creating"),
    confirm: bool = typer.Option(True, help="Ask for confirmation before creating stories")
):
    """Create stories in Jira from a file."""
    try:
        manager = JiraAIStoryManager()
        stories = manager.parse_stories_file(file_path)
        
        if enhance:
            with console.status("[bold green]Enhancing stories with AI..."):
                for story in stories:
                    manager.enhance_story_with_ai(story)
        
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

if __name__ == "__main__":
    app() 