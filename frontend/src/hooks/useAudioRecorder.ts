// src/hooks/useAudioRecorder.ts
import { useState, useCallback, useRef, useEffect } from 'react';
import { AudioAPI } from '../services/api';

interface AudioRecorderState {
  isRecording: boolean;
  isPaused: boolean;
  duration: number;
  audioBlob: Blob | null;
  error: Error | null;
}

interface UseAudioRecorderReturn extends AudioRecorderState {
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<void>;
  pauseRecording: () => void;
  resumeRecording: () => void;
  resetRecording: () => void;
}

const useAudioRecorder = (): UseAudioRecorderReturn => {
  // State management
  const [state, setState] = useState<AudioRecorderState>({
    isRecording: false,
    isPaused: false,
    duration: 0,
    audioBlob: null,
    error: null,
  });

  // Refs for managing MediaRecorder and intervals
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const audioChunks = useRef<Blob[]>([]);
  const durationInterval = useRef<number | null>(null);
  const startTime = useRef<number>(0);

  // Cleanup function
  const cleanup = useCallback(() => {
    if (durationInterval.current) {
      window.clearInterval(durationInterval.current);
      durationInterval.current = null;
    }
    if (mediaRecorder.current) {
      if (mediaRecorder.current.state !== 'inactive') {
        mediaRecorder.current.stop();
      }
      mediaRecorder.current = null;
    }
    audioChunks.current = [];
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanup();
    };
  }, [cleanup]);

  // Start recording function
  const startRecording = useCallback(async () => {
    try {
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      // Create new MediaRecorder instance
      mediaRecorder.current = new MediaRecorder(stream);
      audioChunks.current = [];

      // Handle data available event
      mediaRecorder.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.current.push(event.data);
        }
      };

      // Handle recording stop
      mediaRecorder.current.onstop = async () => {
        const audioBlob = new Blob(audioChunks.current, { type: 'audio/wav' });
        setState(prev => ({ ...prev, audioBlob, isRecording: false }));

        // Notify backend
        try {
          await AudioAPI.stopRecording();
        } catch (error) {
          console.error('Failed to notify backend of recording stop:', error);
        }
      };

      // Start recording
      mediaRecorder.current.start(1000); // Capture data in 1-second chunks
      startTime.current = Date.now();

      // Start duration timer
      durationInterval.current = window.setInterval(() => {
        setState(prev => ({
          ...prev,
          duration: Date.now() - startTime.current
        }));
      }, 1000);

      // Notify backend
      await AudioAPI.startRecording();

      setState(prev => ({
        ...prev,
        isRecording: true,
        isPaused: false,
        error: null
      }));

    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error as Error,
        isRecording: false
      }));
      cleanup();
    }
  }, [cleanup]);

  // Stop recording function
  const stopRecording = useCallback(async () => {
    if (mediaRecorder.current && mediaRecorder.current.state !== 'inactive') {
      mediaRecorder.current.stop();
      cleanup();
      setState(prev => ({
        ...prev,
        isRecording: false,
        isPaused: false
      }));
    }
  }, [cleanup]);

  // Pause recording function
  const pauseRecording = useCallback(() => {
    if (mediaRecorder.current && mediaRecorder.current.state === 'recording') {
      mediaRecorder.current.pause();
      if (durationInterval.current) {
        window.clearInterval(durationInterval.current);
      }
      setState(prev => ({ ...prev, isPaused: true }));
    }
  }, []);

  // Resume recording function
  const resumeRecording = useCallback(() => {
    if (mediaRecorder.current && mediaRecorder.current.state === 'paused') {
      mediaRecorder.current.resume();
      durationInterval.current = window.setInterval(() => {
        setState(prev => ({
          ...prev,
          duration: Date.now() - startTime.current
        }));
      }, 1000);
      setState(prev => ({ ...prev, isPaused: false }));
    }
  }, []);

  // Reset recording function
  const resetRecording = useCallback(() => {
    cleanup();
    setState({
      isRecording: false,
      isPaused: false,
      duration: 0,
      audioBlob: null,
      error: null,
    });
  }, [cleanup]);

  return {
    ...state,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    resetRecording,
  };
};

export default useAudioRecorder;
