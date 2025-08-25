export const DEFAULT_BACKEND_URL = 'http://127.0.0.1:8000'

// Default API keys - will read from environment variables or use fallback values
export const DEFAULT_OPENAI_API_KEY = process.env.NEXT_PUBLIC_OPENAI_API_KEY || 'sk-your-openai-api-key-here'
export const DEFAULT_TAVILY_API_KEY = process.env.NEXT_PUBLIC_TAVILY_API_KEY || 'tvly-your-tavily-api-key-here'