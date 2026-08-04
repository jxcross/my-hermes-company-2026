#!/usr/bin/env python3
"""
객관 게이트: 법률 문서 안전 — 고지 강제 + 개인정보 평문 차단
===============================================================
① 모든 법률 문서에 **"변호사 검토 필요" 고지**가 붙어 있는지
② 문서에 **주민등록번호·사업자등록번호 등 실제 개인정보가 평문으로** 들어 있지 않은지
LLM 없이 검사한다.

⚠️ **②는 원본에 없다. 우리 운영 환경 때문에 필요하다** (docs/13 §5):
   legalforge 는 `_personal/` 을 만들고 "commit 금지" 를 **CLAUDE.md 에 지시만** 한다.
   그런데 우리 파이프라인의 Deliver 단계는 `reports/<MID>/` 를 **커밋하고 GitHub 로 push**
   하며, 이 저장소는 **PUBLIC** 이다. 계약서 초안에 당사자 주민등록번호가 들어간 채로
   미션이 끝나면 그 순간 공개된다. **되돌릴 수 없는 사고**이므로 지시가 아니라 기계 검사로
   막는다(patentforge 의 고지 승격과 같은 패턴 — 도메인의 법적·안전 요구는 게이트로 올린다).

   초안은 **플레이스홀더**로 쓴다: `[갑의 사업자등록번호]` 또는 `000-00-00000`.
   실제 값은 저장소 밖에서 사람이 채운다.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.legal_safety_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : docs/ 디렉터리 또는 단일 문서

정책 필드(legal_safety_policy)
  require_disclaimer (기본 true) · disclaimer_terms
  block_pii (기본 true) · pii_kinds (기본 전체) · allow_placeholder (기본 true)

exit: 0 PASS · 1 FAIL · 2 usage/입력없음(fail-closed)
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML 필요", file=sys.stderr); sys.exit(2)

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)

DEFAULT_DISCLAIMER_TERMS = [
    "변호사 검토", "법률 자문이 아닙니다", "법률 자문 아님", "자격 있는 변호사",
    "not legal advice", "attorney review",
]

# 개인정보 패턴. 값 자체가 들어오면 안 되는 것들.
PII_PATTERNS: dict[str, tuple[str, str]] = {
    "주민등록번호": (r"\b\d{6}\s*[-–—]\s*[1-4]\d{6}\b", "고유식별정보 — 초안에 들어갈 이유가 없다"),
    "외국인등록번호": (r"\b\d{6}\s*[-–—]\s*[5-8]\d{6}\b", "고유식별정보"),
    "법인등록번호": (r"\b\d{6}\s*[-–—]\s*\d{7}\b", "등기부 식별정보"),
    "사업자등록번호": (r"\b\d{3}\s*[-–—]\s*\d{2}\s*[-–—]\s*\d{5}\b", "플레이스홀더로 쓰라"),
    "신용카드번호": (r"\b\d{4}[-–—\s]\d{4}[-–—\s]\d{4}[-–—\s]\d{4}\b", "결제정보"),
    "여권번호": (r"\b[A-Z]{1,2}\d{7,8}\b", "고유식별정보"),
    "계좌번호": (r"(?:계좌|예금주|입금)[^\n]{0,24}?\b\d{2,6}[-–—]\d{2,6}[-–—]\d{2,8}\b", "금융정보"),
}


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("legal_safety_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("legal_safety_policy", {}) or {}


def is_placeholder(raw: str) -> bool:
    """`000-00-00000`·`111111-1111111` 처럼 **같은 숫자 반복**은 채워 넣을 자리다.
    실제 번호는 이런 모양이 되지 않는다."""
    digits = re.sub(r"\D", "", raw)
    return len(set(digits)) <= 1


def scan_pii(text: str, kinds: list[str], allow_placeholder: bool) -> list[tuple[str, str]]:
    hits = []
    for kind in kinds:
        pat = PII_PATTERNS.get(kind)
        if not pat:
            continue
        for m in re.finditer(pat[0], text):
            raw = m.group(0)
            if allow_placeholder and is_placeholder(raw):
                continue
            hits.append((kind, raw))
    return hits


def doc_files(draft: str) -> list[str]:
    if os.path.isdir(draft):
        out = []
        for dirpath, _dirs, names in os.walk(draft):
            out += [os.path.join(dirpath, n) for n in sorted(names) if n.endswith(".md")]
        return sorted(out)
    return [draft] if os.path.isfile(draft) else []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="미사용(gate_keeper 규약상 전달됨)")
    ap.add_argument("--draft", default=None, help="docs/ 디렉터리 또는 단일 문서")
    args = ap.parse_args()

    if not args.draft:
        print("FAIL(usage): --draft(docs/) 필수 — fail-closed", file=sys.stderr); return 2
    try:
        policy = load_policy(args.policy)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2

    files = doc_files(args.draft)
    if not files:
        print(f"FAIL(usage): 문서를 찾지 못했다({args.draft}) — fail-closed", file=sys.stderr)
        return 2

    require_disc = bool(policy.get("require_disclaimer", True))
    terms = policy.get("disclaimer_terms") or DEFAULT_DISCLAIMER_TERMS
    block_pii = bool(policy.get("block_pii", True))
    kinds = policy.get("pii_kinds") or list(PII_PATTERNS)
    allow_ph = bool(policy.get("allow_placeholder", True))

    print(f"문서 {len(files)}건 · 고지 필수={require_disc} · 개인정보 차단={block_pii} "
          f"· 플레이스홀더 허용={allow_ph}")

    fail = False
    for path in files:
        name = os.path.basename(path)
        try:
            text = open(path, encoding="utf-8").read()
        except OSError as e:
            print(f"FAIL: {name} 읽기 실패 ({e})"); fail = True; continue

        bad = False
        if require_disc and not any(t.lower() in text.lower() for t in terms):
            print(f"FAIL: {name} 에 고지 문구가 없다 — 법률 문서 초안은 변호사 자문으로 "
                  f"오인될 수 있으므로 고지가 필수다(인정 문구: {terms[:2]}…)")
            bad = True
        if block_pii:
            hits = scan_pii(text, kinds, allow_ph)
            if hits:
                print(f"FAIL: {name} 에 개인정보 평문 {len(hits)}건 — 이 저장소는 PUBLIC 이고 "
                      f"Deliver 가 push 한다. 되돌릴 수 없다")
                for kind, raw in hits[:5]:
                    masked = raw[:3] + "*" * max(0, len(raw) - 3)
                    print(f"       · {kind}: {masked}  ({PII_PATTERNS[kind][1]})")
                print(f"       → 플레이스홀더로 바꿔라: `[{hits[0][0]}]` 또는 `000-00-00000`")
                bad = True
        if bad:
            fail = True
        else:
            print(f"  ✓ {name} 고지·개인정보 검사 통과")

    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
