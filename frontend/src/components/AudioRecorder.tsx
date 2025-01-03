// src/components/AudioRecorder.tsx
import React, { useState } from 'react';
import useAudioRecorder from '../hooks/useAudioRecorder';
import { Mic, Square, Pause, Play, RefreshCcw } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface AudioRecorderProps {
  onRecordingComplete?: (blob: Blob) => void;
}

const AudioRecorder: React.FC<AudioRecorderProps> = ({ onRecordingComplete }) => {
  const {
    isRecording,
    isPaused,
    duration,
    audioBlob,
    error,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    resetRecording,
  } = useAudioRecorder();

  const [isProcessing, setIsProcessing] = useState(false);

  // Format duration to mm:ss
  const formatDuration = (ms: number): string => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  // Handle recording completion
  const handleRecordingComplete = async () => {
    if (audioBlob && onRecordingComplete) {
      setIsProcessing(true);
      try {
        await onRecordingComplete(audioBlob);
      } catch (error) {
        console.error('Error processing recording:', error);
      } finally {
        setIsProcessing(false);
      }
    }
  };

  return (
    <div className="w-full max-w-md mx-auto p-4 bg-white rounded-lg shadow">
      {/* Recording Controls */}
      <div className="flex items-center justify-center space-x-4 mb-4">
        {!isRecording ? (
          <button
            onClick={startRecording}
            disabled={isProcessing}
            className="p-3 bg-red-500 text-white rounded-full hover:bg-red-600 disabled:opacity-50"
            aria-label="Start Recording"
          >
            <Mic className="w-6 h-6" />
          </button>
        ) : (
          <>
            <button
              onClick={stopRecording}
              className="p-3 bg-gray-500 text-white rounded-full hover:bg-gray-600"
              aria-label="Stop Recording"
            >
              <Square className="w-6 h-6" />
            </button>
            <button
              onClick={isPaused ? resumeRecording : pauseRecording}
              className="p-3 bg-blue-500 text-white rounded-full hover:bg-blue-600"
              aria-label={isPaused ? "Resume Recording" : "Pause Recording"}
            >
              {isPaused ? <Play className="w-6 h-6" /> : <Pause className="w-6 h-6" />}
            </button>
          </>
        )}
        {audioBlob && (
          <button
            onClick={resetRecording}
            className="p-3 bg-gray-300 text-gray-700 rounded-full hover:bg-gray-400"
            aria-label="Reset Recording"
          >
            <RefreshCcw className="w-6 h-6" />
          </button>
        )}
      </div>

      {/* Recording Status */}
      <div className="text-center space-y-2">
        <p className="text-lg font-semibold text-gray-700">
          {isRecording ? (
            isPaused ? "録音一時停止中" : "録音中..."
          ) : (
            audioBlob ? "録音完了" : "録音待機中"
          )}
        </p>
        {(isRecording || audioBlob) && (
          <p className="text-sm text-gray-500">
            録音時間: {formatDuration(duration)}
          </p>
        )}
      </div>

      {/* Audio Preview */}
      {audioBlob && (
        <div className="mt-4">
          <audio
            controls
            src={URL.createObjectURL(audioBlob)}
            className="w-full"
          />
          <button
            onClick={handleRecordingComplete}
            disabled={isProcessing}
            className="mt-2 w-full py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
          >
            {isProcessing ? "処理中..." : "録音を保存"}
          </button>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <Alert variant="destructive" className="mt-4">
          <AlertDescription>
            エラーが発生しました: {error.message}
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
};

export default AudioRecorder;
