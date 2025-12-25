"""
翻訳モジュール
英語から日本語への翻訳を行う
"""

from typing import Optional
from deep_translator import GoogleTranslator, MyMemoryTranslator
import re


class Translator:
    """翻訳を行うクラス"""
    
    def __init__(self, source_lang: str = "en", target_lang: str = "ja", service: str = "google"):
        """
        Args:
            source_lang: 翻訳元の言語コード
            target_lang: 翻訳先の言語コード
            service: 使用する翻訳サービス（"google" or "mymemory"）
        """
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.service = service
        
        if service == "google":
            self.translator = GoogleTranslator(source=source_lang, target=target_lang)
        elif service == "mymemory":
            self.translator = MyMemoryTranslator(source=source_lang, target=target_lang)
        else:
            raise ValueError(f"不明な翻訳サービス: {service}")
    
    def translate(self, text: str) -> str:
        """
        テキストを翻訳する
        
        Args:
            text: 翻訳するテキスト
        
        Returns:
            翻訳されたテキスト
        """
        if not text or not text.strip():
            return ""
        
        # テキストをクリーンアップ
        cleaned_text = self._clean_text(text)
        
        if not cleaned_text:
            return ""
        
        try:
            # 長いテキストは分割して翻訳
            if len(cleaned_text) > 4500:
                return self._translate_long_text(cleaned_text)
            
            result = self.translator.translate(cleaned_text)
            return result if result else ""
            
        except Exception as e:
            print(f"翻訳エラー: {e}")
            return f"[翻訳エラー: {e}]"
    
    def _clean_text(self, text: str) -> str:
        """
        テキストをクリーンアップする
        
        Args:
            text: クリーンアップするテキスト
        
        Returns:
            クリーンアップされたテキスト
        """
        # 余分な空白を削除
        text = re.sub(r'\s+', ' ', text)
        
        # OCRの誤認識でよくある文字を修正
        text = text.replace('|', 'I')
        text = text.replace('0', 'O') if not any(c.isdigit() for c in text.replace('0', '')) else text
        
        return text.strip()
    
    def _translate_long_text(self, text: str) -> str:
        """
        長いテキストを分割して翻訳する
        
        Args:
            text: 翻訳するテキスト
        
        Returns:
            翻訳されたテキスト
        """
        # 文で分割
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        translated_parts = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < 4500:
                current_chunk += " " + sentence
            else:
                if current_chunk:
                    translated_parts.append(self.translator.translate(current_chunk.strip()))
                current_chunk = sentence
        
        if current_chunk:
            translated_parts.append(self.translator.translate(current_chunk.strip()))
        
        return ' '.join(translated_parts)
    
    def detect_language(self, text: str) -> Optional[str]:
        """
        テキストの言語を検出する（簡易版）
        
        Args:
            text: 検出するテキスト
        
        Returns:
            言語コード
        """
        # 日本語文字が含まれているかチェック
        japanese_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]')
        if japanese_pattern.search(text):
            return 'ja'
        
        # 英語のアルファベットが多い場合
        alpha_count = sum(1 for c in text if c.isalpha() and ord(c) < 128)
        if alpha_count > len(text) * 0.5:
            return 'en'
        
        return 'unknown'
    
    def translate_if_english(self, text: str) -> str:
        """
        英語の場合のみ翻訳する
        
        Args:
            text: テキスト
        
        Returns:
            翻訳されたテキスト（英語でない場合は元のテキスト）
        """
        lang = self.detect_language(text)
        
        if lang == 'en':
            return self.translate(text)
        else:
            return text


if __name__ == "__main__":
    # テスト
    translator = Translator()
    
    test_texts = [
        "Hello, how are you?",
        "This is a test message.",
        "The quick brown fox jumps over the lazy dog."
    ]
    
    print("翻訳テスト:")
    for text in test_texts:
        translated = translator.translate(text)
        print(f"  {text}")
        print(f"  → {translated}")
        print()
