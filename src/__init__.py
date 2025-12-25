"""
Window Translator Package
ウィンドウの文字認識と翻訳を行うパッケージ
"""

from .window_capture import get_window_list, find_window_by_title, capture_window
from .ocr_engine import create_ocr_engine, TesseractOCR, EasyOCREngine
from .translator import Translator

__all__ = [
    'get_window_list',
    'find_window_by_title', 
    'capture_window',
    'create_ocr_engine',
    'TesseractOCR',
    'EasyOCREngine',
    'Translator'
]
