from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = Field(
        default="postgresql+psycopg2://postgres:postgres@localhost:5432/active_recall",
        env="DATABASE_URL"
    )
    
    # Data directories
    data_dir: Path = Field(default=Path("./data"), env="DATA_DIR")
    uploads_dir: Path = Field(default=Path("./data/uploads"))
    faiss_dir: Path = Field(default=Path("./data/faiss"))
    
    # Upload limits
    max_upload_mb: int = Field(default=10, env="MAX_UPLOAD_MB")
    max_upload_bytes: int = Field(default=10 * 1024 * 1024)  # 10MB
    
    # AI Models
    embed_model: str = Field(default="text-embedding-004", env="EMBED_MODEL")
    gen_model: str = Field(default="gemini-2.5-flash", env="GEN_MODEL")
    
    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # CORS
    cors_origins: list[str] = Field(default=["http://localhost:3000"])
    
    # Chunking settings
    chunk_size: int = Field(default=800)
    chunk_overlap: int = Field(default=150)
    
    # OCR settings
    ocr_language: str = Field(default="en")
    ocr_confidence_threshold: float = Field(default=0.7)
    
    # Text density threshold for OCR fallback
    text_density_threshold: float = Field(default=0.1)
    
    # FAISS settings
    faiss_dimension: int = Field(default=768)  # text-embedding-004 dimension
    
    # Security
    allowed_mime_types: list[str] = Field(default=["application/pdf", "text/plain"])
    blocked_url_patterns: list[str] = Field(default=["file://", "localhost", "127.0.0.1"])
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.faiss_dir.mkdir(parents=True, exist_ok=True)
        
        # Calculate max upload bytes
        self.max_upload_bytes = self.max_upload_mb * 1024 * 1024


settings = Settings()
