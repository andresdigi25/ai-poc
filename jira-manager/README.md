# Jira Story Creator

This application helps you create Jira stories from a text file containing sprint planning information.

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your Jira credentials:
```
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_TOKEN=your-api-token
JIRA_PROJECT_KEY=PROJ
OLLAMA_MODEL=mistral  # Optional: specify the Ollama model to use
```

To get your Jira API token:
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a name and copy the token

## Input File Format

Create a text file with your stories in the following format:
```
Person Name
    Story description: story points
    Another story description: story points

Another Person
    Their story description: story points
```

Example:
```
John Doe
    Create login page: 3
    Implement user authentication: 5

Jane Smith
    Design database schema: 2
    Create API endpoints: 4
```

## Usage

### Simple Version
Run the simple version of the script:
```bash
python jira_story_creator.py
```

### CLI Version
The CLI version provides more control with separate commands:

1. Read and display stories from a file:
```bash
python jira_cli.py read-stories path/to/stories.txt
```

2. Create stories in Jira:
```bash
python jira_cli.py create-stories path/to/stories.txt
```

3. Validate existing stories:
```bash
python jira_cli.py validate-stories PROJ-123 PROJ-124 PROJ-125
```

### AI-Enhanced Version
The AI-enhanced version uses Ollama to automatically enhance stories with detailed descriptions, acceptance criteria, and technical considerations:

1. Read and display stories:
```bash
python jira_ai_creator.py read-stories path/to/stories.txt
```

2. Enhance stories with AI (without creating them):
```bash
python jira_ai_creator.py enhance-stories path/to/stories.txt
```

3. Create enhanced stories in Jira:
```bash
python jira_ai_creator.py create-stories path/to/stories.txt
```

Additional options for AI version:
- `--no-display`: Don't display the stories when reading (read-stories command)
- `--no-enhance`: Don't enhance stories with AI (create-stories command)
- `--no-confirm`: Don't ask for confirmation before creating stories (create-stories command)

Example workflow with AI enhancement:
```bash
# First, read and verify the stories
python jira_ai_creator.py read-stories stories.txt

# Enhance the stories with AI to see the improvements
python jira_ai_creator.py enhance-stories stories.txt

# If everything looks good, create the enhanced stories
python jira_ai_creator.py create-stories stories.txt
```

The AI-enhanced stories will include:
- Enhanced description
- Detailed acceptance criteria
- Technical considerations
- Dependencies (if any)

All this information will be added to the Jira story description, making it more comprehensive and ready for development.

The stories will be created in your Jira project's backlog with the specified assignees and story points. 