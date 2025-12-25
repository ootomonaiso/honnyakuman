"""
ビルドスクリプト
PyInstallerを使ってexeファイルを作成する
"""

import subprocess
import sys
import shutil
from pathlib import Path


def build():
    """アプリケーションをビルドする"""
    print("🔨 Window Translator をビルド中...")
    
    # distフォルダがあれば削除
    dist_path = Path("dist")
    if dist_path.exists():
        shutil.rmtree(dist_path)
        print("  📁 dist/ を削除しました")
    
    # buildフォルダがあれば削除
    build_path = Path("build")
    if build_path.exists():
        shutil.rmtree(build_path)
        print("  📁 build/ を削除しました")
    
    # PyInstallerコマンド
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name", "WindowTranslator",
        "--add-data", "src;src",
    ]
    
    # アイコンがあれば追加
    icon_path = Path("assets/icon.ico")
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
        print("  🎨 アイコンを追加しました")
    
    cmd.append("main.py")
    
    print(f"  🚀 実行: {' '.join(cmd)}")
    
    # ビルド実行
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode == 0:
        print("\n✅ ビルド成功!")
        print(f"   出力先: dist/WindowTranslator/")
        print(f"   実行: dist/WindowTranslator/WindowTranslator.exe")
    else:
        print("\n❌ ビルド失敗")
        sys.exit(1)


if __name__ == "__main__":
    build()
