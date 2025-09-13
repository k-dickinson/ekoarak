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
    const metaPath = path.join(DATA_DIR, slug, 'meta.json');
    
    if (!fs.existsSync(metaPath)) {
      return NextResponse.json({ error: 'Track not found' }, { status: 404 });
    }

    const metaContent = fs.readFileSync(metaPath, 'utf-8');
    const meta = JSON.parse(metaContent);
    
    // Add API URLs
    const trackData = {
      ...meta,
      slug,
      scoreUrl: `/api/tracks/${slug}/score`,
      audioUrl: `/api/tracks/${slug}/instrumental`
    };

    return NextResponse.json(trackData);
  } catch (error) {
    console.error(`Error reading track ${params.slug}:`, error);
    return NextResponse.json({ error: 'Failed to read track' }, { status: 500 });
  }
}