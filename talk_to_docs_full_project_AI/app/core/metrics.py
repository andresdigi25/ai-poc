from prometheus_client import Counter, Histogram, make_asgi_app
from fastapi import FastAPI

# Document processing metrics
DOCUMENTS_PROCESSED = Counter(
    'documents_processed_total',
    'Total number of documents processed',
    ['status']
)

PROCESSING_TIME = Histogram(
    'document_processing_seconds',
    'Time spent processing documents',
    ['operation']
)

# API metrics
API_REQUESTS = Counter(
    'api_requests_total',
    'Total number of API requests',
    ['endpoint', 'method', 'status']
)

API_LATENCY = Histogram(
    'api_request_duration_seconds',
    'API request latency in seconds',
    ['endpoint', 'method']
)

def setup_metrics(app: FastAPI):
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app) 