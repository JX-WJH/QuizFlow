# app/utils/pdf_handler.py
import pdfplumber
from typing import Optional


def extract_text_from_pdf(file_path: str) -> Optional[str]:
    """
    从 PDF 文件中提取所有文本
    """
    text_content = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content += page_text + "\n"
        return text_content
    except Exception as e:
        print(f"PDF 提取失败: {e}")
        return None
