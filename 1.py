import json
from pathlib import Path

def escape_for_double_quoted_string(text: str) -> str:
    """同前面版本，保持不变"""
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = text.replace('\n', '\\n\\n')
    escaped = json.dumps(text, ensure_ascii=False)
    escaped = escaped.replace('\\\\n\\\\n', '\\n\\n')
    return escaped[1:-1]

def main():
    src = Path('1.txt')
    dst = Path('2.txt')

    raw = src.read_text(encoding='utf-8')
    fixed = escape_for_double_quoted_string(raw)
    dst.write_text(fixed, encoding='utf-8')

if __name__ == '__main__':
    main()