from datetime import date
from pathlib import Path
from models import TranslationResult

VAULT_DIR = Path.home() / "Documents" / "paperwork-vault"


def write_to_vault(result: TranslationResult) -> str:
    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    filename = f"{today}-{result.document_type}.md"
    path = VAULT_DIR / filename

    action_lines = "\n".join(
        f"- [ ] {a.description}" + (f" (by {a.deadline})" if a.deadline else "")
        for a in result.actions
    )

    content = f"""---
date: {today}
type: {result.document_type}
---

## Summary
{result.summary}

## Translation
{result.translation}

## Actions
{action_lines}
"""
    path.write_text(content, encoding="utf-8")
    return str(path)
