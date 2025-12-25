"""
Window Translator - メインGUIアプリケーション
ウィンドウの文字を認識して翻訳するアプリ
"""

import customtkinter as ctk
from PIL import Image, ImageTk
import threading
import time
from typing import Optional
import sys
import os

# srcディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.window_capture import get_window_list, capture_window, find_window_by_title
from src.ocr_engine import create_ocr_engine, TesseractOCR, EasyOCREngine
from src.translator import Translator
from src.overlay import OverlayWindow


class WindowTranslatorApp(ctk.CTk):
    """メインアプリケーションウィンドウ"""
    
    def __init__(self):
        super().__init__()
        
        # ウィンドウ設定
        self.title("Window Translator - 英日翻訳")
        self.geometry("900x700")
        
        # テーマ設定
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # 状態変数
        self.selected_hwnd: Optional[int] = None
        self.ocr_engine = None
        self.translator = Translator(source_lang="en", target_lang="ja")
        self.is_capturing = False
        self.capture_thread: Optional[threading.Thread] = None
        self.current_image: Optional[Image.Image] = None
        
        # オーバーレイウィンドウ
        self.overlay: Optional[OverlayWindow] = None
        self.overlay_enabled = False
        
        # UIを構築
        self._build_ui()
        
        # ウィンドウ一覧を更新
        self._refresh_window_list()
    
    def _build_ui(self):
        """UIを構築する"""
        # メインフレーム
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # === 設定セクション ===
        settings_frame = ctk.CTkFrame(self.main_frame)
        settings_frame.pack(fill="x", padx=5, pady=5)
        
        # ウィンドウ選択
        window_label = ctk.CTkLabel(settings_frame, text="対象ウィンドウ:", font=("Yu Gothic UI", 12))
        window_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.window_combo = ctk.CTkComboBox(settings_frame, width=400, state="readonly")
        self.window_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        refresh_btn = ctk.CTkButton(settings_frame, text="🔄 更新", width=80, command=self._refresh_window_list)
        refresh_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # OCRエンジン選択
        ocr_label = ctk.CTkLabel(settings_frame, text="OCRエンジン:", font=("Yu Gothic UI", 12))
        ocr_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        self.ocr_var = ctk.StringVar(value="easyocr")
        ocr_easyocr = ctk.CTkRadioButton(settings_frame, text="EasyOCR (高精度・推奨)", 
                                         variable=self.ocr_var, value="easyocr")
        ocr_easyocr.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        ocr_tesseract = ctk.CTkRadioButton(settings_frame, text="Tesseract (要インストール)", 
                                           variable=self.ocr_var, value="tesseract")
        ocr_tesseract.grid(row=1, column=2, padx=5, pady=5, sticky="w")
        
        # キャプチャ間隔
        interval_label = ctk.CTkLabel(settings_frame, text="キャプチャ間隔:", font=("Yu Gothic UI", 12))
        interval_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        
        self.interval_slider = ctk.CTkSlider(settings_frame, from_=0.5, to=5, number_of_steps=9, width=200)
        self.interval_slider.set(1)
        self.interval_slider.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        self.interval_value_label = ctk.CTkLabel(settings_frame, text="1.0秒", font=("Yu Gothic UI", 12))
        self.interval_value_label.grid(row=2, column=2, padx=5, pady=5, sticky="w")
        self.interval_slider.configure(command=self._update_interval_label)
        
        # 高速モード
        self.fast_mode_var = ctk.BooleanVar(value=True)
        self.fast_mode_check = ctk.CTkCheckBox(settings_frame, text="⚡ 高速モード（画像を縮小して処理）", 
                                                variable=self.fast_mode_var,
                                                font=("Yu Gothic UI", 11))
        self.fast_mode_check.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        
        # === 操作ボタン ===
        button_frame = ctk.CTkFrame(self.main_frame)
        button_frame.pack(fill="x", padx=5, pady=5)
        
        self.capture_once_btn = ctk.CTkButton(button_frame, text="📷 1回キャプチャ", 
                                               command=self._capture_once, width=150)
        self.capture_once_btn.pack(side="left", padx=5, pady=5)
        
        self.start_btn = ctk.CTkButton(button_frame, text="▶️ 自動キャプチャ開始", 
                                        command=self._toggle_auto_capture, width=180,
                                        fg_color="green", hover_color="darkgreen")
        self.start_btn.pack(side="left", padx=5, pady=5)
        
        self.save_btn = ctk.CTkButton(button_frame, text="💾 結果を保存", 
                                       command=self._save_result, width=120)
        self.save_btn.pack(side="left", padx=5, pady=5)
        
        # オーバーレイボタン
        self.overlay_btn = ctk.CTkButton(button_frame, text="🪟 オーバーレイ表示", 
                                          command=self._toggle_overlay, width=150,
                                          fg_color="#6a0dad", hover_color="#4a0080")
        self.overlay_btn.pack(side="left", padx=5, pady=5)
        
        # === プレビューと結果 ===
        content_frame = ctk.CTkFrame(self.main_frame)
        content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 左側：プレビュー
        preview_frame = ctk.CTkFrame(content_frame)
        preview_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        preview_label = ctk.CTkLabel(preview_frame, text="📷 キャプチャプレビュー", font=("Yu Gothic UI", 14, "bold"))
        preview_label.pack(pady=5)
        
        self.preview_canvas = ctk.CTkLabel(preview_frame, text="ウィンドウを選択してキャプチャしてください", 
                                            width=400, height=300, fg_color="gray20", corner_radius=10)
        self.preview_canvas.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 右側：テキスト
        text_frame = ctk.CTkFrame(content_frame)
        text_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        # 認識テキスト
        ocr_label = ctk.CTkLabel(text_frame, text="📝 認識テキスト (英語)", font=("Yu Gothic UI", 12, "bold"))
        ocr_label.pack(pady=2)
        
        self.ocr_text = ctk.CTkTextbox(text_frame, height=120, font=("Consolas", 11))
        self.ocr_text.pack(fill="x", padx=5, pady=2)
        
        # 翻訳結果
        trans_label = ctk.CTkLabel(text_frame, text="🌐 翻訳結果 (日本語)", font=("Yu Gothic UI", 12, "bold"))
        trans_label.pack(pady=2)
        
        self.trans_text = ctk.CTkTextbox(text_frame, height=150, font=("Yu Gothic UI", 12))
        self.trans_text.pack(fill="both", expand=True, padx=5, pady=2)
        
        # === ステータスバー ===
        self.status_label = ctk.CTkLabel(self.main_frame, text="準備完了", font=("Yu Gothic UI", 11))
        self.status_label.pack(fill="x", padx=5, pady=5)
    
    def _update_interval_label(self, value):
        """スライダーの値ラベルを更新"""
        self.interval_value_label.configure(text=f"{value:.1f}秒")
    
    def _refresh_window_list(self):
        """ウィンドウ一覧を更新する"""
        windows = get_window_list()
        
        # 自分自身を除外
        self_title = self.title()
        window_titles = [title for hwnd, title in windows if title != self_title]
        
        self.window_data = {title: hwnd for hwnd, title in windows if title != self_title}
        
        if window_titles:
            self.window_combo.configure(values=window_titles)
            self.window_combo.set(window_titles[0])
        
        self._set_status(f"ウィンドウ一覧を更新しました ({len(window_titles)}件)")
    
    def _get_selected_hwnd(self) -> Optional[int]:
        """選択されたウィンドウのハンドルを取得"""
        selected = self.window_combo.get()
        return self.window_data.get(selected)
    
    def _init_ocr_engine(self):
        """OCRエンジンを初期化する"""
        engine_type = self.ocr_var.get()
        
        self._set_status(f"OCRエンジン ({engine_type}) を初期化中...")
        self.update()
        
        try:
            if engine_type == "tesseract":
                self.ocr_engine = create_ocr_engine("tesseract", lang="eng")
            else:
                # GPUがあれば使用（高速化）
                try:
                    import torch
                    gpu_available = torch.cuda.is_available()
                except:
                    gpu_available = False
                
                self.ocr_engine = create_ocr_engine("easyocr", languages=["en"], gpu=gpu_available)
                if gpu_available:
                    self._set_status(f"OCRエンジン ({engine_type}) 準備完了 [GPU使用]")
                    return
            
            self._set_status(f"OCRエンジン ({engine_type}) 準備完了")
        except Exception as e:
            self._set_status(f"OCRエンジンの初期化に失敗: {e}")
            self.ocr_engine = None
    
    def _capture_once(self):
        """1回キャプチャして翻訳する"""
        hwnd = self._get_selected_hwnd()
        if not hwnd:
            self._set_status("ウィンドウを選択してください")
            return
        
        # OCRエンジンが未初期化なら初期化
        if self.ocr_engine is None:
            self._init_ocr_engine()
            if self.ocr_engine is None:
                return
        
        self._set_status("キャプチャ中...")
        self.update()
        
        # キャプチャ
        image = capture_window(hwnd)
        if image is None:
            self._set_status("キャプチャに失敗しました")
            return
        
        self.current_image = image
        self._update_preview(image)
        
        # OCR
        self._set_status("文字認識中...")
        self.update()
        
        try:
            ocr_text = self.ocr_engine.recognize(image)
            self.ocr_text.delete("1.0", "end")
            self.ocr_text.insert("1.0", ocr_text)
        except Exception as e:
            self._set_status(f"OCRエラー: {e}")
            return
        
        # 翻訳
        if ocr_text.strip():
            self._set_status("翻訳中...")
            self.update()
            
            try:
                translated = self.translator.translate(ocr_text)
                self.trans_text.delete("1.0", "end")
                self.trans_text.insert("1.0", translated)
                self._update_overlay(translated)
                self._set_status("翻訳完了")
            except Exception as e:
                self._set_status(f"翻訳エラー: {e}")
        else:
            self.trans_text.delete("1.0", "end")
            self._set_status("テキストが認識されませんでした")
    
    def _update_preview(self, image: Image.Image):
        """プレビュー画像を更新する"""
        # リサイズ
        max_width = 400
        max_height = 300
        
        ratio = min(max_width / image.width, max_height / image.height)
        new_size = (int(image.width * ratio), int(image.height * ratio))
        
        resized = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # CTkImageを使用
        ctk_image = ctk.CTkImage(light_image=resized, dark_image=resized, size=new_size)
        self.preview_canvas.configure(image=ctk_image, text="")
        self.preview_canvas.image = ctk_image  # 参照を保持
    
    def _toggle_auto_capture(self):
        """自動キャプチャのオン/オフを切り替える"""
        if self.is_capturing:
            self._stop_auto_capture()
        else:
            self._start_auto_capture()
    
    def _start_auto_capture(self):
        """自動キャプチャを開始する"""
        hwnd = self._get_selected_hwnd()
        if not hwnd:
            self._set_status("ウィンドウを選択してください")
            return
        
        # OCRエンジンが未初期化なら初期化
        if self.ocr_engine is None:
            self._init_ocr_engine()
            if self.ocr_engine is None:
                return
        
        self.is_capturing = True
        self.start_btn.configure(text="⏹️ 自動キャプチャ停止", fg_color="red", hover_color="darkred")
        self.capture_once_btn.configure(state="disabled")
        
        # キャプチャスレッドを開始
        self.capture_thread = threading.Thread(target=self._auto_capture_loop, daemon=True)
        self.capture_thread.start()
        
        self._set_status("自動キャプチャ開始")
    
    def _stop_auto_capture(self):
        """自動キャプチャを停止する"""
        self.is_capturing = False
        self.start_btn.configure(text="▶️ 自動キャプチャ開始", fg_color="green", hover_color="darkgreen")
        self.capture_once_btn.configure(state="normal")
        self._set_status("自動キャプチャ停止")
    
    def _auto_capture_loop(self):
        """自動キャプチャのループ"""
        while self.is_capturing:
            hwnd = self._get_selected_hwnd()
            if not hwnd:
                break
            
            try:
                # キャプチャ
                image = capture_window(hwnd)
                if image:
                    self.current_image = image
                    self.after(0, lambda img=image: self._update_preview(img))
                    
                    # OCR
                    ocr_text = self.ocr_engine.recognize(image)
                    self.after(0, lambda t=ocr_text: self._update_ocr_text(t))
                    
                    # 翻訳
                    if ocr_text.strip():
                        translated = self.translator.translate(ocr_text)
                        self.after(0, lambda t=translated: self._update_trans_text(t))
                
            except Exception as e:
                self.after(0, lambda e=e: self._set_status(f"エラー: {e}"))
            
            # 指定間隔待機
            interval = self.interval_slider.get()
            wait_cycles = int(interval * 10)
            for _ in range(wait_cycles):
                if not self.is_capturing:
                    break
                time.sleep(0.1)
    
    def _update_ocr_text(self, text: str):
        """OCRテキストを更新する（メインスレッド用）"""
        self.ocr_text.delete("1.0", "end")
        self.ocr_text.insert("1.0", text)
    
    def _update_trans_text(self, text: str):
        """翻訳テキストを更新する（メインスレッド用）"""
        self.trans_text.delete("1.0", "end")
        self.trans_text.insert("1.0", text)
        self._update_overlay(text)
    
    def _save_result(self):
        """結果をファイルに保存する"""
        from tkinter import filedialog
        
        ocr_content = self.ocr_text.get("1.0", "end").strip()
        trans_content = self.trans_text.get("1.0", "end").strip()
        
        if not ocr_content and not trans_content:
            self._set_status("保存する内容がありません")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("テキストファイル", "*.txt"), ("すべてのファイル", "*.*")],
            title="結果を保存"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("=== 認識テキスト (英語) ===\n")
                    f.write(ocr_content)
                    f.write("\n\n=== 翻訳結果 (日本語) ===\n")
                    f.write(trans_content)
                
                self._set_status(f"保存しました: {file_path}")
            except Exception as e:
                self._set_status(f"保存に失敗: {e}")
    
    def _set_status(self, message: str):
        """ステータスメッセージを設定する"""
        self.status_label.configure(text=message)
    
    def _toggle_overlay(self):
        """オーバーレイ表示の切り替え"""
        if self.overlay is None:
            self.overlay = OverlayWindow(self)
        
        if self.overlay_enabled:
            self.overlay.hide()
            self.overlay_enabled = False
            self.overlay_btn.configure(text="🪟 オーバーレイ表示", fg_color="#6a0dad")
            self._set_status("オーバーレイを非表示にしました")
        else:
            # 現在の翻訳結果を設定
            trans_content = self.trans_text.get("1.0", "end").strip()
            if trans_content:
                self.overlay.set_text(trans_content)
            else:
                self.overlay.set_text("翻訳結果がここに表示されます")
            
            # 対象ウィンドウの横に配置
            hwnd = self._get_selected_hwnd()
            if hwnd:
                self.overlay.position_near_window(hwnd, 'right')
            
            self.overlay.show()
            self.overlay_enabled = True
            self.overlay_btn.configure(text="🪟 オーバーレイ非表示", fg_color="#4a0080")
            self._set_status("オーバーレイを表示しました（ドラッグで移動可能）")
    
    def _update_overlay(self, text: str):
        """オーバーレイの内容を更新する"""
        if self.overlay and self.overlay_enabled:
            self.overlay.set_text(text)
    
    def on_closing(self):
        """ウィンドウを閉じる時の処理"""
        self.is_capturing = False
        if self.overlay:
            self.overlay.destroy()
        self.destroy()


def main():
    """アプリケーションのエントリーポイント"""
    app = WindowTranslatorApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
