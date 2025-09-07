# Active Recall Backend API

A FastAPI-based backend service for the Active Recall learning application, providing AI-powered flashcard generation, adaptive quizzes, and spaced repetition using the SM-2 algorithm.

## Features

- **Content Ingestion**: PDF, URL, and text processing with OCR fallback
- **AI-Powered Flashcard Generation**: Using Gemini API with RAG (Retrieval-Augmented Generation)
- **Adaptive Quizzes**: Intelligent quiz generation with LLM-based grading
- **Spaced Repetition**: SM-2 algorithm implementation for optimal learning schedules
- **Vector Search**: FAISS-based semantic search for content retrieval
- **User-Specific API Keys**: Secure per-user Gemini API key handling

## Architecture

```
backend/
├── app/
│   ├── api/v1/          # API endpoints
│   │   ├── ingest.py    # Content ingestion
│   │   ├── generate.py  # Flashcard generation
│   │   ├── quiz.py      # Quiz management
│   │   ├── review.py    # Spaced repetition
│   │   └── health.py    # Health checks
│   ├── core/            # Core services
│   │   ├── models.py    # Database models
│   │   ├── database.py  # Database configuration
│   │   ├── settings.py  # Configuration
│   │   ├── pdf.py       # PDF processing
│   │   ├── ocr.py       # OCR processing
│   │   ├── web.py       # Web scraping
│   │   ├── chunk.py     # Text chunking
│   │   ├── embed.py     # Embedding service
│   │   ├── rag.py       # RAG service
│   │   ├── llm.py       # LLM service
│   │   ├── prompts.py   # Prompt templates
│   │   ├── grading.py   # Answer grading
│   │   └── sm2.py       # SM-2 algorithm
│   └── main.py          # FastAPI application
├── tests/               # Test suite
├── Dockerfile           # Container configuration
├── docker-compose.yml   # Multi-service setup
└── requirements.txt     # Python dependencies
```

## Quick Start

### Using Docker Compose (Recommended)

1. **Clone and setup**:
   ```bash
   cd backend
   cp env.example .env
   # Edit .env with your configuration
   ```

2. **Start services**:
   ```bash
   docker-compose up -d
   ```

3. **Access the API**:
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

### Manual Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup database**:
   ```bash
   # Start PostgreSQL
   # Create database: active_recall
   ```

3. **Configure environment**:
   ```bash
   cp env.example .env
   # Edit .env with your settings
   ```

4. **Run the application**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## API Endpoints

### Content Ingestion

- `POST /api/v1/ingest` - Ingest content (PDF, URL, text)
- `GET /api/v1/ingest/collections` - List collections
- `GET /api/v1/ingest/collections/{id}` - Get collection details

### Flashcard Generation

- `POST /api/v1/generate/flashcards` - Generate flashcards from collection
- `GET /api/v1/generate/flashcards/{collection_id}` - Get collection flashcards
- `DELETE /api/v1/generate/flashcards/{flashcard_id}` - Delete flashcard

### Quiz Management

- `POST /api/v1/quiz/start` - Start new quiz session
- `POST /api/v1/quiz/check` - Check quiz answer
- `GET /api/v1/quiz/sessions/{id}` - Get quiz session details

### Spaced Repetition

- `GET /api/v1/review/schedule` - Get review schedule
- `GET /api/v1/review/due` - Get due cards
- `GET /api/v1/review/stats/{user_id}` - Get review statistics

### Health & Monitoring

- `GET /health` - Basic health check
- `GET /health/ready` - Readiness check
- `GET /health/live` - Liveness check

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/active_recall

# Data Storage
DATA_DIR=./data
MAX_UPLOAD_MB=10

# AI Models
EMBED_MODEL=text-embedding-004
GEN_MODEL=gemini-2.5-flash

# Server
HOST=0.0.0.0
PORT=8000

# CORS
CORS_ORIGINS=http://localhost:3000
```

### API Key Security

- All LLM operations require `X-User-Gemini-Key` header
- No built-in API keys - users provide their own
- Keys are passed through to Gemini API per request
- No server-side storage of user API keys

## Data Flow

### Content Ingestion
1. Upload PDF/URL/Text → Extract content
2. Chunk text with heading awareness
3. Generate embeddings using Gemini
4. Store in FAISS vector index
5. Save metadata to PostgreSQL

### Flashcard Generation
1. Query collection with RAG
2. Retrieve relevant chunks
3. Generate flashcards using LLM
4. Store flashcards with provenance

### Quiz & Review
1. Select cards based on SM-2 schedule
2. Present questions to user
3. Grade answers with LLM + rubric
4. Update SM-2 parameters
5. Schedule next review

## SM-2 Algorithm

The SuperMemo 2 algorithm optimizes learning intervals:

- **Quality Scale**: 0-5 (blackout to perfect)
- **Easiness Factor**: Adjusts based on performance
- **Intervals**: 1, 6, then exponential growth
- **Reset**: Poor performance (< 3) resets to beginning

## Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=app tests/

# Run specific test
pytest tests/test_basic.py::TestSM2Algorithm::test_review_calculation
```

## Development

### Code Structure

- **Models**: SQLAlchemy ORM models
- **Services**: Business logic and AI integration
- **API**: FastAPI endpoints with validation
- **Core**: Shared utilities and configuration

### Adding New Features

1. **Models**: Add to `app/core/models.py`
2. **Services**: Create in `app/core/`
3. **API**: Add endpoints in `app/api/v1/`
4. **Tests**: Add to `tests/`

### Database Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "Description"

# Apply migration
alembic upgrade head
```

## Production Deployment

### Docker Production

```bash
# Build production image
docker build -t active-recall-backend .

# Run with production settings
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e CORS_ORIGINS=https://yourdomain.com \
  active-recall-backend
```

### Environment Considerations

- **Database**: Use managed PostgreSQL service
- **Storage**: Use persistent volumes for FAISS indexes
- **Monitoring**: Add health checks and logging
- **Security**: Use HTTPS and secure headers
- **Scaling**: Consider horizontal scaling for high load

## Troubleshooting

### Common Issues

1. **OCR not working**: Install PaddlePaddle dependencies
2. **FAISS errors**: Check disk space and permissions
3. **API key issues**: Verify Gemini API key format
4. **Database connection**: Check PostgreSQL status and credentials

### Logs

```bash
# View logs
docker-compose logs -f backend

# Check specific service
docker-compose logs backend | grep ERROR
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit pull request

## License

MIT License - see LICENSE file for details.
