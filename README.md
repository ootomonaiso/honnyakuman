# Window Translator 🌐

Windowsの特定のウィンドウから文字を認識（OCR）して、英語を日本語に翻訳するアプリケーションです。

## ✨ 機能

- **ウィンドウキャプチャ**: 開いているウィンドウを選択してスクリーンショットを取得
- **OCR（文字認識）**: 2つのエンジンから選択可能
  - Tesseract: 軽量で高速（要インストール）
  - EasyOCR: より高精度・GPU対応（推奨）
- **自動翻訳**: 認識した英語テキストを日本語に自動翻訳
- **自動キャプチャ**: 0.5〜5秒間隔で自動的にキャプチャ・翻訳を繰り返し
- **🪟 オーバーレイ表示**: 翻訳結果を対象ウィンドウの横に常時表示
- **🚀 GPU加速**: NVIDIA GPU（CUDA）対応で高速処理
- **結果保存**: 認識・翻訳結果をテキストファイルに保存

## 📦 必要なもの

### Python環境
- Python 3.9以上

### GPU加速（推奨）
NVIDIA GPUがある場合、CUDA版PyTorchで高速化できます：

```powershell
# CUDA版PyTorchをインストール（RTX 30/40シリーズ対応）
pip uninstall torch torchvision -y
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
```

### Tesseract OCR（オプション）
Tesseractを使用する場合は、別途インストールが必要です：

1. [Tesseract-OCR](https://github.com/UB-Mannheim/tesseract/wiki) からインストーラーをダウンロード
2. インストール時に「Additional language data」で **English** を選択
3. デフォルトのインストール先: `C:\Program Files\Tesseract-OCR`

## 🚀 セットアップ

```powershell
# リポジトリに移動
cd e:\00code\translate

# 仮想環境を作成（推奨）
python -m venv venv
.\venv\Scripts\Activate.ps1

# 依存関係をインストール
pip install -r requirements.txt
```

## 🎮 使い方

```powershell
# アプリケーションを起動
python main.py
```

### 操作手順

1. **ウィンドウを選択**: ドロップダウンから翻訳したい内容があるウィンドウを選択
2. **OCRエンジンを選択**: EasyOCR（高精度・推奨）または Tesseract（要インストール）を選択
3. **キャプチャ実行**:
   - 「📷 1回キャプチャ」: 1回だけキャプチャ・翻訳
   - 「▶️ 自動キャプチャ開始」: 指定間隔で自動的にキャプチャ・翻訳を繰り返す
4. **結果を確認**: 認識テキストと翻訳結果が表示されます
5. **オーバーレイ**: 「🪟 オーバーレイ表示」で翻訳結果を別ウィンドウに常時表示
6. **保存**: 「💾 結果を保存」で結果をテキストファイルに保存

## 📁 プロジェクト構造

```
translate/
├── main.py              # GUIアプリケーション
├── requirements.txt     # 依存関係
├── README.md           # このファイル
└── src/
    ├── __init__.py
    ├── window_capture.py  # ウィンドウキャプチャ機能
    ├── ocr_engine.py      # OCRエンジン（Tesseract/EasyOCR）
    ├── translator.py      # 翻訳機能（Google翻訳）
    └── overlay.py         # オーバーレイ表示機能
```

## ⚙️ 設定オプション

### OCRエンジン

| エンジン | 特徴 | GPU対応 | 初回起動 |
|---------|------|---------|---------|
| EasyOCR | 高精度・推奨 | ✅ | モデルダウンロード（約100MB） |
| Tesseract | 軽量・要インストール | ❌ | 即座に使用可能 |

### キャプチャ間隔
- 0.5〜5秒の間で調整可能
- GPU使用時は0.5秒でもサクサク動作

### 高速モード
- 画像を縮小して処理（デフォルトON）
- 認識精度を少し犠牲にして速度向上

### オーバーレイ機能
- 翻訳結果を常に最前面に表示
- ドラッグで移動可能
- リサイズ可能

## 🚀 パフォーマンス

| 環境 | 処理時間（目安） |
|------|-----------------|
| CPU のみ | 3〜5秒 |
| NVIDIA GPU (RTX 40系) | 0.3〜0.5秒 |

## 🔧 トラブルシューティング

### Tesseractが見つからない
```
TesseractNotFoundError: tesseract is not installed
```
→ EasyOCRを使用するか、Tesseract-OCRをインストール

### EasyOCRが遅い
- 初回起動時はモデルのダウンロードに時間がかかります
- NVIDIA GPUがある場合はCUDA版PyTorchをインストール
- 「高速モード」をONにする

### GPUが認識されない
```powershell
# 確認コマンド
python -c "import torch; print(torch.cuda.is_available())"
```
→ CUDA版PyTorchを再インストール

### 文字認識の精度が悪い
- ウィンドウのフォントサイズを大きくする
- 高速モードをOFFにする
- コントラストの高い表示設定を使用する

## � ビルド & リリース

### ローカルでビルド
```powershell
# PyInstallerでexe化
python build.py
# → dist/WindowTranslator/WindowTranslator.exe が生成される
```

### GitHub Releasesに公開
```powershell
git tag v1.0.0
git push origin v1.0.0
```

または、GitHub Actions の「Run workflow」から手動実行も可能です。

## �📝 ライセンス

MIT License

## 🙏 使用ライブラリ

- [pywin32](https://github.com/mhammond/pywin32) - Windowsウィンドウ操作
- [Pillow](https://pillow.readthedocs.io/) - 画像処理
- [pytesseract](https://github.com/madmaze/pytesseract) - Tesseract OCR
- [EasyOCR](https://github.com/JaidedAI/EasyOCR) - Deep Learning OCR
- [deep-translator](https://github.com/nidhaloff/deep-translator) - 翻訳API
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) - モダンGUI
