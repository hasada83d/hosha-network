# tests/conftest.py

import sys
import os

# プロジェクトルート/src をモジュール検索パスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
