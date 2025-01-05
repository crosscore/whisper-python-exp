# whisper-python-exp

## Project Directory Structure
```
whisper-python-exp/
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── audio.py          # 音声録音のエンドポイント
│   │   ├── transcription.py  # 文字起こしのエンドポイント
│   │   └── websocket.py      # WebSocket関連（後で実装）
│   ├── services/
│   │   ├── __init__.py
│   │   ├── audio_service.py         # 音声録音サービス
│   │   ├── transcription_service.py # 文字起こしサービス
│   │   └── realtime_service.py      # リアルタイム処理（後で実装）
│   ├── models/                 # Whisperモデルの保存ディレクトリ
│   ├── recorded_audio/         # 録音ファイルの保存ディレクトリ
│   ├── requirements.txt        # Python依存関係
│   └── main.py                 # FastAPIアプリケーションのエントリーポイント
│
└── frontend/
    ├── public/
    │   └── index.html          # HTMLエントリーポイント
    ├── src/
    │   ├── components/
    │   │   ├── AudioRecorder.tsx      # 録音機能UI
    │   │   ├── TranscriptionView.tsx  # 文字起こし結果表示
    │   │   └── FileUploader.tsx       # 音声ファイルアップロード
    │   ├── hooks/
    │   │   └── useAudioRecorder.ts    # 録音関連のカスタムフック
    │   ├── services/
    │   │   └── api.ts                 # バックエンドAPIとの通信
    │   ├── types/
    │   │   └── index.ts               # TypeScript型定義
    │   ├── utils/
    │   │   └── audio.ts           # 音声処理ユーティリティ
    │   ├── App.tsx                # メインアプリケーションコンポーネント
    │   ├── main.tsx               # Reactアプリケーションのエントリーポイント
    │   └── index.css              # グローバルスタイル
    ├── .gitignore
    ├── package.json          # npm依存関係
    ├── tsconfig.json         # TypeScript設定
    ├── tailwind.config.js    # Tailwind CSS設定
    ├── postcss.config.js     # PostCSS設定
    └── vite.config.ts        # Vite設定
```

## frontend settings
```
(venv_whisper) yuu@Mac whisper-python-exp % npm create vite@latest frontend -- --template react-ts
(venv_whisper) yuu@Mac whisper-python-exp % cd frontend
(venv_whisper) yuu@Mac frontend % npm install
(venv_whisper) yuu@Mac frontend % sudo chown -R $USER:$GROUP ~/.npm
(venv_whisper) yuu@Mac frontend % sudo chown -R $USER:$GROUP ~/.config
(venv_whisper) yuu@Mac frontend % npm install axios @types/node tailwindcss postcss autoprefixer @headlessui/react @heroicons/react --force
(venv_whisper) yuu@Mac frontend % npx tailwindcss init -p
(venv_whisper) yuu@Mac frontend % npm install lucide-react @radix-ui/react-slot @radix-ui/react-alert-dialog

(venv_whisper) yuu@Mac frontend % npm install @radix-ui/react-scroll-area class-variance-authority clsx tailwind-merge @types/node
```
