"""
オーバーレイウィンドウモジュール
翻訳結果を対象ウィンドウの上に表示する
"""

import tkinter as tk
from tkinter import font as tkfont
import win32gui
import win32con
from ctypes import windll
from typing import Optional, Tuple


class OverlayWindow:
    """翻訳結果をオーバーレイ表示するウィンドウ"""
    
    def __init__(self, parent=None):
        """
        Args:
            parent: 親ウィンドウ（Tkinter root）
        """
        self.overlay = tk.Toplevel(parent) if parent else tk.Tk()
        self.overlay.title("Translation Overlay")
        
        # ウィンドウの装飾を削除
        self.overlay.overrideredirect(True)
        
        # 常に最前面に表示
        self.overlay.attributes('-topmost', True)
        
        # 背景を半透明に
        self.overlay.attributes('-alpha', 0.85)
        
        # 背景色（暗めの色）
        self.bg_color = '#1a1a2e'
        self.overlay.configure(bg=self.bg_color)
        
        # テキスト表示用のフレーム
        self.frame = tk.Frame(self.overlay, bg=self.bg_color, padx=10, pady=8)
        self.frame.pack(fill='both', expand=True)
        
        # ヘッダー（ドラッグ用 & 閉じるボタン）
        self.header = tk.Frame(self.frame, bg='#16213e')
        self.header.pack(fill='x', pady=(0, 5))
        
        self.title_label = tk.Label(
            self.header, 
            text="🌐 翻訳結果", 
            bg='#16213e', 
            fg='#e94560',
            font=('Yu Gothic UI', 10, 'bold')
        )
        self.title_label.pack(side='left', padx=5)
        
        # 閉じるボタン
        self.close_btn = tk.Label(
            self.header, 
            text="✕", 
            bg='#16213e', 
            fg='#aaaaaa',
            font=('Arial', 12, 'bold'),
            cursor='hand2'
        )
        self.close_btn.pack(side='right', padx=5)
        self.close_btn.bind('<Button-1>', lambda e: self.hide())
        self.close_btn.bind('<Enter>', lambda e: self.close_btn.configure(fg='#e94560'))
        self.close_btn.bind('<Leave>', lambda e: self.close_btn.configure(fg='#aaaaaa'))
        
        # テキスト表示ラベル
        self.text_label = tk.Label(
            self.frame,
            text="",
            bg=self.bg_color,
            fg='#ffffff',
            font=('Yu Gothic UI', 12),
            wraplength=500,
            justify='left',
            anchor='nw'
        )
        self.text_label.pack(fill='both', expand=True)
        
        # ドラッグ用の変数
        self._drag_start_x = 0
        self._drag_start_y = 0
        
        # ドラッグイベントをバインド
        self.header.bind('<Button-1>', self._start_drag)
        self.header.bind('<B1-Motion>', self._on_drag)
        self.title_label.bind('<Button-1>', self._start_drag)
        self.title_label.bind('<B1-Motion>', self._on_drag)
        
        # リサイズ用
        self.resize_grip = tk.Label(self.overlay, text="⋮⋮", bg=self.bg_color, fg='#555555', cursor='sizing')
        self.resize_grip.place(relx=1.0, rely=1.0, anchor='se')
        self.resize_grip.bind('<Button-1>', self._start_resize)
        self.resize_grip.bind('<B1-Motion>', self._on_resize)
        
        # 初期サイズと位置
        self.overlay.geometry('400x200+100+100')
        
        # 最初は非表示
        self.overlay.withdraw()
        self.is_visible = False
        
        # 追従するウィンドウのハンドル
        self.target_hwnd: Optional[int] = None
        self.follow_offset: Tuple[int, int] = (0, 0)
    
    def _start_drag(self, event):
        """ドラッグ開始"""
        self._drag_start_x = event.x
        self._drag_start_y = event.y
    
    def _on_drag(self, event):
        """ドラッグ中"""
        x = self.overlay.winfo_x() + (event.x - self._drag_start_x)
        y = self.overlay.winfo_y() + (event.y - self._drag_start_y)
        self.overlay.geometry(f'+{x}+{y}')
    
    def _start_resize(self, event):
        """リサイズ開始"""
        self._resize_start_x = event.x_root
        self._resize_start_y = event.y_root
        self._resize_start_width = self.overlay.winfo_width()
        self._resize_start_height = self.overlay.winfo_height()
    
    def _on_resize(self, event):
        """リサイズ中"""
        delta_x = event.x_root - self._resize_start_x
        delta_y = event.y_root - self._resize_start_y
        new_width = max(200, self._resize_start_width + delta_x)
        new_height = max(100, self._resize_start_height + delta_y)
        self.overlay.geometry(f'{new_width}x{new_height}')
        self.text_label.configure(wraplength=new_width - 30)
    
    def set_text(self, text: str):
        """
        表示するテキストを設定
        
        Args:
            text: 表示するテキスト
        """
        self.text_label.configure(text=text)
    
    def show(self):
        """オーバーレイを表示"""
        self.overlay.deiconify()
        self.overlay.lift()
        self.is_visible = True
    
    def hide(self):
        """オーバーレイを非表示"""
        self.overlay.withdraw()
        self.is_visible = False
    
    def toggle(self):
        """表示/非表示を切り替え"""
        if self.is_visible:
            self.hide()
        else:
            self.show()
    
    def position_near_window(self, hwnd: int, position: str = 'right'):
        """
        指定したウィンドウの近くに配置
        
        Args:
            hwnd: ウィンドウハンドル
            position: 配置位置 ('right', 'bottom', 'top', 'left')
        """
        try:
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            
            overlay_width = self.overlay.winfo_width()
            overlay_height = self.overlay.winfo_height()
            
            if position == 'right':
                x = right + 10
                y = top
            elif position == 'bottom':
                x = left
                y = bottom + 10
            elif position == 'top':
                x = left
                y = top - overlay_height - 10
            elif position == 'left':
                x = left - overlay_width - 10
                y = top
            else:
                x = right + 10
                y = top
            
            # 画面外にはみ出さないように調整
            screen_width = self.overlay.winfo_screenwidth()
            screen_height = self.overlay.winfo_screenheight()
            
            if x + overlay_width > screen_width:
                x = left - overlay_width - 10
            if y + overlay_height > screen_height:
                y = screen_height - overlay_height - 10
            if x < 0:
                x = 10
            if y < 0:
                y = 10
            
            self.overlay.geometry(f'+{x}+{y}')
            
        except Exception as e:
            print(f"オーバーレイ配置エラー: {e}")
    
    def set_transparency(self, alpha: float):
        """
        透明度を設定
        
        Args:
            alpha: 透明度（0.0〜1.0）
        """
        self.overlay.attributes('-alpha', alpha)
    
    def set_font_size(self, size: int):
        """
        フォントサイズを設定
        
        Args:
            size: フォントサイズ
        """
        self.text_label.configure(font=('Yu Gothic UI', size))
    
    def destroy(self):
        """オーバーレイウィンドウを破棄"""
        self.overlay.destroy()


class CompactOverlay:
    """コンパクトなオーバーレイ（ウィンドウ上に直接表示）"""
    
    def __init__(self, parent=None):
        self.overlay = tk.Toplevel(parent) if parent else tk.Tk()
        self.overlay.overrideredirect(True)
        self.overlay.attributes('-topmost', True)
        self.overlay.attributes('-alpha', 0.9)
        
        # クリックスルーを有効にする（オプション）
        # self._set_click_through()
        
        self.bg_color = '#000000'
        self.overlay.configure(bg=self.bg_color)
        
        self.text_label = tk.Label(
            self.overlay,
            text="",
            bg=self.bg_color,
            fg='#00ff00',
            font=('Yu Gothic UI', 11),
            padx=8,
            pady=4
        )
        self.text_label.pack()
        
        self.overlay.withdraw()
        self.is_visible = False
    
    def _set_click_through(self):
        """クリックを透過させる（Windowsのみ）"""
        hwnd = windll.user32.GetParent(self.overlay.winfo_id())
        style = windll.user32.GetWindowLongW(hwnd, -20)  # GWL_EXSTYLE
        windll.user32.SetWindowLongW(hwnd, -20, style | 0x80000 | 0x20)  # WS_EX_LAYERED | WS_EX_TRANSPARENT
    
    def set_text(self, text: str):
        self.text_label.configure(text=text)
    
    def show_at(self, x: int, y: int):
        """指定位置に表示"""
        self.overlay.geometry(f'+{x}+{y}')
        self.overlay.deiconify()
        self.is_visible = True
    
    def hide(self):
        self.overlay.withdraw()
        self.is_visible = False
    
    def destroy(self):
        self.overlay.destroy()


if __name__ == "__main__":
    # テスト
    root = tk.Tk()
    root.withdraw()
    
    overlay = OverlayWindow(root)
    overlay.set_text("これはテスト翻訳です。\nHello, World! → こんにちは、世界！")
    overlay.show()
    
    root.mainloop()
