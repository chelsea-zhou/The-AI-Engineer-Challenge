import { NextRequest, NextResponse } from 'next/server'
import { DEFAULT_BACKEND_URL } from '../constants'

export async function POST(request: NextRequest) {
  try {
    // Get form data from request
    const formData = await request.formData()
    
    // Forward the request to your backend API
    const backendUrl = process.env.BACKEND_URL || DEFAULT_BACKEND_URL
    const response = await fetch(`${backendUrl}/api/upload-pdf`, {
      method: 'POST',
      body: formData, // Forward the FormData directly
    })

    if (!response.ok) {
      const error = await response.json()
      return NextResponse.json(
        { error: error.detail || 'Upload failed' },
        { status: response.status }
      )
    }

    // Return the response from backend
    const result = await response.json()
    return NextResponse.json(result)
  } catch (error) {
    console.error('Error in upload-pdf API route:', error)
    return NextResponse.json(
      { error: 'Failed to process upload request' },
      { status: 500 }
    )
  }
} 