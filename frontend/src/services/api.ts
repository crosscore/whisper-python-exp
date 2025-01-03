// frontend/src/services/api.ts
import axios from 'axios';

const BASE_URL = 'http://localhost:8000';
const api = axios.create({ baseURL: BASE_URL });

// Types
export interface RecordingStatus {
  is_recording: boolean;
  sample_rate: number;
  channels: number;
  queue_size: number;
}

export interface Recording {
  filename: string;
  path: string;
  size: number;
  created: number;
}

export interface TranscriptionResult {
  text: string;
  language: string;
  segments: Array<{
    text: string;
    start: number;
    end: number;
  }>;
}

export interface ModelInfo {
  model_name: string;
  language: string;
  device: string;
  model_path: string;
}

// Audio Recording API
export const AudioAPI = {
  startRecording: async (): Promise<boolean> => {
    const response = await api.post('/start');
    return response.data.success;
  },

  stopRecording: async (): Promise<string> => {
    const response = await api.post('/stop');
    return response.data.filename;
  },

  getStatus: async (): Promise<RecordingStatus> => {
    const response = await api.get('/status');
    return response.data;
  },

  listRecordings: async (): Promise<Recording[]> => {
    const response = await api.get('/recordings');
    return response.data;
  },

  downloadRecording: (filename: string): string => {
    return `${BASE_URL}/download/${filename}`;
  }
};

// Transcription API
export const TranscriptionAPI = {
  // Upload and transcribe a new audio file
  transcribeFile: async (file: File, language?: string): Promise<TranscriptionResult> => {
    const formData = new FormData();
    formData.append('file', file);
    if (language) {
      formData.append('language', language);
    }

    const response = await api.post('/transcribe', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Transcribe an existing recording
  transcribeRecording: async (recordingId: string): Promise<TranscriptionResult> => {
    const response = await api.post(`/transcribe/${recordingId}`);
    return response.data;
  },

  // Get model information
  getModelInfo: async (): Promise<ModelInfo> => {
    const response = await api.get('/model-info');
    return response.data;
  }
};

// WebSocket handling for real-time transcription
export class RealtimeTranscriptionService {
  private ws: WebSocket | null = null;
  private onTranscriptionCallback: ((result: TranscriptionResult) => void) | null = null;

  constructor() {
    this.ws = null;
  }

  connect(onTranscription: (result: TranscriptionResult) => void): void {
    this.onTranscriptionCallback = onTranscription;
    this.ws = new WebSocket(`ws://${window.location.hostname}:8000/ws/audio`);

    this.ws.onmessage = (event) => {
      const result = JSON.parse(event.data);
      if (this.onTranscriptionCallback) {
        this.onTranscriptionCallback(result);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket connection closed');
      this.ws = null;
    };
  }

  sendAudioData(audioData: ArrayBuffer): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(audioData);
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export default {
  AudioAPI,
  TranscriptionAPI,
  RealtimeTranscriptionService
};
