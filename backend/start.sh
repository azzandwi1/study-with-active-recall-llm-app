#!/bin/bash

# Active Recall Backend Startup Script

echo "🚀 Starting Active Recall Backend..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from env.example..."
    cp env.example .env
    echo "📝 Please edit .env file with your configuration before running again."
    exit 1
fi

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

echo "🐳 Starting services with Docker Compose..."

# Start services
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if backend is healthy
echo "🔍 Checking backend health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy!"
    echo "📚 API Documentation: http://localhost:8000/docs"
    echo "🔧 Health Check: http://localhost:8000/health"
    echo "🗄️  Database: PostgreSQL on localhost:5432"
else
    echo "❌ Backend health check failed. Check logs with: docker-compose logs backend"
    exit 1
fi

echo "🎉 Active Recall Backend is ready!"
echo ""
echo "📋 Quick Start:"
echo "1. Get your Gemini API key from: https://makersuite.google.com/app/apikey"
echo "2. Import the Postman collection: postman_collection.json"
echo "3. Set the api_key variable in Postman"
echo "4. Start testing the API endpoints!"
echo ""
echo "🛑 To stop services: docker-compose down"
