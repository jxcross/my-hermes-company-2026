#!/usr/bin/env python3
"""
산출 도구: BibTeX 내보내기
==========================
`raw/sources.yaml` → `references.bib`. 아키타입 B(학술 논문)의 Deliver 단계에서 쓴다.

⚠️ 이것은 **게이트가 아니라 산출 도구**다(판정하지 않는다). 그래서 `scripts/gates/`가 아니라
`scripts/tools/`에 둔다 — gate_keeper 는 `scripts/gates/*.py`만 exit code 로 판정한다.
출처: other_projects/harness-templates/.../paperforge/scripts/bib_export.py 를 우리
sources.yaml 스키마(fenced markdown → YAML)로 재작성.

입력
  --sources <path>  : raw/sources.yaml (id·title·authors·published_year·venue·doi·url·bibtype)
  --draft   <path>  : (선택) 원고. 주면 **실제 인용된 id 만** 내보낸다(미인용 항목 제외).
  --out     <path>  : 출력 .bib (기본 sources.yaml 옆의 references.bib)

bibtype 기본 @article. 항목에 `bibtype: inproceedings|misc|techreport` 로 재지정 가능.
exit: 0 성공 · 2 usage/입력오류
"""
from __future__ import annotations
import argparse
import os
import re
import sys

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML 필요", file=sys.stderr); sys.exit(2)

CITATION_RE = re.compile(r"\[([a-z][a-z0-9_\-]*)\]", re.IGNORECASE)
FIELD_MAP = {          # sources.yaml 키 → BibTeX 필드
    "title": "title",
    "authors": "author",
    "published_year": "year",
    "venue": "journal",
    "doi": "doi",
    "url": "url",
    "note": "note",
}
DROP = {"id", "status", "bibtype", "seminal", "source_type", "collected_at", "relevance"}


def load_sources(path: str) -> list[dict]:
    data = yaml.safe_load(open(path, encoding="utf-8").read())
    if isinstance(data, dict):
        data = data.get("sources", [])
    return [s for s in (data or []) if isinstance(s, dict) and s.get("id")]


def escape(v) -> str:
    """BibTeX 에서 의미를 갖는 문자를 중화한다."""
    s = str(v).replace("\\", r"\textbackslash{}")
    for ch in "{}$&#_%":
        s = s.replace(ch, "\\" + ch)
    return s.replace("\n", " ").strip()


def authors_field(v) -> str:
    if isinstance(v, (list, tuple)):
        return " and ".join(escape(a) for a in v)
    # "홍길동, 김철수" 또는 "A and B" 둘 다 수용
    s = str(v)
    parts = [p.strip() for p in re.split(r",| and ", s) if p.strip()]
    return " and ".join(escape(p) for p in parts) if parts else escape(s)


def to_entry(s: dict) -> str:
    btype = str(s.get("bibtype") or "article").strip().lstrip("@")
    lines = [f"@{btype}{{{s['id']},"]
    for key, field in FIELD_MAP.items():
        if key not in s or s[key] in (None, ""):
            continue
        val = authors_field(s[key]) if key == "authors" else escape(s[key])
        lines.append(f"  {field} = {{{val}}},")
    for k, v in s.items():           # 알려지지 않은 필드는 그대로 통과
        if k in FIELD_MAP or k in DROP or v in (None, ""):
            continue
        lines.append(f"  {escape(k)} = {{{escape(v)}}},")
    lines[-1] = lines[-1].rstrip(",")
    lines.append("}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sources", required=True)
    ap.add_argument("--draft", default=None, help="주면 인용된 id 만 내보낸다")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    try:
        sources = load_sources(args.sources)
    except (OSError, yaml.YAMLError) as e:
        print(f"ERROR: sources 읽기 실패 ({e})", file=sys.stderr); return 2
    if not sources:
        print("ERROR: 내보낼 항목이 없다(id 있는 항목 0건)", file=sys.stderr); return 2

    picked = [s for s in sources if str(s.get("status", "selected")).lower() not in ("failed", "excluded")]
    if args.draft:
        try:
            keys = {k.lower() for k in CITATION_RE.findall(open(args.draft, encoding="utf-8").read())}
            cited = [s for s in picked if str(s["id"]).lower() in keys]
            if cited:
                picked = cited
            else:
                print("WARNING 원고에서 인용 키를 찾지 못했다 — 전체를 내보낸다", file=sys.stderr)
        except OSError as e:
            print(f"WARNING draft 읽기 실패({e}) — 전체를 내보낸다", file=sys.stderr)

    out = args.out or os.path.join(os.path.dirname(os.path.abspath(args.sources)), "references.bib")
    body = "\n\n".join(to_entry(s) for s in picked) + "\n"
    try:
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        open(out, "w", encoding="utf-8").write(body)
    except OSError as e:
        print(f"ERROR: 쓰기 실패 ({e})", file=sys.stderr); return 2

    print(f"{len(picked)}건 → {out}" + (" (인용분만)" if args.draft else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
