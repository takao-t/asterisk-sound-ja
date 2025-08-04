#!/bin/sh
#
# TTSで変換するPythonスクリプトは以下のように起動します
#

# Google Cloudで作成した認証情報(JSON)を以下のように指定します
# 認証情報->サービスアカウントで.jsonを作成してください
#
# export GOOGLE_APPLICATION_CREDENTIALS="/your/path/credential.json"

# スクリプトの引数としてマスターのCSVファイルを指定します
python3 ./text2wav.py core-sounds-ja.csv

#
tar cvfz core-sound-ja.tgz ja/*
