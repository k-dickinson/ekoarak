'use client';

import { useState, useEffect } from 'react';
import UploadScreen from '@/app/components/UploadScreen';
import LoadingScreen from '@/app/components/LoadingScreen';
import KaraokeScreen from '@/app/components/KaraokeScreen';

interface TrackData {
  slug: string;
  title: string;
  artist: string;
  key?: string;
  durationSec: number;
  scoreUrl: string;
  audioUrl: string;
}

type Screen = 'upload' | 'loading' | 'karaoke';

export default function Home() {
  const [currentScreen, setCurrentScreen] = useState<Screen>('upload');
  const [trackData, setTrackData] = useState<TrackData | null>(null);
  const [uploadedFileName, setUploadedFileName] = useState<string>('');

  // Handle file upload
  const handleFileUpload = async (file: File) => {
    setUploadedFileName(file.name);
    setCurrentScreen('loading');
    
    try {
      // Create FormData for file upload
      const formData = new FormData();
      formData.append('audio', file);
      
      // Upload file to backend
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error('Upload failed');
      }
      
      const result = await response.json();
      
      // Poll for processing status
      await pollProcessingStatus(result.trackId, file);
      
    } catch (error) {
      console.error('Error uploading file:', error);
      // Reset to upload screen on error
      setCurrentScreen('upload');
      setUploadedFileName('');
    }
  };

  // Poll processing status
  const pollProcessingStatus = async (trackId: string, file: File) => {
    const maxAttempts = 30; // 5 minutes max
    let attempts = 0;
    
    const poll = async (): Promise<void> => {
      try {
        const response = await fetch(`/api/upload/status?trackId=${trackId}`);
        const status = await response.json();
        
        if (status.status === 'completed' && status.trackData) {
          // Processing complete, use the processed track data
          setTrackData(status.trackData);
          setCurrentScreen('karaoke');
          return;
        } else if (status.status === 'failed') {
          throw new Error('Processing failed');
        } else if (attempts >= maxAttempts) {
          throw new Error('Processing timeout');
        }
        
        // Continue polling
        attempts++;
        setTimeout(poll, 10000); // Poll every 10 seconds
        
      } catch (error) {
        console.error('Error checking status:', error);
        // Fallback to default track data for demo purposes
        const defaultTrack: TrackData = {
          slug: 'uploaded-song',
          title: file.name.replace(/\.[^/.]+$/, ''), // Remove file extension
          artist: 'Unknown Artist',
          durationSec: 180, // Default duration
          scoreUrl: '/test.musicxml', // Default score
          audioUrl: URL.createObjectURL(file), // Use uploaded file
        };
        
        setTrackData(defaultTrack);
        setCurrentScreen('karaoke');
      }
    };
    
    // Start polling after a short delay
    setTimeout(poll, 2000);
  };

  // Handle loading screen
  const handleLoading = () => {
    setCurrentScreen('loading');
  };

  // Handle back to upload
  const handleBackToUpload = () => {
    setCurrentScreen('upload');
    setTrackData(null);
    setUploadedFileName('');
  };

  // Render current screen
  const renderCurrentScreen = () => {
    switch (currentScreen) {
      case 'upload':
        return (
          <UploadScreen 
            onUpload={handleFileUpload}
            onLoading={handleLoading}
          />
        );
      case 'loading':
        return (
          <LoadingScreen 
            fileName={uploadedFileName}
          />
        );
      case 'karaoke':
        return trackData ? (
          <KaraokeScreen 
            trackData={trackData}
            onBack={handleBackToUpload}
          />
        ) : null;
      default:
        return null;
    }
  };

  return renderCurrentScreen();
}