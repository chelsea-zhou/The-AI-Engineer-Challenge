import { NextRequest, NextResponse } from 'next/server'
import { DEFAULT_BACKEND_URL } from '../constants'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    // Forward the request to your backend API
    const backendUrl = process.env.BACKEND_URL || DEFAULT_BACKEND_URL
    const response = await fetch(`${backendUrl}/api/chat-pdf`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`)
    }

    // Return the streaming response
    return new Response(response.body, {
      headers: {
        'Content-Type': 'text/plain',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    })
  } catch (error) {
    console.error('Error in chat-pdf API route:', error)
    return NextResponse.json(
      { error: 'Failed to process request' },
      { status: 500 }
    )
  }
} 