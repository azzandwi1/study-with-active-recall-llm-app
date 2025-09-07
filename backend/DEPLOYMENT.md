# Active Recall Backend - Deployment Guide

This guide covers deploying the Active Recall Backend API in various environments.

## Quick Start

### Development Environment

1. **Clone and setup**:
   ```bash
   cd backend
   cp env.example .env
   # Edit .env with your configuration
   ```

2. **Start with Docker Compose**:
   ```bash
   ./start.sh
   ```

3. **Access the API**:
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs

### Production Environment

1. **Setup production configuration**:
   ```bash
   cp env.prod.example .env.prod
   # Edit .env.prod with production settings
   ```

2. **Deploy with production Docker Compose**:
   ```bash
   ./deploy.sh
   ```

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Nginx         │    │   Backend       │
│   (Next.js)     │◄──►│   (Reverse      │◄──►│   (FastAPI)     │
│   Port 3000     │    │    Proxy)       │    │   Port 8000     │
└─────────────────┘    │   Port 80/443   │    └─────────────────┘
                       └─────────────────┘             │
                                                       ▼
                                              ┌─────────────────┐
                                              │   PostgreSQL    │
                                              │   Port 5432     │
                                              └─────────────────┘
```

## Components

### Backend API (FastAPI)
- **Content Ingestion**: PDF, URL, text processing
- **AI Integration**: Gemini API for embeddings and generation
- **Vector Search**: FAISS for semantic search
- **Spaced Repetition**: SM-2 algorithm implementation
- **Database**: PostgreSQL with SQLAlchemy ORM

### Database (PostgreSQL)
- **Collections**: Document collections
- **Documents**: Source documents (PDF, URL, text)
- **Chunks**: Text chunks with embeddings
- **Flashcards**: Generated learning cards
- **Reviews**: SM-2 spaced repetition data
- **Quiz Sessions**: Quiz attempts and results

### Vector Storage (FAISS)
- **Indexes**: Per-collection FAISS indexes
- **Embeddings**: Gemini text-embedding-004 vectors
- **Search**: Semantic similarity search

## API Endpoints

### Content Management
- `POST /api/v1/ingest` - Ingest content
- `GET /api/v1/ingest/collections` - List collections
- `GET /api/v1/ingest/collections/{id}` - Get collection

### Flashcard Generation
- `POST /api/v1/generate/flashcards` - Generate flashcards
- `GET /api/v1/generate/flashcards/{collection_id}` - Get flashcards
- `DELETE /api/v1/generate/flashcards/{flashcard_id}` - Delete flashcard

### Quiz System
- `POST /api/v1/quiz/start` - Start quiz
- `POST /api/v1/quiz/check` - Check answer
- `GET /api/v1/quiz/sessions/{id}` - Get session

### Spaced Repetition
- `GET /api/v1/review/schedule` - Get schedule
- `GET /api/v1/review/due` - Get due cards
- `GET /api/v1/review/stats/{user_id}` - Get stats

## Configuration

### Environment Variables

#### Database
```bash
DATABASE_URL=postgresql+psycopg2://user:pass@host:port/db
```

#### AI Models
```bash
EMBED_MODEL=text-embedding-004
GEN_MODEL=gemini-2.5-flash
```

#### Server
```bash
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

#### Security
```bash
MAX_UPLOAD_MB=10
DEBUG=false
```

### API Key Security
- All LLM operations require `X-User-Gemini-Key` header
- No server-side API key storage
- User-provided keys passed through to Gemini API

## Database Migrations

### Initialize Database
```bash
# Using Alembic
alembic upgrade head

# Or using Docker
docker-compose exec backend alembic upgrade head
```

### Create New Migration
```bash
alembic revision --autogenerate -m "Description of changes"
```

## Monitoring & Logging

### Health Checks
- `GET /health` - Basic health check
- `GET /health/ready` - Readiness check (includes DB)
- `GET /health/live` - Liveness check

### Logging
- **Console**: Structured JSON logs
- **Files**: Rotating log files in `data/logs/`
- **Levels**: DEBUG, INFO, WARNING, ERROR

### Metrics
- Request/response times
- Error rates
- Database connection status
- FAISS index health

## Security Considerations

### API Security
- Rate limiting via Nginx
- CORS configuration
- Input validation
- File upload restrictions

### Data Security
- No API key storage
- Encrypted database connections
- Secure file handling
- Input sanitization

### Network Security
- HTTPS termination at Nginx
- Internal service communication
- Firewall configuration

## Scaling Considerations

### Horizontal Scaling
- Stateless backend design
- Shared database
- Shared FAISS storage
- Load balancer configuration

### Performance Optimization
- Database connection pooling
- FAISS index optimization
- Caching strategies
- CDN for static assets

## Backup & Recovery

### Database Backups
```bash
# Create backup
pg_dump active_recall > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
psql active_recall < backup_file.sql
```

### FAISS Index Backups
```bash
# Backup FAISS indexes
tar -czf faiss_backup_$(date +%Y%m%d_%H%M%S).tar.gz data/faiss/
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check PostgreSQL status
   - Verify connection string
   - Check network connectivity

2. **API Key Errors**
   - Verify Gemini API key format
   - Check API key permissions
   - Monitor API usage limits

3. **File Upload Issues**
   - Check file size limits
   - Verify file format
   - Check disk space

4. **FAISS Index Errors**
   - Check disk space
   - Verify file permissions
   - Rebuild indexes if corrupted

### Debug Commands
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f backend

# Check database
docker-compose exec db psql -U postgres -d active_recall

# Test API
curl http://localhost:8000/health
```

## Production Checklist

- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] SSL certificates installed
- [ ] Monitoring configured
- [ ] Backup strategy implemented
- [ ] Security headers configured
- [ ] Rate limiting enabled
- [ ] Log aggregation setup
- [ ] Health checks configured
- [ ] Load balancer configured

## Support

For issues and questions:
1. Check logs: `docker-compose logs backend`
2. Review health status: `curl http://localhost:8000/health`
3. Check database connectivity
4. Verify API key configuration
5. Review environment variables
