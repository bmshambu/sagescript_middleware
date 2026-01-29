# SageScript Middleware

An AI-powered test case generation middleware service built with FastAPI and Redis Queue (RQ). This service processes test case generation requests and manages job scheduling for automated test case creation.

## Overview

SageScript Middleware is a backend service that facilitates test case generation using AI models. It provides REST API endpoints for managing test case generation jobs, extracting test data, and storing results in a PostgreSQL database.

## Features

- **FastAPI Web Framework**: Modern, fast Python web framework for building APIs
- **Redis Queue Integration**: Asynchronous job processing with RQ for scalable task handling
- **Database Support**: PostgreSQL integration for persistent data storage
- **AI-Powered Generation**: Integration with LangChain and OpenAI/Google GenAI models
- **Test Case Management**: Extract, prioritize, and store test cases
- **CORS Enabled**: Cross-origin resource sharing for multi-origin requests

## Project Structure

```
sagescript_middleware/
├── app.py                    # Main FastAPI application
├── config.py                 # Application configuration
├── db.py                     # Database connection and utilities
├── rq_config.py             # Redis Queue configuration
├── requirements.txt         # Python dependencies
├── schemas/
│   └── test_case.py        # Test case data models
└── tools/
    ├── extract_rows.py     # Extract test cases from data
    ├── priority_summary.py # Summarize and prioritize test cases
    ├── save_job.py         # Save job metadata
    └── store_test_cases.py # Store test cases in database
```

## Prerequisites

- Python 3.8+
- Redis server (for job queue)
- PostgreSQL database
- API keys for OpenAI and/or Google GenAI (if using those models)

## Installation

1. **Clone the repository**
   ```bash
   cd sagescript_middleware
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file with required configuration:
   ```
   DATABASE_URL=postgresql://user:password@localhost/dbname
   REDIS_URL=redis://localhost:6379
   OPENAI_API_KEY=your_openai_key
   GOOGLE_API_KEY=your_google_key
   ```

4. **Initialize the database**
   ```bash
   python db.py
   ```

## Running the Service

### Start the FastAPI Server

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

Or with auto-reload for development:

```bash
uvicorn app:app --reload
```

### Start the Redis Queue Worker

In a separate terminal:

```bash
python -m rq worker test_generation_queue -c rq_config
```

### Access the API

- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Alternative Documentation**: http://localhost:8000/redoc (ReDoc)

## Key Components

### `app.py`
Main FastAPI application with REST API endpoints for:
- Test case generation job creation
- Job status tracking
- Test data extraction and processing
- Priority summarization

### `config.py`
Application configuration management including database URLs, API keys, and service settings.

### `db.py`
PostgreSQL database connection and query utilities using psycopg.

### `rq_config.py`
Redis Queue configuration for async job processing.

### `tools/`
Utility modules:
- **extract_rows.py**: Extract test cases from raw data sources
- **priority_summary.py**: Analyze and prioritize test cases
- **save_job.py**: Persist job information to database
- **store_test_cases.py**: Store generated test cases in PostgreSQL

### `schemas/`
Pydantic models for data validation:
- **test_case.py**: Test case data model definition

## Dependencies

Key Python packages:
- **FastAPI**: Web framework
- **Uvicorn**: ASGI server
- **RQ**: Redis Queue for job processing
- **Redis**: In-memory data store
- **psycopg**: PostgreSQL adapter
- **Pandas**: Data manipulation
- **LangChain**: AI model integration
- **langchain_openai**: OpenAI API integration
- **langchain_google_genai**: Google GenAI integration
- **Streamlit**: Data visualization (optional)
- **sentence-transformers**: Semantic similarity

## API Endpoints

Common endpoints (detailed in Swagger UI at `/docs`):
- `POST /generate-test-cases`: Create a new test case generation job
- `GET /job/{job_id}`: Get job status and results
- `POST /extract-test-cases`: Extract test cases from data
- `POST /summarize-priorities`: Analyze and prioritize test cases

## Environment Variables

```
DATABASE_URL          # PostgreSQL connection string
REDIS_URL            # Redis connection string
OPENAI_API_KEY       # OpenAI API key
GOOGLE_API_KEY       # Google GenAI API key
LOG_LEVEL            # Logging level (DEBUG, INFO, WARNING, ERROR)
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black .
```

### Linting

```bash
flake8 .
```

## Troubleshooting

### Redis Connection Issues
- Ensure Redis server is running: `redis-cli ping`
- Check REDIS_URL environment variable

### Database Connection Issues
- Verify PostgreSQL is running
- Check DATABASE_URL credentials and host
- Ensure the database exists

### Job Processing Issues
- Check Redis Queue worker is running
- Monitor logs: `python -m rq info`
- View failed jobs: `python -m rq failed`

## Performance Considerations

- Use connection pooling for database operations
- Monitor Redis memory usage
- Implement job timeouts for long-running processes
- Use background tasks for non-critical operations

## Security

- Keep API keys in environment variables
- Use HTTPS in production
- Implement authentication for API endpoints
- Validate all user inputs
- Use database parameterized queries (psycopg handles this)

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

[Add your license here]

## Support

For issues and questions, please open an issue in the project repository.

## Related Projects

- Test Case Generation Service (main orchestrator)
- SageScript Frontend (React/Angular UI)

---

**Last Updated**: January 29, 2026
