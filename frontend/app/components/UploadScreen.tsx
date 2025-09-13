'use client';

import { useState, useRef } from 'react';
import { Upload, Music, FileAudio } from 'lucide-react';

interface UploadScreenProps {
  onUpload: (file: File) => void;
  onLoading: () => void;
}

export default function UploadScreen({ onUpload, onLoading }: UploadScreenProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    const audioFile = files.find(file => 
      file.type.startsWith('audio/') || 
      file.name.toLowerCase().match(/\.(mp3|wav|m4a|aac|flac|ogg)$/)
    );
    
    if (audioFile) {
      setSelectedFile(audioFile);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    
    onLoading();
    onUpload(selectedFile);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="min-h-screen bg-[#F5F3EE] flex items-center justify-center p-4">
      <div className="w-full max-w-2xl space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <div className="flex justify-center">
            <div className="w-16 h-16 bg-[#EA384D] rounded-full flex items-center justify-center">
              <Music className="w-8 h-8 text-white" />
            </div>
          </div>
          <h1 className="text-[32px] font-serif text-[#0F0E0E] font-medium">
            Reverse Karaoke
          </h1>
          <p className="text-[#A8A29E] text-lg max-w-md mx-auto">
            Upload your favorite song and we'll extract the vocal melody for you to practice with
          </p>
        </div>

        {/* Upload Area */}
        <div className="space-y-6">
          <div
            className={`relative border-2 border-dashed rounded-xl p-12 text-center transition-colors ${
              isDragOver 
                ? 'border-[#EA384D] bg-[#EA384D]/5' 
                : 'border-[#E7E5E4] hover:border-[#EA384D]/50'
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="audio/*,.mp3,.wav,.m4a,.aac,.flac,.ogg"
              onChange={handleFileSelect}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            
            <div className="space-y-4">
              <div className="flex justify-center">
                <div className="w-12 h-12 bg-[#EA384D]/10 rounded-full flex items-center justify-center">
                  <Upload className="w-6 h-6 text-[#EA384D]" />
                </div>
              </div>
              
              <div>
                <p className="text-[#0F0E0E] font-medium text-lg">
                  {selectedFile ? 'File Selected' : 'Drop your audio file here'}
                </p>
                <p className="text-[#A8A29E] text-sm mt-1">
                  {selectedFile 
                    ? `or click to choose a different file`
                    : 'or click to browse files'
                  }
                </p>
              </div>
              
              {selectedFile && (
                <div className="bg-white rounded-lg p-4 border border-[#E7E5E4] max-w-md mx-auto">
                  <div className="flex items-center space-x-3">
                    <FileAudio className="w-5 h-5 text-[#EA384D]" />
                    <div className="flex-1 text-left">
                      <p className="text-[#0F0E0E] font-medium text-sm truncate">
                        {selectedFile.name}
                      </p>
                      <p className="text-[#A8A29E] text-xs">
                        {formatFileSize(selectedFile.size)}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Upload Button */}
          {selectedFile && (
            <div className="flex justify-center">
              <button
                onClick={handleUpload}
                className="px-8 py-3 bg-[#EA384D] text-white rounded-lg font-medium hover:bg-opacity-90 transition-colors flex items-center space-x-2"
              >
                <Upload className="w-5 h-5" />
                <span>Process Song</span>
              </button>
            </div>
          )}
        </div>

        {/* Supported Formats */}
        <div className="text-center">
          <p className="text-[#A8A29E] text-sm">
            Supported formats: MP3, WAV, M4A, AAC, FLAC, OGG
          </p>
        </div>
      </div>
    </div>
  );
}