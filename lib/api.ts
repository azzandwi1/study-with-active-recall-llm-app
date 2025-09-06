export const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"

export function getApiHeaders(): HeadersInit {
  const apiKey = typeof window !== "undefined" ? localStorage.getItem("gemini_api_key") : null

  return {
    "Content-Type": "application/json",
    ...(apiKey && { "X-User-Gemini-Key": apiKey }),
  }
}

export async function apiRequest(endpoint: string, options: RequestInit = {}) {
  const url = `${API_BASE_URL}${endpoint}`

  const response = await fetch(url, {
    ...options,
    headers: {
      ...getApiHeaders(),
      ...options.headers,
    },
  })

  if (!response.ok) {
    throw new Error(`API request failed: ${response.statusText}`)
  }

  return response.json()
}
