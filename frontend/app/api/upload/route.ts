import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get('audio') as File;
    
    if (!file) {
      return NextResponse.json(
        { error: 'No audio file provided' },
        { status: 400 }
      );
    }

    // Validate file type
    const allowedTypes = [
      'audio/mpeg',
      'audio/wav',
      'audio/mp4',
      'audio/aac',
      'audio/flac',
      'audio/ogg',
      'audio/m4a'
    ];
    
    if (!allowedTypes.includes(file.type) && 
        !file.name.toLowerCase().match(/\.(mp3|wav|m4a|aac|flac|ogg)$/)) {
      return NextResponse.json(
        { error: 'Unsupported file type. Please upload an audio file.' },
        { status: 400 }
      );
    }

    // Validate file size (max 50MB)
    const maxSize = 50 * 1024 * 1024; // 50MB
    if (file.size > maxSize) {
      return NextResponse.json(
        { error: 'File too large. Maximum size is 50MB.' },
        { status: 400 }
      );
    }

    // TODO: Send file to backend for processing
    // For now, return a mock response
    const mockResponse = {
      success: true,
      message: 'File uploaded successfully',
      trackId: `uploaded-${Date.now()}`,
      // These would come from the backend processing
      estimatedProcessingTime: 120, // seconds
    };

    return NextResponse.json(mockResponse);
    
  } catch (error) {
    console.error('Upload error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}