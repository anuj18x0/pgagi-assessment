# pgagi Backend

FastAPI backend for the pgagi project.

## Tech Stack
- **FastAPI**: Modern, fast (high-performance) web framework.
- **Poetry**: Dependency management.
- **Pydantic v2**: Data validation and settings management.
- **Uvicorn**: Lightning-fast ASGI server.

## Getting Started

### Prerequisites
- Python 3.11+
- [Poetry](https://python-poetry.org/docs/#installation)

### Installation
```bash
cd backend
poetry install
```

### Running the Application
```bash
poetry run uvicorn app.main:app --reload
```

## API Documentation
Once the server is running, visit:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
