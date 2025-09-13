import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

const DATA_DIR = process.env.DATA_DIR || path.join(process.cwd(), 'data', 'tracks');

export async function GET() {
  try {
    if (!fs.existsSync(DATA_DIR)) {
      return NextResponse.json({ tracks: [] });
    }

    const trackDirs = fs.readdirSync(DATA_DIR, { withFileTypes: true })
      .filter(dirent => dirent.isDirectory())
      .map(dirent => dirent.name);

    const tracks = [];
    
    for (const slug of trackDirs) {
      const metaPath = path.join(DATA_DIR, slug, 'meta.json');
      
      if (fs.existsSync(metaPath)) {
        try {
          const metaContent = fs.readFileSync(metaPath, 'utf-8');
          const meta = JSON.parse(metaContent);
          
          // Add API URLs
          const trackData = {
            ...meta,
            slug,
            scoreUrl: `/api/tracks/${slug}/score`,
            audioUrl: `/api/tracks/${slug}/instrumental`
          };
          
          tracks.push(trackData);
        } catch (error) {
          console.error(`Error reading meta.json for ${slug}:`, error);
        }
      }
    }

    return NextResponse.json({ tracks });
  } catch (error) {
    console.error('Error listing tracks:', error);
    return NextResponse.json({ error: 'Failed to list tracks' }, { status: 500 });
  }
}