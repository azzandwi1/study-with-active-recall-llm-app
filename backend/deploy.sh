#!/bin/bash

# Active Recall Backend Production Deployment Script

set -e  # Exit on any error

echo "🚀 Starting Active Recall Backend Production Deployment..."

# Check if .env.prod file exists
if [ ! -f .env.prod ]; then
    echo "⚠️  .env.prod file not found. Copying from env.prod.example..."
    cp env.prod.example .env.prod
    echo "📝 Please edit .env.prod file with your production configuration before running again."
    exit 1
fi

# Load environment variables
export $(cat .env.prod | grep -v '^#' | xargs)

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install docker-compose."
    exit 1
fi

echo "🔧 Building production images..."

# Build production images
docker-compose -f docker-compose.prod.yml build --no-cache

echo "🗄️  Setting up database..."

# Run database migrations
docker-compose -f docker-compose.prod.yml run --rm backend alembic upgrade head

echo "🐳 Starting production services..."

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check if backend is healthy
echo "🔍 Checking backend health..."
if curl -f http://localhost:${BACKEND_PORT:-8000}/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy!"
    echo "📚 API Documentation: http://localhost:${BACKEND_PORT:-8000}/docs"
    echo "🔧 Health Check: http://localhost:${BACKEND_PORT:-8000}/health"
    echo "🌐 Nginx Proxy: http://localhost:${NGINX_PORT:-80}"
else
    echo "❌ Backend health check failed. Check logs with: docker-compose -f docker-compose.prod.yml logs backend"
    exit 1
fi

echo "🎉 Active Recall Backend is deployed and ready!"
echo ""
echo "📋 Production URLs:"
echo "  - API: http://localhost:${NGINX_PORT:-80}/api/"
echo "  - Docs: http://localhost:${NGINX_PORT:-80}/docs"
echo "  - Health: http://localhost:${NGINX_PORT:-80}/health"
echo ""
echo "🛑 To stop services: docker-compose -f docker-compose.prod.yml down"
echo "📊 To view logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "🔄 To restart: docker-compose -f docker-compose.prod.yml restart"
