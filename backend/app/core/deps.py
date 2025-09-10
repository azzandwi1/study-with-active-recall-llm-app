from fastapi import Request, HTTPException


def get_api_key(request: Request) -> str:
    """Extract and validate API key from request headers."""
    api_key = request.headers.get("X-User-Gemini-Key")
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="X-User-Gemini-Key header is required for all LLM operations",
        )
    return api_key


