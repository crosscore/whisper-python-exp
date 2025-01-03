// src/App.tsx
import React, { useState, useCallback } from 'react';
import AudioRecorder from './components/AudioRecorder';
import FileUploader from './components/FileUploader';
import TranscriptionView from './components/TranscriptionView';
import { TranscriptionResult } from './services/api';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent } from '@/components/ui/card';
import { RealtimeTranscriptionService } from './services/api';

const App: React.FC = () => {
  // State management
  const [transcriptionResult, setTranscriptionResult] = useState<TranscriptionResult | undefined>();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [realtimeService] = useState(() => new RealtimeTranscriptionService());
  const [isRealtimeActive, setIsRealtimeActive] = useState(false);

  // Handle file upload completion
  const handleUploadComplete = useCallback((result: TranscriptionResult) => {
    setTranscriptionResult(result);
    setError(null);
  }, []);

  // Handle upload error
  const handleUploadError = useCallback((error: Error) => {
    setError(error.message);
    setTranscriptionResult(undefined);
  }, []);

  // Handle recording completion
  const handleRecordingComplete = useCallback(async (blob: Blob) => {
    setIsLoading(true);
    try {
      const file = new File([blob], 'recording.wav', { type: 'audio/wav' });
      const result = await fetch('/transcribe', {
        method: 'POST',
        body: file
      });
      const transcription = await result.json();
      setTranscriptionResult(transcription);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '文字起こしに失敗しました');
      setTranscriptionResult(undefined);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Handle realtime transcription update
  const handleRealtimeTranscription = useCallback((result: TranscriptionResult) => {
    setTranscriptionResult(prev => ({
      ...prev,
      text: prev?.text ? `${prev.text}\n${result.text}` : result.text,
      segments: [...(prev?.segments || []), ...(result.segments || [])]
    }));
  }, []);

  // Start realtime transcription
  const startRealtimeTranscription = useCallback(() => {
    setIsRealtimeActive(true);
    realtimeService.connect(handleRealtimeTranscription);
  }, [realtimeService, handleRealtimeTranscription]);

  // Stop realtime transcription
  const stopRealtimeTranscription = useCallback(() => {
    setIsRealtimeActive(false);
    realtimeService.disconnect();
  }, [realtimeService]);

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-center text-gray-900 mb-8">
          音声文字起こしアプリ
        </h1>

        <Tabs defaultValue="upload" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="upload">
              ファイルアップロード
            </TabsTrigger>
            <TabsTrigger value="record">
              音声録音
            </TabsTrigger>
            <TabsTrigger value="realtime">
              リアルタイム
            </TabsTrigger>
          </TabsList>

          <TabsContent value="upload">
            <Card>
              <CardContent className="pt-6">
                <FileUploader
                  onUploadComplete={handleUploadComplete}
                  onError={handleUploadError}
                />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="record">
            <Card>
              <CardContent className="pt-6">
                <AudioRecorder
                  onRecordingComplete={handleRecordingComplete}
                />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="realtime">
            <Card>
              <CardContent className="pt-6">
                <div className="flex justify-center space-x-4 mb-6">
                  {!isRealtimeActive ? (
                    <button
                      onClick={startRealtimeTranscription}
                      className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                    >
                      リアルタイム文字起こしを開始
                    </button>
                  ) : (
                    <button
                      onClick={stopRealtimeTranscription}
                      className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
                    >
                      停止
                    </button>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Transcription result section */}
        <div className="mt-8">
          <TranscriptionView
            result={transcriptionResult}
            isLoading={isLoading}
            isRealtime={isRealtimeActive}
          />
        </div>
      </div>
    </div>
  );
};

export default App;
