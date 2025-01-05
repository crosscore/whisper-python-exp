import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { TranscriptionResult } from '../services/api';
import { Loader2, Languages } from 'lucide-react';

interface TranscriptionViewProps {
  result?: TranscriptionResult;
  isLoading?: boolean;
  isRealtime?: boolean;
}

const TranscriptionView: React.FC<TranscriptionViewProps> = ({
  result,
  isLoading = false,
  isRealtime = false,
}) => {
  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center p-6">
          <div className="flex flex-col items-center space-y-2">
            <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
            <p className="text-gray-600">文字起こし処理中...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!result) {
    return (
      <Card>
        <CardContent className="p-6 text-center text-gray-500">
          音声ファイルをアップロードするか、録音を開始してください。
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="p-6">
        {/* Language indicator */}
        <div className="flex items-center gap-2 mb-4 text-sm text-gray-600">
          <Languages className="w-4 h-4" />
          <span>検出された言語: {result.language || '不明'}</span>
          {isRealtime && (
            <span className="ml-auto text-blue-500 animate-pulse">
              リアルタイム文字起こし中...
            </span>
          )}
        </div>

        {/* Transcription text */}
        <ScrollArea className="h-[400px] pr-4">
          <div className="space-y-4">
            {result.segments && result.segments.length > 0 ? (
              result.segments.map((segment, index) => (
                <div key={index} className="group relative">
                  <p className="text-gray-900">{segment.text}</p>
                  <span className="text-xs text-gray-500">
                    {formatTimestamp(segment.start)} - {formatTimestamp(segment.end)}
                  </span>
                </div>
              ))
            ) : (
              <p className="text-gray-900 whitespace-pre-wrap">{result.text}</p>
            )}
          </div>
        </ScrollArea>

        {/* Statistics */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex justify-between text-sm text-gray-600">
            <span>
              文字数: {result.text.length}
            </span>
            <span>
              セグメント数: {result.segments?.length || 1}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Helper function to format timestamp (seconds) to MM:SS format
const formatTimestamp = (seconds: number): string => {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.floor(seconds % 60);
  return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
};

export default TranscriptionView;
