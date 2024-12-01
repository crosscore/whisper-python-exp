import sounddevice as sd
import numpy as np
import wave
import sys

def record_audio(duration, filename, fs=44100):
    """
    音声を録音してWAVファイルとして保存する関数。

    Args:
        duration (float): 録音時間（秒）。
        filename (str): 保存するファイル名（例: 'output.wav'）。
        fs (int, optional): サンプリング周波数。デフォルトは44100Hz。
    """
    print(f"{duration}秒間の録音を開始します...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()  # 録音が完了するまで待機
    print("録音が完了しました。")

    # WAVファイルとして保存
    with wave.open(filename, 'w') as wf:
        wf.setnchannels(1)        # モノラル
        wf.setsampwidth(2)        # 16ビット
        wf.setframerate(fs)       # サンプリング周波数
        wf.writeframes(recording.tobytes())
    print(f"音声が {filename} に保存されました。")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("使用法: python record_audio.py <録音時間（秒）> <保存ファイル名.wav>")
        sys.exit(1)
    try:
        duration = float(sys.argv[1])
        filename = sys.argv[2]
        record_audio(duration, filename)
    except ValueError:
        print("録音時間は数値で指定してください。")
        sys.exit(1)
