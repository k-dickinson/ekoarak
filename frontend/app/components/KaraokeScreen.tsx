'use client';

import { useState, useRef, useEffect } from 'react';
import { Play, Pause, ArrowLeft } from 'lucide-react';
import OpenSheetMusicDisplay from '@/app/components/OpenSheetMusicDisplay';

interface TrackData {
  slug: string;
  title: string;
  artist: string;
  key?: string;
  durationSec: number;
  scoreUrl: string;
  audioUrl: string;
}

interface MusicXMLData {
  xmlDoc: Document;
  bpm: number;
  divisions: number;
  totalDuration: number;
}

interface KaraokeScreenProps {
  trackData: TrackData;
  onBack: () => void;
}

export default function KaraokeScreen({ trackData, onBack }: KaraokeScreenProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [playheadPosition, setPlayheadPosition] = useState(0);
  const [musicXMLData, setMusicXMLData] = useState<MusicXMLData | null>(null);
  const [timeOffset, setTimeOffset] = useState(0); // Offset in seconds for sync
  const lastIdxRef = useRef(0);
  
  const osmdRef = useRef<any>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const progressRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const animationFrameRef = useRef<number>(0);

  // Parse MusicXML for basic info
  const parseMusicXML = async (xmlText: string): Promise<MusicXMLData> => {
    const parser = new DOMParser();
    const xmlDoc = parser.parseFromString(xmlText, 'text/xml');
    
    // Get tempo
    const tempoElement = xmlDoc.querySelector('metronome per-minute');
    const bpm = tempoElement ? parseInt(tempoElement.textContent || '96') : 96;
    
    // Get divisions
    const divisionsElement = xmlDoc.querySelector('divisions');
    const divisions = divisionsElement ? parseInt(divisionsElement.textContent || '1') : 1;
    
    // Calculate total duration by going through all measures
    let totalDuration = 0;
    const measureElements = xmlDoc.querySelectorAll('measure');
    measureElements.forEach((measureEl) => {
      const noteElements = measureEl.querySelectorAll('note');
      noteElements.forEach((noteEl) => {
        const durationEl = noteEl.querySelector('duration');
        if (durationEl) {
          const duration = parseInt(durationEl.textContent || '1');
          const quarterNotes = duration / divisions;
          const noteDuration = quarterNotes * (60 / bpm);
          totalDuration += noteDuration;
        }
      });
    });
    
    return {
      xmlDoc,
      bpm,
      divisions,
      totalDuration
    };
  };

  // Find target cursor index by traversing MusicXML in real-time
  const findTargetIndex = (time: number): number => {
    if (!musicXMLData) return 0;
    
    const { xmlDoc, bpm, divisions } = musicXMLData;
    let currentTime = 0;
    let noteIndex = 0;
    let lastNoteIndex = 0;
    
    // Traverse through all measures and notes
    const measureElements = xmlDoc.querySelectorAll('measure');
    for (const measureEl of measureElements) {
      const noteElements = measureEl.querySelectorAll('note');
      for (const noteEl of noteElements) {
        const durationEl = noteEl.querySelector('duration');
        const pitchEl = noteEl.querySelector('pitch');
        const restEl = noteEl.querySelector('rest');
        
        if (durationEl) {
          const duration = parseInt(durationEl.textContent || '1');
          const quarterNotes = duration / divisions;
          const noteDuration = quarterNotes * (60 / bpm);
          
          // If this is a note (not a rest)
          if (pitchEl && !restEl) {
            // If time is within this note's duration, return this index
            if (time >= currentTime && time < currentTime + noteDuration) {
              return noteIndex;
            }
            lastNoteIndex = noteIndex;
            noteIndex++;
          }
          
          currentTime += noteDuration;
          
          // If we've passed the current time, return the last note index
          if (currentTime > time) {
            return Math.max(0, lastNoteIndex);
          }
        }
      }
    }
    
    // If time is beyond all notes, keep returning the last note index
    // This ensures the cursor doesn't disappear
    console.log(`Time ${time.toFixed(2)}s is beyond score, staying at note ${lastNoteIndex}`);
    return Math.max(0, lastNoteIndex);
  };

  // Move OSMD cursor to target index with auto-scroll
  const moveCursorToIndex = (targetIndex: number) => {
    if (!osmdRef.current || !musicXMLData) return;
    
    const delta = targetIndex - lastIdxRef.current;
    
    if (delta === 0) return;
    
    try {
      if (targetIndex >= lastIdxRef.current && delta <= 5) {
        // Small forward movement: step forward
        for (let i = 0; i < delta; i++) {
          osmdRef.current.cursor.next();
        }
      } else {
        // Large jump or backward: reset and step forward
        osmdRef.current.cursor.reset();
        for (let i = 0; i < targetIndex; i++) {
          osmdRef.current.cursor.next();
        }
      }
      
      lastIdxRef.current = targetIndex;
    } catch (error) {
      console.error('Error moving cursor:', error);
      console.log(`Failed to move cursor to index ${targetIndex}, current: ${lastIdxRef.current}`);
    }
  };

  // Handle OSMD ready
  const handleOsmdReady = (osmd: any) => {
    osmdRef.current = osmd;
    osmd.cursor.reset();
    osmd.cursor.show();
    lastIdxRef.current = 0;
    
    // Enable follow cursor - this will auto-advance the sheet music
    osmd.FollowCursor = true;
    
    // Try to force cursor visibility
    setTimeout(() => {
      console.log('OSMD cursor ready, testing movement...');
      console.log('OSMD instance:', osmd);
      console.log('Cursor object:', osmd.cursor);
      
      // Try multiple approaches to show cursor
      osmd.cursor.show();
      osmd.cursor.reset();
      osmd.cursor.show();
      
      // Find and resize the single OSMD cursor
      const cursorElements = document.querySelectorAll('[id*="cursor"], .osmd-cursor, [class*="cursor"]');
      console.log('Found cursor elements:', cursorElements);
      
      // Remove any duplicate cursors (keep only the first one)
      if (cursorElements.length > 1) {
        console.log('Found multiple cursors, removing duplicates...');
        for (let i = 1; i < cursorElements.length; i++) {
          cursorElements[i].remove();
        }
      }
      
      // Only resize the first cursor element found
      if (cursorElements.length > 0) {
        const cursor = cursorElements[0] as HTMLElement;
        cursor.style.display = 'block';
        cursor.style.visibility = 'visible';
        cursor.style.opacity = '1';
        cursor.style.zIndex = '1000';
        cursor.style.width = '4px';
        cursor.style.height = '400px';
        cursor.style.background = '#EA384D';
        cursor.style.border = 'none';
        cursor.style.margin = '0';
        cursor.style.padding = '0';
        console.log('Resized cursor element:', cursor);
      }
      
      osmd.cursor.next(); // should visibly move one step
      osmd.cursor.previous();
      console.log('Cursor test complete - check if cursor is visible');
    }, 1000);
  };

  // Load MusicXML
  useEffect(() => {
    const loadMusicXML = async () => {
      try {
        const scoreResponse = await fetch(trackData.scoreUrl);
        const xmlText = await scoreResponse.text();
        const musicXMLData = await parseMusicXML(xmlText);
        setMusicXMLData(musicXMLData);
      } catch (error) {
        console.error('Error loading MusicXML:', error);
      }
    };
    
    loadMusicXML();
  }, [trackData]);

  // Animation loop for cursor movement
  useEffect(() => {
    if (!isPlaying || !audioRef.current || !musicXMLData) return;
    
    const updateCursor = () => {
      if (!audioRef.current) return;
      
      const t = audioRef.current.currentTime + timeOffset;
      setCurrentTime(t);
      
      // Update progress bar
      const percentage = (t / duration) * 100;
      setPlayheadPosition(Math.min(percentage, 100));
      
      // Find target cursor index using real-time MusicXML traversal
      const targetIndex = findTargetIndex(t);
      
      // Move cursor if needed
      if (targetIndex !== lastIdxRef.current && targetIndex >= 0) {
        console.log(`Moving cursor from ${lastIdxRef.current} to ${targetIndex} at time ${t.toFixed(2)}s`);
        moveCursorToIndex(targetIndex);
      } else if (targetIndex === lastIdxRef.current) {
        // Debug: cursor is staying at the same position
        console.log(`Cursor staying at position ${targetIndex} at time ${t.toFixed(2)}s`);
      }
      
      if (isPlaying) {
        animationFrameRef.current = requestAnimationFrame(updateCursor);
      }
    };
    
    animationFrameRef.current = requestAnimationFrame(updateCursor);
    
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [isPlaying, musicXMLData, duration]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handlePlayPause = () => {
    if (!audioRef.current) return;
    
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleProgressClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!progressRef.current || !audioRef.current || !musicXMLData) return;
    
    const rect = progressRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const percentage = clickX / rect.width;
    const newTime = percentage * duration;
    
    audioRef.current.currentTime = newTime;
    setCurrentTime(newTime);
    setPlayheadPosition(percentage * 100);
    
    // Jump cursor to new position using real-time MusicXML traversal
    const targetIndex = findTargetIndex(newTime);
    
    // Reset cursor and fast-forward to target
    if (osmdRef.current) {
      osmdRef.current.cursor.reset();
      for (let i = 0; i < targetIndex; i++) {
        osmdRef.current.cursor.next();
      }
      lastIdxRef.current = targetIndex;
    }
  };

  return (
    <div className="min-h-screen bg-[#F5F3EE] flex items-center justify-center p-4">
      <div className="w-full max-w-[1100px] space-y-6">
        {/* Hidden Audio Element */}
        <audio
          id="bk"
          ref={audioRef}
          src={trackData.audioUrl}
          preload="metadata"
          onLoadedMetadata={() => {
            if (audioRef.current) {
              setDuration(audioRef.current.duration);
            }
          }}
        />
        
        {/* Back Button */}
        <div className="flex justify-start">
          <button
            onClick={onBack}
            className="flex items-center space-x-2 text-[#A8A29E] hover:text-[#0F0E0E] transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm">Upload Another Song</span>
          </button>
        </div>

        {/* Song Info Header */}
        <div className="text-center space-y-4">
          <h1 className="text-[28px] font-serif text-[#0F0E0E] font-medium">
            {trackData.title}
          </h1>
          <div className="text-sm text-[#A8A29E]">
            {trackData.artist}
          </div>
          {trackData.key && (
            <div className="flex justify-center">
              <div className="px-3 py-1 border border-[#E7E5E4] rounded-full text-sm text-[#0F0E0E]">
                Key: {trackData.key}
              </div>
            </div>
          )}
        </div>

        {/* Score Viewport */}
        <div className="relative max-w-[960px] mx-auto">
          <div 
            ref={scrollContainerRef}
            className="relative overflow-x-auto overflow-y-hidden h-[400px] scrollbar-hide"
          >
            <OpenSheetMusicDisplay 
              file={trackData.scoreUrl} 
              drawTitle={false} 
              autoResize 
              onReady={handleOsmdReady} 
            />
          </div>
        </div>

        {/* Progress Bar */}
        <div className="max-w-[960px] mx-auto">
          <div
            ref={progressRef}
            className="relative h-2 bg-[#E7E5E4] rounded-full cursor-pointer"
            onClick={handleProgressClick}
          >
            <div
              className="absolute top-0 left-0 h-full bg-[#EA384D] rounded-full"
              style={{ width: `${playheadPosition}%` }}
            />
            <div
              className="absolute top-1/2 w-3.5 h-3.5 bg-[#EA384D] rounded-full transform -translate-y-1/2 -translate-x-1/2 cursor-pointer"
              style={{ left: `${playheadPosition}%` }}
            />
          </div>
          <div className="flex justify-between text-sm text-[#A8A29E] mt-2">
            <span>{formatTime(currentTime)}</span>
            <span>{formatTime(duration)}</span>
          </div>
        </div>

        {/* Transport Controls */}
        <div className="flex items-center justify-center space-x-6">
          {/* Play/Pause Button */}
          <button
            onClick={handlePlayPause}
            className="w-12 h-12 bg-[#EA384D] rounded-full flex items-center justify-center text-white hover:bg-opacity-90 transition-colors"
          >
            {isPlaying ? (
              <Pause className="w-5 h-5" />
            ) : (
              <Play className="w-5 h-5 ml-0.5" />
            )}
          </button>
          
          {/* Sync Controls */}
          <div className="flex items-center space-x-4">
            <label className="text-sm text-[#A8A29E]">Sync Offset:</label>
            <input
              type="range"
              min="-2"
              max="2"
              step="0.1"
              value={timeOffset}
              onChange={(e) => setTimeOffset(parseFloat(e.target.value))}
              className="w-24"
            />
            <span className="text-sm text-[#A8A29E] w-12">
              {timeOffset > 0 ? '+' : ''}{timeOffset.toFixed(1)}s
            </span>
          </div>
        </div>
      </div>

      <style jsx>{`
        .osmd-page-background, .osmd-canvas-background {
          display: none !important;
        }
        .osmd-cursor {
          display: block !important;
          visibility: visible !important;
          opacity: 1 !important;
          z-index: 1000 !important;
          width: 4px !important;
          height: var(--cursor-height, 60px) !important;
          background: #EA384D !important;
          position: absolute !important;
        }
        .osmd-cursor-line {
          stroke: #EA384D !important;
          stroke-width: 4px !important;
          opacity: 1 !important;
        }
        .osmd-cursor * {
          width: 4px !important;
          height: var(--cursor-height, 60px) !important;
          background: #EA384D !important;
          border: none !important;
          margin: 0 !important;
          padding: 0 !important;
        }
        .osmd-cursor div {
          width: 4px !important;
          height: var(--cursor-height, 60px) !important;
          background: #EA384D !important;
          position: absolute !important;
          border: none !important;
        }
        [id*="cursor"] {
          display: block !important;
          visibility: visible !important;
          opacity: 1 !important;
          width: 4px !important;
          height: var(--cursor-height, 60px) !important;
          background: #EA384D !important;
        }
        .osmd-cursor img {
          width: 4px !important;
          height: var(--cursor-height, 60px) !important;
          background: #EA384D !important;
          border: none !important;
          display: block !important;
          position: absolute !important;
          object-fit: none !important;
        }
        .osmd-cursor svg {
          width: 4px !important;
          height: var(--cursor-height, 60px) !important;
        }
        .osmd-cursor svg line {
          stroke: #EA384D !important;
          stroke-width: 4px !important;
        }
        .osmd-cursor svg rect {
          fill: #EA384D !important;
          width: 4px !important;
          height: var(--cursor-height, 60px) !important;
        }
        .osmd-cursor svg path {
          fill: #EA384D !important;
          stroke: #EA384D !important;
          stroke-width: 4px !important;
        }
        .scrollbar-hide {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
      `}</style>
    </div>
  );
}