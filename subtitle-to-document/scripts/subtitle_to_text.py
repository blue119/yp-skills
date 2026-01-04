#!/usr/bin/env python3
"""
Subtitle to Text Converter (VTT + SRT) with Multi-Language Support

Converts WebVTT (.vtt) and SubRip (.srt) subtitle files to natural, readable
text by:
- Removing timestamps and subtitle formatting
- Merging captions into natural paragraphs based on sentence breaks
- Cleaning speaker labels, annotations and spacing (language-aware)
- Supporting English, Traditional Chinese (zh_TW), and Simplified Chinese (zh_CN)

Preferred script name: subtitle_to_text.py
This file provides convert_subtitles_to_text(...) as the main API.
Backwards-compatible alias: convert_vtt_to_text(...)
"""

import re
import sys
from pathlib import Path


# Language-specific configurations
LANGUAGE_CONFIGS = {
    'en': {
        'sentence_end': r'[.!?][\s]*$',
        'annotations': [
            r'\[(?:Music|Applause|Laughter|Inaudible|.*?)\]',
            r'\((?:Music|Applause|Laughter|Inaudible)\)'
        ],
        'fix_capitalization': True,
        'space_join': ' ',
    },
    'zh_tw': {
        'sentence_end': r'[\u3002\uff01\uff1f][\s]*$',
        'annotations': [
            r'\[(?:\u97f3\u6a02|\u638c\u8072|\u7b11\u8072|\u7121\u6cd5\u807d\u6e05|.*?)\]',
            r'\((?:\u97f3\u6a02|\u638c\u8072|\u7b11\u8072|\u7121\u6cd5\u807d\u6e05)\)',
            r'\[(?:Music|Applause|Laughter|Inaudible|.*?)\]',  # Also support English
        ],
        'fix_capitalization': False,
        'space_join': '',  # Chinese doesn't need spaces between words
    },
    'zh_cn': {
        'sentence_end': r'[\u3002\uff01\uff1f][\s]*$',
        'annotations': [
            r'\[(?:\u97f3\u4e50|\u638c\u58f0|\u7b11\u58f0|\u65e0\u6cd5\u542c\u6e05|.*?)\]',
            r'\((?:\u97f3\u4e50|\u638c\u58f0|\u7b11\u58f0|\u65e0\u6cd5\u542c\u6e05)\)',
            r'\[(?:Music|Applause|Laughter|Inaudible|.*?)\]',  # Also support English
        ],
        'fix_capitalization': False,
        'space_join': '',  # Chinese doesn't need spaces between words
    },
}


def detect_language(text):
    """
    Detect the primary language of the text.
    Returns: 'en', 'zh_tw', 'zh_cn', default 'en'.
    """
    if not text:
        return 'en'

    # Count CJK unified ideographs (basic range)
    simplified_chars = len(re.findall(r'[\u4e00-\u9fff]', text))

    # Traditional Chinese indicator characters
    traditional_indicators = ['\u81fa', '\u7063', '\u7e41', '\u9ad4', '\u61c9', '\u70ba', '\u5011', '\u500b', '\u9019', '\u8aac']
    traditional_count = sum(1 for char in traditional_indicators if char in text)

    # Simplified Chinese indicator characters
    simplified_indicators = ['\u53f0', '\u6e7e', '\u7b80', '\u4f53', '\u5e94', '\u4e3a', '\u4eec', '\u4e2a', '\u8fd9', '\u8bf4']
    simplified_count = sum(1 for char in simplified_indicators if char in text)

    if simplified_chars > len(text) * 0.3:
        if traditional_count > simplified_count:
            return 'zh_tw'
        else:
            return 'zh_cn'

    return 'en'


def remove_subtitle_formatting(text):
    """Remove common subtitle formatting tags like <v Speaker>, <c>, <i>, etc."""
    text = re.sub(r'<v\s+[^>]*>', '', text)
    text = re.sub(r'</?[^>]+>', '', text)
    return text


def remove_annotations(text, lang='en'):
    """Remove common caption annotations based on language."""
    config = LANGUAGE_CONFIGS.get(lang, LANGUAGE_CONFIGS['en'])
    for pattern in config['annotations']:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    return text


def parse_subtitle_file(sub_path, fmt='auto'):
    """Parse a subtitle file (VTT or SRT) and extract cleaned caption lines.

    Returns a tuple: (captions_list, detected_format)
    """
    p = Path(sub_path)
    raw = p.read_text(encoding='utf-8', errors='replace')

    normalized = raw.replace('\r\n', '\n').replace('\r', '\n')
    blocks = re.split(r'\n\s*\n+', normalized)

    detected = fmt
    if fmt == 'auto':
        ext = p.suffix.lower()
        if ext == '.vtt' or normalized.lstrip().startswith('WEBVTT'):
            detected = 'vtt'
        elif ext == '.srt' or '-->' in normalized:
            detected = 'srt'
        else:
            detected = 'vtt'

    captions = []

    if detected == 'vtt':
        timestamp_re = re.compile(r'\d{1,2}:\d{2}:\d{2}[.,]\d{3}\s*-->\s*\d{1,2}:\d{2}:\d{2}[.,]\d{3}')
        for block in blocks:
            lines = [ln for ln in block.split('\n') if ln.strip()]
            if not lines:
                continue
            if lines[0].startswith('WEBVTT') or lines[0].startswith('NOTE'):
                continue
            caption_text = []
            for i, line in enumerate(lines):
                if timestamp_re.search(line):
                    caption_text = lines[i+1:]
                    break
            if caption_text:
                text = ' '.join(caption_text)
                text = remove_subtitle_formatting(text)
                if text.strip():
                    captions.append(text.strip())

    elif detected == 'srt':
        for block in blocks:
            lines = [ln for ln in block.split('\n') if ln.strip()]
            if not lines:
                continue
            caption_text = []
            for i, line in enumerate(lines):
                if '-->' in line:
                    caption_text = lines[i+1:]
                    break
            if not caption_text and len(lines) >= 2 and '-->' in lines[1]:
                caption_text = lines[2:]
            if caption_text:
                text = ' '.join(caption_text)
                text = remove_subtitle_formatting(text)
                if text.strip():
                    captions.append(text.strip())

    return captions, detected


def remove_duplicates(captions):
    """Remove duplicate consecutive captions."""
    if not captions:
        return captions
    cleaned = [captions[0]]
    for caption in captions[1:]:
        if caption.lower() != cleaned[-1].lower():
            cleaned.append(caption)
    return cleaned


def merge_into_paragraphs(captions, lang='en'):
    """Merge captions into paragraphs based on sentence endings.

    Keeps each caption on its own line to avoid collapsing into one long line.
    """
    if not captions:
        return []
    config = LANGUAGE_CONFIGS.get(lang, LANGUAGE_CONFIGS['en'])
    paragraphs = []
    current = []
    sentence_end = re.compile(config['sentence_end'])
    for cap in captions:
        current.append(cap)
        if sentence_end.search(cap):
            paragraphs.append('\n'.join(current))
            current = []
    if current:
        paragraphs.append('\n'.join(current))
    return paragraphs


def fix_capitalization(text, lang='en'):
    """Fix basic capitalization issues (English only)."""
    config = LANGUAGE_CONFIGS.get(lang, LANGUAGE_CONFIGS['en'])
    if not config['fix_capitalization']:
        return text
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    text = re.sub(r'([.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), text)
    text = re.sub(r'\bi\b', 'I', text)
    text = re.sub(r"\bi\'", "I'", text)
    return text


def clean_spacing(text, lang='en'):
    """Fix spacing issues based on language while preserving line breaks."""
    lines = text.splitlines()
    cleaned_lines = []
    for line in lines:
        if not line.strip():
            cleaned_lines.append('')
            continue
        if lang in ['zh_tw', 'zh_cn']:
            line = re.sub(r'([\u4e00-\u9fff])\s+([\u4e00-\u9fff])', r'\1\2', line)
            line = re.sub(r'[ \t]{2,}', ' ', line)
            line = re.sub(r'[ \t]+([\uff0c\u3002\uff01\uff1f\u3001\uff1b\uff1a])', r'\1', line)
        else:
            line = re.sub(r'[ \t]+', ' ', line)
            line = re.sub(r'[ \t]+([,.!?;:])', r'\1', line)
            line = re.sub(r'([,.!?;:])([A-Za-z])', r'\1 \2', line)
        cleaned_lines.append(line.strip())
    return '\n'.join(cleaned_lines).strip()


def convert_subtitles_to_text(sub_path, output_path=None, lang='auto', fmt='auto'):
    """Convert subtitle file (.vtt or .srt) to readable text.

    Args:
        sub_path: Path to input subtitle file
        output_path: Path to output text file (optional)
        lang: Language code ('en', 'zh_tw', 'zh_cn', or 'auto')
        fmt: Subtitle format override ('auto', 'vtt', 'srt')

    Returns:
        Converted text as a string
    """
    captions, detected_fmt = parse_subtitle_file(sub_path, fmt=fmt)

    if lang == 'auto':
        sample_text = ' '.join(captions[:10])
        lang = detect_language(sample_text)
        print(f"\U0001F310 Detected language: {lang}")

    print(f"\U0001F4CB Detected subtitle format: {detected_fmt}")

    captions = [remove_annotations(c, lang) for c in captions]
    captions = [c.strip() for c in captions if c.strip()]
    captions = remove_duplicates(captions)
    paragraphs = merge_into_paragraphs(captions, lang)

    cleaned_paragraphs = []
    for para in paragraphs:
        para = fix_capitalization(para, lang)
        para = clean_spacing(para, lang)
        if para:
            cleaned_paragraphs.append(para)

    final_text = '\n\n'.join(cleaned_paragraphs)

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_text)
        print(f"\u2705 Converted text saved to: {output_path}")

    return final_text


# Backwards-compatible alias
def convert_vtt_to_text(sub_path, output_path=None, lang='auto'):
    return convert_subtitles_to_text(sub_path, output_path=output_path, lang=lang, fmt='vtt')


def main():
    if len(sys.argv) < 2:
        print("Usage: python subtitle_to_text.py <input.vtt|input.srt> [output.txt] [--lang en|zh_tw|zh_cn] [--format auto|vtt|srt]")
        print("\nLanguage options:")
        print("  --lang auto    Auto-detect language (default)")
        print("  --lang en      English")
        print("  --lang zh_tw   Traditional Chinese (\u7e41\u9ad4\u4e2d\u6587)")
        print("  --lang zh_cn   Simplified Chinese (\u7b80\u4f53\u4e2d\u6587)")
        print("\nFormat options:")
        print("  --format auto  Auto-detect subtitle format (default)")
        print("  --format vtt   Force VTT parsing")
        print("  --format srt   Force SRT parsing")
        print("\nIf output path is not specified, a .txt file will be created next to input.")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        sys.exit(1)

    output_path = None
    lang = 'auto'
    fmt = 'auto'

    args = sys.argv[2:]
    i = 0
    while i < len(args):
        a = args[i]
        if a == '--lang' and i + 1 < len(args):
            lang = args[i+1]
            i += 2
        elif a == '--format' and i + 1 < len(args):
            fmt = args[i+1]
            if fmt not in ['auto', 'vtt', 'srt']:
                print(f"Error: Invalid format '{fmt}'. Use: auto, vtt, or srt")
                sys.exit(1)
            i += 2
        elif a.startswith('--'):
            print(f"Warning: Unknown option: {a}")
            i += 1
        else:
            output_path = Path(a)
            i += 1

    if output_path is None:
        output_path = input_path.with_suffix('.txt')

    print(f"\U0001F4C4 Converting: {input_path}")
    text = convert_subtitles_to_text(input_path, output_path, lang, fmt)

    print("\n" + "="*60)
    print("Preview (first 500 characters):")
    print("="*60)
    print(text[:500])
    if len(text) > 500:
        print("\n[... truncated ...]")
    print("="*60)


if __name__ == '__main__':
    main()
