"""
OCRエンジンモジュール
画像から文字を認識する
"""

from PIL import Image, ImageEnhance, ImageFilter
from typing import Optional, List, Tuple
import os


def preprocess_image(image: Image.Image, max_width: int = 1200) -> Image.Image:
    """
    OCR用に画像を前処理する（速度向上のため）
    
    Args:
        image: 入力画像
        max_width: 最大幅（これより大きい場合はリサイズ）
    
    Returns:
        前処理済み画像
    """
    # 大きすぎる画像はリサイズ（速度向上）
    if image.width > max_width:
        ratio = max_width / image.width
        new_size = (max_width, int(image.height * ratio))
        image = image.resize(new_size, Image.Resampling.LANCZOS)
    
    # グレースケール化
    if image.mode != 'L':
        image = image.convert('L')
    
    # コントラスト強調
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.5)
    
    return image


class OCREngine:
    """OCRエンジンの基底クラス"""
    
    def recognize(self, image: Image.Image) -> str:
        """画像から文字を認識する"""
        raise NotImplementedError


class TesseractOCR(OCREngine):
    """
    Tesseract OCRエンジン
    軽量で高速、ただしインストールが必要
    """
    
    def __init__(self, tesseract_path: Optional[str] = None, lang: str = "eng"):
        """
        Args:
            tesseract_path: Tesseractの実行ファイルパス
            lang: 認識する言語（eng, jpn, eng+jpn など）
        """
        import pytesseract
        
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        elif os.path.exists(r"C:\Program Files\Tesseract-OCR\tesseract.exe"):
            pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        
        self.pytesseract = pytesseract
        self.lang = lang
    
    def recognize(self, image: Image.Image) -> str:
        """
        画像から文字を認識する
        
        Args:
            image: 入力画像
        
        Returns:
            認識されたテキスト
        """
        # 画像を前処理（グレースケール化して認識精度を上げる）
        if image.mode != 'L':
            gray_image = image.convert('L')
        else:
            gray_image = image
        
        text = self.pytesseract.image_to_string(gray_image, lang=self.lang)
        return text.strip()
    
    def recognize_with_boxes(self, image: Image.Image) -> List[dict]:
        """
        画像から文字を認識し、位置情報も取得する
        
        Args:
            image: 入力画像
        
        Returns:
            認識結果のリスト（text, left, top, width, height）
        """
        data = self.pytesseract.image_to_data(image, lang=self.lang, output_type=self.pytesseract.Output.DICT)
        
        results = []
        for i in range(len(data['text'])):
            if data['text'][i].strip():
                results.append({
                    'text': data['text'][i],
                    'left': data['left'][i],
                    'top': data['top'][i],
                    'width': data['width'][i],
                    'height': data['height'][i],
                    'confidence': data['conf'][i]
                })
        
        return results


class EasyOCREngine(OCREngine):
    """
    EasyOCR エンジン
    より高精度、ただし初回起動時にモデルダウンロードが必要
    """
    
    def __init__(self, languages: List[str] = None, gpu: bool = False):
        """
        Args:
            languages: 認識する言語のリスト（['en', 'ja'] など）
            gpu: GPUを使用するかどうか
        """
        import easyocr
        
        if languages is None:
            languages = ['en']
        
        self.reader = easyocr.Reader(languages, gpu=gpu)
        self.languages = languages
    
    def recognize(self, image: Image.Image) -> str:
        """
        画像から文字を認識する
        
        Args:
            image: 入力画像
        
        Returns:
            認識されたテキスト
        """
        import numpy as np
        
        # 前処理で高速化
        processed = preprocess_image(image, max_width=1000)
        
        # PIL ImageをNumPy配列に変換
        image_np = np.array(processed)
        
        # OCR実行（パラメータ調整で高速化）
        results = self.reader.readtext(
            image_np,
            paragraph=True,      # 段落としてまとめる（高速化）
            min_size=10,         # 小さすぎる文字を無視
            text_threshold=0.7,  # 信頼度閾値を上げる
            low_text=0.3,
            width_ths=0.7,       # 単語の結合閾値
        )
        
        # テキストを結合
        texts = [result[1] for result in results]
        return '\n'.join(texts)
    
    def recognize_with_boxes(self, image: Image.Image) -> List[dict]:
        """
        画像から文字を認識し、位置情報も取得する
        
        Args:
            image: 入力画像
        
        Returns:
            認識結果のリスト
        """
        import numpy as np
        
        image_np = np.array(image)
        results = self.reader.readtext(image_np)
        
        output = []
        for bbox, text, confidence in results:
            # bboxは4点の座標 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            x_coords = [point[0] for point in bbox]
            y_coords = [point[1] for point in bbox]
            
            output.append({
                'text': text,
                'left': int(min(x_coords)),
                'top': int(min(y_coords)),
                'width': int(max(x_coords) - min(x_coords)),
                'height': int(max(y_coords) - min(y_coords)),
                'confidence': confidence * 100  # パーセントに変換
            })
        
        return output


def create_ocr_engine(engine_type: str = "tesseract", **kwargs) -> OCREngine:
    """
    OCRエンジンを作成するファクトリー関数
    
    Args:
        engine_type: "tesseract" または "easyocr"
        **kwargs: エンジン固有のオプション
    
    Returns:
        OCRエンジンインスタンス
    """
    if engine_type.lower() == "tesseract":
        return TesseractOCR(**kwargs)
    elif engine_type.lower() == "easyocr":
        return EasyOCREngine(**kwargs)
    else:
        raise ValueError(f"不明なOCRエンジン: {engine_type}")


if __name__ == "__main__":
    # テスト用
    print("OCRエンジンモジュールがロードされました")
    print("利用可能なエンジン: tesseract, easyocr")
