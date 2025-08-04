#!/usr/bin/env python3
import csv
import os
import sys
import datetime
from pathlib import Path
from google.cloud import texttospeech

# Google Cloud TTSを使用するのでGoogle CloudでTTS APIを有効にし
# 必要な認証情報を取得しておくこと
# 認証情報は以下の例のように環境変数に設定する
# export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/credentials.json"

# 音声ファイルの出力設定（変更可能）
#  音声はWaveNetを使用(無料範囲と金額に注意)
#  標準では以下が使用可能
#   ja-JP ja-JP-Standard-A 女性	
#   ja-JP ja-JP-Standard-B 女性	
#   ja-JP ja-JP-Standard-C 男性	
#   ja-JP ja-JP-Standard-D 男性
#
AUDIO_CONFIG = {
    'audio_encoding': texttospeech.AudioEncoding.LINEAR16,  # 16ビットリニアPCM
    'sample_rate_hertz': 8000,                            # 8kHzサンプリング
    'speaking_rate': 1.0,                                 # 話す速度
    'language_code': 'ja-JP',                             # 日本語
    'voice_name': 'ja-JP-Standard-A',                     # ボイスの種類
    'volume_gain_db': 0.0,  # 音量調整（デシベル単位、-96.0 から +6.0）
}

# 履歴管理
# history.csvがカレントディレクトリに作成される
# 一度変換した音声は内容に変更がなければ再度変換しない
# 声種を変更した場合には全変換を再度実行する必要があるので
# history.csvを削除してから実行すること
#
HISTORY_FILE = 'history.csv'

# 出力先プレフィクス
OUTPUT_PREFIX = 'ja/'

#
# 以下、通常は変更の必要なし
#

def setup_google_cloud_tts():
    """Google Cloud TTSクライアントの初期化"""
    try:
        client = texttospeech.TextToSpeechClient()
        return client
    except Exception as e:
        print(f"Google Cloud TTSの初期化に失敗しました: {e}")
        sys.exit(1)

def read_history():
    """history.csvを読み込み、辞書として返す"""
    history = {}
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)  # ヘッダー行をスキップ
            for row in reader:
                if len(row) >= 3:
                    history[row[0]] = {'text': row[2], 'timestamp': row[3] if len(row) > 3 else '', 'char_count': int(row[4]) if len(row) > 4 else 0}
    return history

def write_history(seq, filename, text, timestamp, char_count):
    """history.csvに書き込む（文字数も追加）"""
    with open(HISTORY_FILE, mode='a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([seq, filename, text, timestamp, char_count])

def ensure_history_file():
    """history.csvが存在しない場合にヘッダーを作成（文字数カラムを追加）"""
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Sequence', 'Filename', 'Text', 'Timestamp', 'CharCount'])

def get_output_path(filename):
    prefixed_filename = f"{OUTPUT_PREFIX}{filename}"
    path = Path(prefixed_filename)
    if path.parent != Path('.'):
        path.parent.mkdir(parents=True, exist_ok=True)
    return path

def text_to_speech(client, text, output_file):
    """テキストを音声ファイルに変換"""
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code=AUDIO_CONFIG['language_code'],
        name=AUDIO_CONFIG['voice_name']
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=AUDIO_CONFIG['audio_encoding'],
        sample_rate_hertz=AUDIO_CONFIG['sample_rate_hertz'],
        speaking_rate=AUDIO_CONFIG['speaking_rate'],
        volume_gain_db=AUDIO_CONFIG['volume_gain_db']
    )

    try:
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        with open(output_file, 'wb') as out:
            out.write(response.audio_content)
        print(f"音声ファイルを生成しました: {output_file}")
    except Exception as e:
        print(f"音声ファイルの生成に失敗しました ({output_file}): {e}")

def main():
    if len(sys.argv) != 2:
        print("使用方法: python script.py <input_csv_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    if not os.path.exists(input_file):
        print(f"入力ファイルが見つかりません: {input_file}")
        sys.exit(1)

    # Google Cloud TTSクライアントの初期化
    client = setup_google_cloud_tts()

    # history.csvの読み込みと初期化
    history = read_history()
    ensure_history_file()

    # 実際に変換された文字数の合計を初期化
    converted_char_count = 0

    # CSVファイルの読み込み
    try:
        with open(input_file, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 3:
                    print(f"無効な行をスキップ: {row}")
                    continue

                seq, filename, text = row[0], row[1], row[2]
                output_path = get_output_path(filename + '.wav')

                # 文字数をカウント
                char_count = len(text)

                # 出力ファイルが存在しない、またはテキストが変更されている場合に変換
                if not output_path.exists() or seq not in history or history[seq]['text'] != text:
                    text_to_speech(client, text, output_path)
                    timestamp = datetime.datetime.now().isoformat()
                    write_history(seq, filename, text, timestamp, char_count)
                    converted_char_count += char_count
                else:
                    print(f"スキップ: {filename} (変更なし)")

        # 実際に変換された文字数の合計を表示
        print(f"変換された文字数の合計: {converted_char_count}")

    except Exception as e:
        print(f"CSVファイルの処理中にエラーが発生しました: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
