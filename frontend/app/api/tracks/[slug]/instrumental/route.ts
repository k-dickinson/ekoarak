import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

const DATA_DIR = process.env.DATA_DIR || path.join(process.cwd(), 'data', 'tracks');

export async function GET(
  request: Request,
  { params }: { params: { slug: string } }
) {
  try {
    const { slug } = params;
    const audioPath = path.join(DATA_DIR, slug, 'instrumental.m4a');
    
    if (!fs.existsSync(audioPath)) {
      return NextResponse.json({ error: 'Audio not found' }, { status: 404 });
    }

    const stat = fs.statSync(audioPath);
    const fileSize = stat.size;
    const range = request.headers.get('range');

    if (range) {
      // Handle byte-range requests for scrubbing
      const parts = range.replace(/bytes=/, "").split("-");
      const start = parseInt(parts[0], 10);
      const end = parts[1] ? parseInt(parts[1], 10) : fileSize - 1;
      const chunksize = (end - start) + 1;
      
      const file = fs.createReadStream(audioPath, { start, end });
      const head = {
        'Content-Range': `bytes ${start}-${end}/${fileSize}`,
        'Accept-Ranges': 'bytes',
        'Content-Length': chunksize.toString(),
        'Content-Type': 'audio/mp4',
        'Cache-Control': 'public, max-age=3600'
      };
      
      return new NextResponse(file as any, { status: 206, headers: head });
    } else {
      // Return full file
      const file = fs.readFileSync(audioPath);
      
      return new NextResponse(file, {
        headers: {
          'Content-Type': 'audio/mp4',
          'Content-Length': fileSize.toString(),
          'Accept-Ranges': 'bytes',
          'Cache-Control': 'public, max-age=3600'
        }
      });
    }
  } catch (error) {
    console.error(`Error reading audio for ${params.slug}:`, error);
    return NextResponse.json({ error: 'Failed to read audio' }, { status: 500 });
  }
}