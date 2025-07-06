import { NextRequest, NextResponse } from 'next/server'
import { DEFAULT_BACKEND_URL } from '../../constants'

export async function DELETE(
  request: NextRequest,
  { params }: { params: { pdfId: string } }
) {
  try {
    const { pdfId } = params
    
    // Forward the request to your backend API
    const backendUrl = process.env.BACKEND_URL || DEFAULT_BACKEND_URL
    const response = await fetch(`${backendUrl}/api/pdfs/${pdfId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      const error = await response.json()
      return NextResponse.json(
        { error: error.detail || 'Delete failed' },
        { status: response.status }
      )
    }

    // Return the response from backend
    const result = await response.json()
    return NextResponse.json(result)
  } catch (error) {
    console.error('Error in delete PDF API route:', error)
    return NextResponse.json(
      { error: 'Failed to delete PDF' },
      { status: 500 }
    )
  }
} 