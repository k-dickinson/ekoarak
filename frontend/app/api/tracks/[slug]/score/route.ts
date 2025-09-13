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
    const scorePath = path.join(DATA_DIR, slug, 'melody.musicxml');
    
    if (!fs.existsSync(scorePath)) {
      return NextResponse.json({ error: 'Score not found' }, { status: 404 });
    }

    const scoreContent = fs.readFileSync(scorePath, 'utf-8');
    
    return new NextResponse(scoreContent, {
      headers: {
        'Content-Type': 'application/vnd.recordare.musicxml+xml',
        'Cache-Control': 'public, max-age=3600'
      }
    });
  } catch (error) {
    console.error(`Error reading score for ${params.slug}:`, error);
    return NextResponse.json({ error: 'Failed to read score' }, { status: 500 });
  }
}