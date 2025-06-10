# Talk to Docs

An intelligent document processing system that extracts, summarizes, and analyzes PDF documents.

## Features

- PDF document processing from FTP server
- Text and image extraction using Hugging Face models
- Document summarization using Ollama
- Email notifications with summaries and extracted images
- N8N workflow orchestration
- FastAPI backend service
- CLI tool for direct document processing
- Logging and metrics tracking
- PostgreSQL database for document metadata and summaries
- Streamlit dashboard for visualization

## Tech Stack

- N8N: Workflow orchestration
- LangChain: Document processing framework
- Ollama: Local LLM for summarization
- Hugging Face: Document processing models
- FastAPI: Backend API
- Docker Compose: Containerization
- PostgreSQL: Database
- Streamlit: Dashboard

## Project Structure

```
.
├── app/
│   ├── api/            # FastAPI application
│   ├── cli/            # CLI tool
│   ├── core/           # Core business logic
│   ├── models/         # Database models
│   └── utils/          # Utility functions
├── docker/             # Docker configuration files
├── n8n/               # N8N workflow definitions
├── scripts/           # Utility scripts
└── tests/             # Test files
```

## Setup

1. Clone the repository
2. Create a `.env` file based on `.env.example`
3. Run `docker-compose up -d`

## Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the FastAPI server:
```bash
uvicorn app.api.main:app --reload
```

3. Run the CLI tool:
```bash
python -m app.cli.main
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

MIT