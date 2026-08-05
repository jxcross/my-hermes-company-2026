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

⚠️ **공개 범위 축은 아키타입 Q(연구제안서)에서 열었다** (docs/13 §5 · 2026-08-05):
   제안서는 **심사 전 공개되면 아이디어를 선점당한다.** 개인정보만 막아서는 부족하고
   "본문이 커밋되는 위치에 있는가" 자체를 봐야 한다. 아키타입 N(dataset-release)이
   `pii_presence` 안에서 하는 일과 같은 것을 문서 아키타입에서 하는 것이므로 **쌍둥이 게이트를
   만들지 않고 이 게이트에 정책 축을 하나 열었다**(docs/13 §5 의 M 교훈).
   `publication_policy` 를 선언하지 않으면 이 검사는 돌지 않는다 — 아키타입 H 의 동작은
   그대로다.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.legal_safety_policy · policy.publication_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : docs/ 디렉터리 또는 단일 문서(공개 범위 검사는 미션 루트를 본다)

정책 필드(legal_safety_policy)
  require_disclaimer (기본 true) · disclaimer_terms · disclaimer_reason
  block_pii (기본 true) · pii_kinds (기본 전체) · allow_placeholder (기본 true)
  disclaimer_files : 고지를 요구할 파일명 목록(미선언이면 전 문서)

정책 필드(publication_policy) — 선언했을 때만 검사
  mode          : local_only(기본 — 커밋하지 않는다) | repo_commit(Sam 승인 후 커밋)
  private_dir   : 커밋되지 않는 디렉터리(기본 _private · .gitignore 대상)
  content_files : 본문에 해당하는 산출물(번들 기준 상대경로). local_only 면 이것이
                  private_dir **밖**에 있으면 FAIL, repo_commit 이면 선언 위치에 없으면 FAIL

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


def load_policy(path: str, key: str = "legal_safety_policy") -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get(key, {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get(key, {}) or {}


def mission_root(draft: str) -> str:
    """공개 범위는 미션 루트 기준으로 본다 — draft 가 하위 디렉터리여도 위로 올라가
    `SCOPE.md` 가 있는 곳을 미션 루트로 삼는다."""
    p = os.path.abspath(draft)
    if not os.path.isdir(p):
        p = os.path.dirname(p)
    cur = p
    for _ in range(4):
        if os.path.isfile(os.path.join(cur, "SCOPE.md")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return p


def check_publication_scope(root: str, pub: dict) -> tuple[bool, list[str]]:
    """선언한 공개 범위와 **실제 산출 위치**가 맞는가. (fail?, 메시지들)

    이 저장소는 PUBLIC 이고 Deliver 가 `reports/<MID>/` 를 push 한다. 제안서 본문이
    `_private/` 밖에 있으면 **심사 전에 아이디어가 공개된다** — 되돌릴 수 없다."""
    mode = str(pub.get("mode") or "local_only")
    priv = str(pub.get("private_dir") or "_private")
    files = list(pub.get("content_files") or [])
    msgs: list[str] = []
    if not files:
        return True, [f"FAIL: publication_policy.content_files 선언이 없다 — 무엇이 본문인지 "
                      f"모르면 그것이 어디 있는지도 물을 수 없다(공집합이 통과하는 자리)"]
    fail = False
    for rel in files:
        public_path = os.path.join(root, rel)
        private_path = os.path.join(root, priv, rel)
        if mode == "local_only":
            if os.path.exists(public_path):
                msgs.append(f"FAIL: 공개 범위 `local_only` 인데 본문 '{rel}' 이 커밋 대상 "
                            f"위치에 있다 — 이 저장소는 PUBLIC 이고 Deliver 가 push 한다. "
                            f"{priv}/ 안으로 옮겨라")
                fail = True
            elif not os.path.exists(private_path):
                msgs.append(f"FAIL: 본문 '{rel}' 이 {priv}/ 에도 없다 — 선언한 산출물의 부재")
                fail = True
        elif mode == "repo_commit":
            if not os.path.exists(public_path):
                msgs.append(f"FAIL: 공개 범위 `repo_commit` 인데 본문 '{rel}' 이 커밋 대상 "
                            f"위치에 없다 — 공개하기로 승인받은 것을 내지 않았다")
                fail = True
        else:
            msgs.append(f"FAIL: 알 수 없는 공개 범위 mode '{mode}' — "
                        f"local_only | repo_commit 중 하나여야 한다(fail-closed)")
            fail = True
            break
    if not fail:
        msgs.append(f"  ✓ 공개 범위 mode={mode} · 본문 {len(files)}건이 선언한 위치에 있다")
    return fail, msgs


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
        pub = load_policy(args.policy, "publication_policy")
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2

    files = doc_files(args.draft)
    if not files:
        print(f"FAIL(usage): 문서를 찾지 못했다({args.draft}) — fail-closed", file=sys.stderr)
        return 2

    require_disc = bool(policy.get("require_disclaimer", True))
    terms = policy.get("disclaimer_terms") or DEFAULT_DISCLAIMER_TERMS
    reason = policy.get("disclaimer_reason") or ("법률 문서 초안은 변호사 자문으로 오인될 수 "
                                                 "있으므로 고지가 필수다")
    disc_files = policy.get("disclaimer_files") or None
    block_pii = bool(policy.get("block_pii", True))
    kinds = policy.get("pii_kinds") or list(PII_PATTERNS)
    allow_ph = bool(policy.get("allow_placeholder", True))

    print(f"문서 {len(files)}건 · 고지 필수={require_disc}"
          f"{f'({disc_files})' if disc_files else ''} · 개인정보 차단={block_pii} "
          f"· 플레이스홀더 허용={allow_ph}")

    fail = False

    # 공개 범위 — 선언했을 때만 돈다(아키타입 H 는 선언하지 않으므로 동작 불변)
    if pub:
        scope_fail, msgs = check_publication_scope(mission_root(args.draft), pub)
        for m in msgs:
            print(m)
        fail = fail or scope_fail
    if disc_files:
        # 선언한 고지 대상 파일이 아예 없으면 FAIL — '선언 목록 대비 존재'(docs/13 §5)
        have = {os.path.basename(p) for p in files}
        for want in disc_files:
            if want not in have:
                print(f"FAIL: 고지를 요구한 파일 '{want}' 이 검사 대상에 없다")
                fail = True

    for path in files:
        name = os.path.basename(path)
        try:
            text = open(path, encoding="utf-8").read()
        except OSError as e:
            print(f"FAIL: {name} 읽기 실패 ({e})"); fail = True; continue

        bad = False
        need_disc = require_disc and (disc_files is None or name in disc_files)
        if need_disc and not any(t.lower() in text.lower() for t in terms):
            print(f"FAIL: {name} 에 고지 문구가 없다 — {reason}(인정 문구: {terms[:2]}…)")
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
