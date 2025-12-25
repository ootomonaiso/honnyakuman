"""
ウィンドウキャプチャモジュール
特定のウィンドウをキャプチャして画像として取得する
"""

import win32gui
import win32ui
import win32con
import win32api
import ctypes
from ctypes import windll
from PIL import Image
from typing import Optional, List, Tuple

# Windows API定数
PW_RENDERFULLCONTENT = 2


def get_window_list() -> List[Tuple[int, str]]:
    """
    開いているウィンドウの一覧を取得する
    
    Returns:
        List[Tuple[int, str]]: (ウィンドウハンドル, ウィンドウタイトル)のリスト
    """
    windows = []
    
    def enum_callback(hwnd, results):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:  # タイトルがあるウィンドウのみ
                results.append((hwnd, title))
        return True
    
    win32gui.EnumWindows(enum_callback, windows)
    return windows


def find_window_by_title(title: str) -> Optional[int]:
    """
    タイトルからウィンドウハンドルを検索する
    
    Args:
        title: 検索するウィンドウタイトル（部分一致）
    
    Returns:
        ウィンドウハンドル、見つからない場合はNone
    """
    windows = get_window_list()
    for hwnd, window_title in windows:
        if title.lower() in window_title.lower():
            return hwnd
    return None


def capture_window(hwnd: int) -> Optional[Image.Image]:
    """
    指定されたウィンドウをキャプチャする
    
    Args:
        hwnd: ウィンドウハンドル
    
    Returns:
        キャプチャした画像（PIL Image）、失敗した場合はNone
    """
    try:
        # ウィンドウのサイズを取得
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bottom - top
        
        if width <= 0 or height <= 0:
            return None
        
        # デバイスコンテキストを取得
        hwnd_dc = win32gui.GetWindowDC(hwnd)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()
        
        # ビットマップを作成
        bitmap = win32ui.CreateBitmap()
        bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
        save_dc.SelectObject(bitmap)
        
        # ctypesを使ってPrintWindowを呼び出す
        result = windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), PW_RENDERFULLCONTENT)
        
        if result == 0:
            # PrintWindowが失敗した場合はBitBltを試す
            save_dc.BitBlt((0, 0), (width, height), mfc_dc, (0, 0), win32con.SRCCOPY)
        
        # ビットマップをPIL Imageに変換
        bmp_info = bitmap.GetInfo()
        bmp_bits = bitmap.GetBitmapBits(True)
        
        image = Image.frombuffer(
            'RGB',
            (bmp_info['bmWidth'], bmp_info['bmHeight']),
            bmp_bits, 'raw', 'BGRX', 0, 1
        )
        
        # リソースを解放
        win32gui.DeleteObject(bitmap.GetHandle())
        save_dc.DeleteDC()
        mfc_dc.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwnd_dc)
        
        return image
        
    except Exception as e:
        print(f"ウィンドウキャプチャエラー: {e}")
        return None


def capture_window_region(hwnd: int, region: Tuple[int, int, int, int]) -> Optional[Image.Image]:
    """
    ウィンドウの特定領域をキャプチャする
    
    Args:
        hwnd: ウィンドウハンドル
        region: (x, y, width, height) キャプチャする領域
    
    Returns:
        キャプチャした画像（PIL Image）
    """
    full_image = capture_window(hwnd)
    if full_image is None:
        return None
    
    x, y, width, height = region
    return full_image.crop((x, y, x + width, y + height))


def bring_window_to_front(hwnd: int) -> bool:
    """
    ウィンドウを前面に持ってくる
    
    Args:
        hwnd: ウィンドウハンドル
    
    Returns:
        成功した場合True
    """
    try:
        win32gui.SetForegroundWindow(hwnd)
        return True
    except Exception as e:
        print(f"ウィンドウを前面に出せませんでした: {e}")
        return False


if __name__ == "__main__":
    # テスト用
    print("利用可能なウィンドウ一覧:")
    for hwnd, title in get_window_list():
        print(f"  [{hwnd}] {title}")
