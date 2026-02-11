
# SageScript Middleware

AI-powered test case generation middleware built with FastAPI, PostgreSQL, and Redis Queue (RQ). This service manages test case generation jobs, prioritization, and storage, integrating with modern AI models.

## Overview

SageScript Middleware is a backend service for automated test case generation and management. It exposes REST API endpoints for job scheduling, test data extraction, prioritization, and result storage in PostgreSQL.

## Features

- **FastAPI**: Modern Python web framework for APIs
- **Redis Queue (RQ)**: Asynchronous job processing for scalability
- **PostgreSQL**: Persistent data storage
- **AI Model Integration**: LangChain, OpenAI, Google GenAI
- **Test Case Management**: Extract, prioritize, and store test cases
- **CORS Support**: Multi-origin API access
- **Job Dashboard**: Track job status and statistics

## Project Structure

```
├── app.py                # Main FastAPI application and API endpoints
├── db.py                 # PostgreSQL connection utilities
├── rq_config.py          # Redis Queue configuration
├── requirements.txt      # Python dependencies
├── Sample1.ipynb         # Example Jupyter notebook
├── schemas/
│   └── test_case.py      # Pydantic models for test cases
└── tools/
   ├── extract_rows.py      # Extract test cases from DB rows
   ├── priority_summary.py  # Summarize/prioritize test cases
   ├── save_job.py          # Save job and user stories to DB
   └── store_test_cases.py  # Store validated test cases as JSON
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


<!-- config.py is not present; configuration is via environment variables and .env file. -->

### `db.py`
PostgreSQL database connection and query utilities using psycopg.

### `rq_config.py`
Redis Queue configuration for async job processing.


### `tools/`
Utility modules:
- **extract_rows.py**: Extract and flatten test cases from DB rows (handles nested/JSON)
- **priority_summary.py**: Summarize and count test cases by priority
- **save_job.py**: Save scheduled jobs and user stories to the database
- **store_test_cases.py**: Validate and store test cases as JSON files


### `schemas/`
Pydantic models for data validation:
- **test_case.py**: Test case and test case list schema

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

Key endpoints (see `/docs` for full details):
- `POST /api/generate-test-cases`: Create a new test case generation job
- `GET /api/jobs`: List all jobs
- `GET /api/jobs/{job_id}`: Get job details and results
- `POST /api/jobs/{job_id}/regenerate`: Re-queue a job for processing
- `DELETE /api/jobs/{job_id}`: Delete a job
- `GET /api/dashboard/{user_id}`: Get dashboard stats for a user


## Environment Variables

```
DATABASE_URL   # PostgreSQL connection string
REDIS_URL      # Redis connection string
OPENAI_API_KEY # OpenAI API key (optional)
GOOGLE_API_KEY # Google GenAI API key (optional)
LOG_LEVEL      # Logging level (optional)
```


## Development

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

**Last Updated**: February 11, 2026
