# Skills Repository

This repo contains skills focused on my daily works.

## Installation (Codex)

Clone or copy this repo into your Codex skills folder, then restart Claude/Codex:

```bash
mkdir -p $CODEX_HOME/skills
cp -R /path/to/this/repo/* $CODEX_HOME/skills/
```

## Skills
### subtitle-to-document

Convert subtitle files (.vtt or .srt) into readable text documents. It removes timestamps and formatting, merges captions into natural paragraphs, and applies language-aware spacing and cleanup for English, Traditional Chinese, or Simplified Chinese.

How to use:
- Run the conversion script with an input subtitle file.
- Output defaults to `<input_basename>.txt` next to the source file, or you can pass a custom output path.

### internal-doc-polisher

Transform raw or transcript-like text into a polished Markdown document for internal sharing. It repairs sentences, restructures content into clear headings and paragraphs, adds a concise summary, and includes an Action Items section when tasks are present.

How to use:
- Provide a text file (zh_tw, zh_cn, or en).
- The skill outputs a cleaned `.md` file, defaulting to `<input_basename>.md` unless you specify another path.

