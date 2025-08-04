#!/bin/sh

# Python3でvenvを使用します
# 以下のコマンドでvenvを作成し、google-cloud-texttospeechを入れます
#
python3 -m venv venv
source venv/bin/activate
pip3 install google-cloud-texttospeech
