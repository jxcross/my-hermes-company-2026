#!/usr/bin/env python3
"""
객관 게이트: 비밀값 비노출 + 고지
===================================
보안 감사 산출물이 **찾아낸 비밀값을 그대로 옮겨 적지 않았는지**, 그리고 고지 문구가 있는지
LLM 없이 검사한다.

⚠️ **원본에는 이 게이트가 없다. 우리 운영 환경 때문에 필요하다** (docs/13 §5).
   secforge 의 secrets-scanner 는 하드코딩된 API 키·토큰·개인키를 찾아낸다. 그 발견을
   보고서에 **값 그대로** 적고, 우리 Deliver 단계가 `reports/` 를 커밋해 **PUBLIC 저장소로
   push** 하면 — **보안 감사가 그 자체로 유출 사고가 된다.** 찾아낸 비밀을 공개하는 셈이다.

   그래서 규약을 둔다: 발견은 **위치(`file:line`)와 마스킹된 형태**로만 적는다.
   `AKIA****`, `<redacted>`, `sk-…(마스킹)` 은 허용하고 실제 값은 반려한다.
   상세·재현 정보는 `reports/<MID>/_private/`(gitignore)에 둔다.

   legal-draft 의 `legal_safety`(개인정보)와 같은 계열이되 패턴이 다르므로 별도 게이트다 —
   한 파일에 섞으면 어느 도메인의 정책인지 흐려진다(§5 이름 충돌 교훈의 짝).

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.redaction_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : 커밋 대상 산출물 디렉터리(report/) 또는 단일 문서

정책 필드(redaction_policy)
  require_disclaimer (기본 true) · disclaimer_terms
  block_secrets (기본 true) · secret_kinds (기본 전체) · min_entropy_len (기본 20)
  scan_extensions (기본 [".md"]) — 검사할 확장자
  disclaimer_files (기본 없음) — 고지를 반드시 담아야 하는 파일 basename 목록

⚠️ **확장자를 정책으로 뺀 이유**(아키타입 M 도입, 2026-08-05). 보안 감사(L)의 산출물은
   문서뿐이라 `.md` 만 훑으면 충분했다. 그런데 AI 시스템 평가(M)는 **코드와 설정을
   커밋한다** — `src/<system>/config.yaml` 이나 `runs/<id>/config.json` 에 API 키가
   남으면 문서를 아무리 검사해도 잡히지 않는다. 기본값은 `[".md"]` 이므로 L 의 동작은
   그대로다.
   `disclaimer_files` 도 같은 이유다 — 코드 파일마다 고지 문구를 요구할 수는 없으므로,
   확장자를 넓힐 때는 고지 대상을 명시적으로 좁힌다(선언한 파일이 **없으면 FAIL**).

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
    "정식 보안 감사가 아닙니다", "정식 보안 감사 아님", "보안 전문가 검토",
    "침투 테스트를 대체하지", "not a penetration test", "not a formal security audit",
]

# 실제 비밀값의 모양. 마스킹된 형태는 아래 is_redacted 로 걸러 낸다.
SECRET_PATTERNS: dict[str, tuple[str, str]] = {
    "개인키": (r"-----BEGIN\s+(?:RSA|EC|DSA|OPENSSH|PGP)?\s*PRIVATE KEY-----", "개인키 블록 전체"),
    "AWS 액세스키": (r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b", "AWS 키 ID"),
    "GitHub 토큰": (r"\bgh[pousr]_[A-Za-z0-9]{20,}\b", "GitHub PAT"),
    "Slack 토큰": (r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b", "Slack 토큰"),
    "OpenAI 키": (r"\bsk-[A-Za-z0-9]{20,}\b", "API 키"),
    "JWT": (r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b", "서명된 토큰"),
    "자격증명 대입": (r"(?i)\b(?:password|passwd|secret|api[_-]?key|token)\s*[:=]\s*"
                r"[\"']?([A-Za-z0-9/+_\-]{20,})[\"']?", "키=값 형태의 실제 값"),
}


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("redaction_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("redaction_policy", {}) or {}


def is_redacted(raw: str) -> bool:
    """마스킹된 표기는 발견 보고에 필요하다 — 막으면 보고서를 쓸 수 없다.
    `AKIA****` · `<redacted>` · `sk-xxxx…` · 같은 문자 반복은 값이 아니다."""
    if re.search(r"\*{3,}|x{4,}|X{4,}|…|\.\.\.|<redacted>|＊{3,}|●{3,}", raw):
        return True
    tail = re.sub(r"^(?:AKIA|ASIA|gh[pousr]_|xox[baprs]-|sk-)", "", raw)
    body = re.sub(r"[^A-Za-z0-9]", "", tail)
    return len(set(body)) <= 2 if body else True


def scan(text: str, kinds: list[str]) -> list[tuple[str, str]]:
    hits = []
    for kind in kinds:
        pat = SECRET_PATTERNS.get(kind)
        if not pat:
            continue
        for m in re.finditer(pat[0], text):
            raw = m.group(0)
            if is_redacted(raw):
                continue
            hits.append((kind, raw))
    return hits


def files_of(draft: str, exts: list[str] | None = None) -> list[str]:
    exts = tuple(exts or [".md"])
    if os.path.isdir(draft):
        out = []
        for dirpath, dirs, names in os.walk(draft):
            # _private/ 는 커밋 대상이 아니다(gitignore) — 검사에서 제외한다.
            # __pycache__ 도 커밋 대상이 아니다(.gitignore).
            dirs[:] = [d for d in dirs if d not in ("_private", "__pycache__")]
            out += [os.path.join(dirpath, n) for n in sorted(names) if n.endswith(exts)]
        return sorted(out)
    return [draft] if os.path.isfile(draft) else []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="미사용(gate_keeper 규약상 전달됨)")
    ap.add_argument("--draft", default=None, help="커밋 대상 산출물 디렉터리 또는 문서")
    args = ap.parse_args()

    if not args.draft:
        print("FAIL(usage): --draft 필수 — fail-closed", file=sys.stderr); return 2
    try:
        policy = load_policy(args.policy)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2

    exts = policy.get("scan_extensions") or [".md"]
    files = files_of(args.draft, exts)
    if not files:
        print(f"FAIL(usage): 검사할 문서를 찾지 못했다({args.draft}, 확장자 {exts}) — fail-closed",
              file=sys.stderr)
        return 2

    require_disc = bool(policy.get("require_disclaimer", True))
    terms = policy.get("disclaimer_terms") or DEFAULT_DISCLAIMER_TERMS
    block = bool(policy.get("block_secrets", True))
    kinds = policy.get("secret_kinds") or list(SECRET_PATTERNS)
    disc_files = policy.get("disclaimer_files") or None

    print(f"커밋 대상 파일 {len(files)}건(확장자 {exts}) · 고지 필수={require_disc} · "
          f"비밀값 차단={block} (`_private/` 는 검사 제외 — gitignore 대상)")

    fail = False
    # 고지 대상을 명시했다면 그 파일들이 **실재하는지**부터 본다 — 없으면 검사할 것이 없어
    # 통과하는 구멍이 된다(§5 '선언 목록 대비 존재').
    if require_disc and disc_files:
        have = {os.path.basename(p) for p in files}
        gone = [n for n in disc_files if n not in have]
        if gone:
            print(f"FAIL: 고지를 담아야 할 파일 {gone} 이 커밋 대상에 없다 — 파일이 없으면 "
                  f"고지 검사가 통째로 건너뛰어진다")
            fail = True

    for path in files:
        name = os.path.relpath(path, args.draft if os.path.isdir(args.draft) else os.path.dirname(path))
        try:
            text = open(path, encoding="utf-8").read()
        except OSError as e:
            print(f"FAIL: {name} 읽기 실패 ({e})"); fail = True; continue

        bad = False
        # 고지 대상: 선언이 있으면 그 파일만, 없으면 기존 동작(검사 대상 .md 전부)
        needs_disc = (os.path.basename(path) in disc_files) if disc_files else path.endswith(".md")
        if require_disc and needs_disc and not any(t.lower() in text.lower() for t in terms):
            print(f"FAIL: {name} 에 고지 문구가 없다 — 보조 감사 결과가 정식 보안 감사로 "
                  f"오인될 수 있다(인정 문구: {terms[:2]}…)")
            bad = True
        if block:
            hits = scan(text, kinds)
            if hits:
                print(f"FAIL: {name} 에 마스킹되지 않은 비밀값 {len(hits)}건 — 이 저장소는 "
                      f"PUBLIC 이고 Deliver 가 push 한다. **감사가 유출 사고가 된다**")
                for kind, raw in hits[:5]:
                    print(f"       · {kind}: {raw[:6]}{'*' * 8}  ({SECRET_PATTERNS[kind][1]})")
                print(f"       → 위치(`file:line`)와 마스킹 형태로만 적어라: `AKIA****` · "
                      f"`<redacted>`. 상세는 `_private/` 에 둔다")
                bad = True
        if bad:
            fail = True
        else:
            print(f"  ✓ {name}")

    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
