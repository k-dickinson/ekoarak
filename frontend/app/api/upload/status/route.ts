import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const trackId = searchParams.get('trackId');
    
    if (!trackId) {
      return NextResponse.json(
        { error: 'Track ID is required' },
        { status: 400 }
      );
    }

    // TODO: Check actual processing status from backend
    // For now, return a mock response
    const mockStatus = {
      trackId,
      status: 'processing', // 'processing', 'completed', 'failed'
      progress: 45, // percentage
      estimatedTimeRemaining: 60, // seconds
      steps: [
        { name: 'Separating vocals from instrumental', completed: true },
        { name: 'Extracting melody notes', completed: true },
        { name: 'Generating sheet music', completed: false },
        { name: 'Preparing karaoke experience', completed: false },
      ],
      // When completed, include track data
      trackData: null as any,
    };

    return NextResponse.json(mockStatus);
    
  } catch (error) {
    console.error('Status check error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}