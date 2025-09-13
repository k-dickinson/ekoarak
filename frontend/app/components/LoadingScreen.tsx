'use client';

import { Music, Loader2 } from 'lucide-react';
import { useState, useEffect } from 'react';

interface LoadingScreenProps {
  fileName?: string;
}

export default function LoadingScreen({ fileName }: LoadingScreenProps) {
  const [currentStep, setCurrentStep] = useState(0);
  
  const steps = [
    'Separating vocals from instrumental',
    'Extracting melody notes',
    'Generating sheet music',
    'Preparing karaoke experience',
  ];

  // Simulate step progression
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStep(prev => Math.min(prev + 1, steps.length - 1));
    }, 2000);

    return () => clearInterval(interval);
  }, [steps.length]);
  return (
    <div className="min-h-screen bg-[#F5F3EE] flex items-center justify-center p-4">
      <div className="w-full max-w-md space-y-8 text-center">
        {/* Header */}
        <div className="space-y-4">
          <div className="flex justify-center">
            <div className="w-16 h-16 bg-[#EA384D] rounded-full flex items-center justify-center">
              <Music className="w-8 h-8 text-white" />
            </div>
          </div>
          <h1 className="text-[28px] font-serif text-[#0F0E0E] font-medium">
            Processing Your Song
          </h1>
        </div>

        {/* Loading Animation */}
        <div className="space-y-6">
          <div className="flex justify-center">
            <Loader2 className="w-12 h-12 text-[#EA384D] animate-spin" />
          </div>
          
          <div className="space-y-3">
            <p className="text-[#0F0E0E] font-medium">
              {fileName ? `Processing "${fileName}"` : 'Processing your audio file'}
            </p>
            <p className="text-[#A8A29E] text-sm">
              This may take a few minutes...
            </p>
          </div>

          {/* Progress Steps */}
          <div className="space-y-3 text-left max-w-sm mx-auto">
            {steps.map((step, index) => (
              <div key={index} className="flex items-center space-x-3">
                <div className={`w-2 h-2 rounded-full ${
                  index < currentStep 
                    ? 'bg-[#EA384D]' 
                    : index === currentStep 
                    ? 'bg-[#EA384D] animate-pulse' 
                    : 'bg-[#E7E5E4]'
                }`}></div>
                <span className={`text-sm ${
                  index <= currentStep ? 'text-[#0F0E0E]' : 'text-[#A8A29E]'
                }`}>
                  {step}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Fun Fact */}
        <div className="bg-white rounded-lg p-4 border border-[#E7E5E4]">
          <p className="text-[#A8A29E] text-sm">
            💡 <strong>Did you know?</strong> Our AI analyzes the frequency spectrum to identify and separate vocal frequencies from instrumental backing tracks.
          </p>
        </div>
      </div>
    </div>
  );
}