// frontend/src/components/FileUploader.tsx
import React, { useCallback, useState, useRef } from 'react';
import { Upload, X, FileAudio, Loader2 } from 'lucide-react';
import { TranscriptionAPI } from '../services/api';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface FileUploaderProps {
  onUploadComplete: (result: any) => void;
  onError?: (error: Error) => void;
  accept?: string;
  maxSize?: number; // in bytes
}

const FileUploader: React.FC<FileUploaderProps> = ({
  onUploadComplete,
  onError,
  accept = '.wav,.mp3,.m4a',
  maxSize = 50 * 1024 * 1024, // 50MB default
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Handle drag events
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragging(true);
    } else if (e.type === 'dragleave') {
      setIsDragging(false);
    }
  }, []);

  // Validate file
  const validateFile = (file: File): string | null => {
    if (!file.type.startsWith('audio/') && !file.name.match(/\.(wav|mp3|m4a)$/)) {
      return '対応していないファイル形式です。WAV, MP3, M4Aファイルをアップロードしてください。';
    }
    if (file.size > maxSize) {
      return `ファイルサイズが大きすぎます。${Math.floor(maxSize / 1024 / 1024)}MB以下のファイルをアップロードしてください。`;
    }
    return null;
  };

  // Handle file selection
  const handleFile = async (file: File) => {
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      setSelectedFile(null);
      if (onError) onError(new Error(validationError));
      return;
    }

    setSelectedFile(file);
    setError(null);

    // Auto upload when file is selected
    await handleUpload(file);
  };

  // Handle drop event
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const { files } = e.dataTransfer;
    if (files && files[0]) {
      handleFile(files[0]);
    }
  }, []);

  // Handle file input change
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { files } = e.target;
    if (files && files[0]) {
      handleFile(files[0]);
    }
  };

  // Handle upload button click
  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  // Handle file upload
  const handleUpload = async (file: File) => {
    setIsUploading(true);
    setError(null);

    try {
      const result = await TranscriptionAPI.transcribeFile(file);
      onUploadComplete(result);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '音声ファイルのアップロードに失敗しました。';
      setError(errorMessage);
      if (onError && err instanceof Error) onError(err);
    } finally {
      setIsUploading(false);
    }
  };

  // Reset component state
  const handleReset = () => {
    setSelectedFile(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        accept={accept}
        onChange={handleChange}
      />

      {/* Upload area */}
      <div
        className={`relative border-2 border-dashed rounded-lg p-8 text-center ${
          isDragging
            ? 'border-blue-500 bg-blue-50'
            : error
            ? 'border-red-300 bg-red-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
      >
        {isUploading ? (
          // Uploading state
          <div className="flex flex-col items-center justify-center">
            <Loader2 className="w-12 h-12 text-blue-500 animate-spin" />
            <p className="mt-2 text-sm text-gray-600">アップロード中...</p>
          </div>
        ) : selectedFile ? (
          // Selected file state
          <div className="flex flex-col items-center">
            <FileAudio className="w-12 h-12 text-blue-500" />
            <p className="mt-2 text-sm text-gray-600">{selectedFile.name}</p>
            <button
              onClick={handleReset}
              className="mt-2 flex items-center text-red-500 hover:text-red-600"
            >
              <X className="w-4 h-4 mr-1" />
              キャンセル
            </button>
          </div>
        ) : (
          // Empty state
          <div className="flex flex-col items-center">
            <Upload className="w-12 h-12 text-gray-400" />
            <p className="mt-2 text-sm text-gray-600">
              ファイルをドラッグ&ドロップ、または
            </p>
            <button
              onClick={handleButtonClick}
              className="mt-2 text-blue-500 hover:text-blue-600"
            >
              クリックしてファイルを選択
            </button>
            <p className="mt-2 text-xs text-gray-500">
              対応形式: WAV, MP3, M4A (最大 {Math.floor(maxSize / 1024 / 1024)}MB)
            </p>
          </div>
        )}
      </div>

      {/* Error message */}
      {error && (
        <Alert variant="destructive" className="mt-4">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
    </div>
  );
};

export default FileUploader;
