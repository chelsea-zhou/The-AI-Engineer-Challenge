import { NextRequest, NextResponse } from 'next/server'
import { DEFAULT_BACKEND_URL } from '../constants'

export async function GET(request: NextRequest) {
  try {
    // Forward the request to your backend API
    const backendUrl = process.env.BACKEND_URL || DEFAULT_BACKEND_URL
    const response = await fetch(`${backendUrl}/api/pdfs`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      cache: 'no-store',
    })

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`)
    }

    // Return the response from backend
    const result = await response.json()
    return NextResponse.json(result)
  } catch (error) {
    console.error('Error in pdfs API route:', error)
    return NextResponse.json(
      { error: 'Failed to fetch PDFs' },
      { status: 500 }
    )
  }
} 