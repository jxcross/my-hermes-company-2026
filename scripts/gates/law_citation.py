#!/usr/bin/env python3
"""
객관 게이트: 법령 인용 형식·실재성
====================================
한국 법령 인용이 표준 형식(`법령명 제N조 제M항 제K호`)을 지키는지, 법령명이 알려진 것인지,
조문 번호가 실재 가능한 범위인지 LLM 없이 검사한다.
출처: other_projects/harness-templates/.../legalforge/scripts/law_citation_check.py

⚠️ **원본은 정상 문서도 항상 FAIL 시켰다** (docs/13 §5):
  1. **법령명 캡처가 앞 문장을 삼켰다** — `([가-힣A-Za-z0-9\\s·]+(?:법|령|규칙))` 의 문자
     클래스에 `\\s` 가 있고 탐욕적이라, "본 계약은 민법 제105조" 에서 법령명이
     **`본 계약은 민법`** 으로 잡힌다(실측). 화이트리스트 조회는 당연히 실패한다.
  2. **그 실패가 곧 FAIL 이었다** — docstring 은 "warns for unknowns; **doesn't fail**"
     이라고 했지만 코드는 `overall="WARN"` 뒤에 `return 0 if overall == "PASS" else 1`.
     즉 ①과 겹쳐 **어떤 문서를 넣어도 exit 1**. 하드게이트가 아니라 벽이었다.
  → 법령명은 **뒤에서 앞으로**(제N조 앞의 꼬리) 추출하고 화이트리스트 최장 접미사 매칭을
     쓴다. 미등재 법령은 정책 `allow_unknown`(기본 true)에 따라 WARN 으로 남긴다.

이식하며 보강한 것
  · **자기 조항 참조와 법령 인용을 구별** — 계약서의 "제5조에 따라"는 법령 인용이 아니다.
    법령명이 앞에 없으면 내부 참조로 보고 건너뛴다(원본은 이 구별이 우연히 됐을 뿐이다).
  · **조문 번호 타당성** — 원본 docstring 은 "references real laws" 를 검증한다고 했지만
    오프라인에서 조문 실재는 확인할 수 없다. 대신 **비현실적 조문 번호**(기본 >1500)를
    잡는다 — 환각된 조문은 대개 여기서 걸린다(민법 최종 조문이 제1118조다).

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.law_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : docs/ 디렉터리 또는 단일 문서

정책 필드(law_policy)
  whitelist (기본 내장 60여종) · allow_unknown (기본 true) · max_article_no (기본 1500)
  min_citations (기본 0) — 법령 근거가 하나도 없는 법률 문서를 막고 싶을 때

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

# 조문 토큰. `제` 유무를 따로 잡아 형식 오류('민법 105조')를 판정한다.
ARTICLE_RE = re.compile(r"(?P<je>제\s*)?(?P<num>\d{1,4})\s*조(?:\s*의\s*\d+)?")
# 조문 바로 뒤의 항/호(형식 검사용)
PARA_RE = re.compile(r"^\s*(?P<je>제\s*)?(?P<num>\d{1,3})\s*(?P<unit>항|호)")
# 법령명 꼬리 후보: 제N조 앞에 붙는 한글/영숫자/가운뎃점/공백 덩어리
TAIL_RE = re.compile(r"([가-힣A-Za-z0-9·]+(?:[ \t]+[가-힣A-Za-z0-9·]+)*)[ \t]*$")
LAW_SUFFIX = ("법", "법률", "령", "규칙", "규정", "조례")

DEFAULT_WHITELIST = [
    "민법", "상법", "민사소송법", "민사집행법", "형법", "형사소송법",
    "정보통신망법", "정보통신망 이용촉진 및 정보보호 등에 관한 법률",
    "개인정보보호법", "개인정보 보호법", "전자상거래법",
    "전자상거래 등에서의 소비자보호에 관한 법률",
    "전자서명법", "전자문서 및 전자거래 기본법", "신용정보법",
    "저작권법", "특허법", "실용신안법", "디자인보호법", "상표법", "부정경쟁방지법",
    "부정경쟁방지 및 영업비밀보호에 관한 법률",
    "근로기준법", "산업안전보건법", "산업재해보상보험법", "최저임금법",
    "남녀고용평등법", "기간제 및 단시간근로자 보호 등에 관한 법률", "파견근로자보호법",
    "노동조합 및 노동관계조정법", "근로자퇴직급여 보장법", "고용보험법", "직업안정법",
    "산업기술의 유출방지 및 보호에 관한 법률",
    "소비자기본법", "약관의 규제에 관한 법률", "할부거래법", "방문판매법",
    "의료법", "약사법", "의료기기법", "식품위생법",
    "환경정책기본법", "대기환경보전법", "물환경보전법",
    "부동산등기법", "건축법", "주택법", "공인중개사법",
    "은행법", "자본시장과 금융투자업에 관한 법률", "보험업법",
    "행정절차법", "행정심판법", "행정소송법", "헌법", "헌법재판소법",
    "학술진흥법", "과학기술기본법", "국가연구개발혁신법",
    "생명윤리 및 안전에 관한 법률", "중대재해 처벌 등에 관한 법률",
]


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("law_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("law_policy", {}) or {}


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def law_name_before(text: str, pos: int, whitelist: set[str]) -> str | None:
    """조문 토큰 **앞쪽에서** 법령명을 뽑는다(원본의 탐욕 캡처 결함을 뒤집은 것).
    ① 「법령명」 괄호 형태가 우선 ② 화이트리스트 **최장 접미사** 매칭
    ③ 그래도 없으면 법령 접미사로 끝나는 마지막 어절. 법령명이 없으면 None(=내부 참조)."""
    head = text[max(0, pos - 80):pos]
    stripped = head.rstrip()
    if stripped.endswith("」"):
        i = stripped.rfind("「")
        if i >= 0:
            return norm(stripped[i + 1:-1])
    m = TAIL_RE.search(head)
    if not m:
        return None
    tail = norm(m.group(1))
    # ② 화이트리스트 최장 접미사 — 긴 공식 명칭("… 등에 관한 법률")을 통째로 잡는다
    best = None
    for law in whitelist:
        if tail.endswith(law) and (best is None or len(law) > len(best)):
            best = law
    if best:
        return best
    # ③ 법령 접미사로 끝나는 마지막 어절만 취한다(앞 문장을 삼키지 않는다)
    last = tail.split(" ")[-1]
    return last if last.endswith(LAW_SUFFIX) and len(last) >= 2 else None


def check_doc(path: str, whitelist: set[str], max_article: int) -> tuple[list[dict], list[str]]:
    body = FRONTMATTER_RE.sub("", open(path, encoding="utf-8").read(), count=1)
    cites, problems = [], []
    for m in ARTICLE_RE.finditer(body):
        name = law_name_before(body, m.start(), whitelist)
        if not name:
            continue                      # 자기 조항 참조("제5조에 따라") — 법령 인용이 아니다
        num = int(m.group("num"))
        rec = {"law": name, "article": num, "raw": norm(body[max(0, m.start() - len(name) - 2):m.end()]),
               "je": bool(m.group("je")), "known": name in whitelist, "para_ok": True}
        pm = PARA_RE.match(body[m.end():m.end() + 12])
        if pm and not pm.group("je"):
            rec["para_ok"] = False
            problems.append(f"{rec['raw']} → '제{pm.group('num')}{pm.group('unit')}' 의 '제' 누락")
        if not rec["je"]:
            problems.append(f"{rec['raw']} → '제' 누락(표준: '{name} 제{num}조')")
        if num > max_article:
            problems.append(f"{rec['raw']} → 조문 번호 {num} 은 실재하기 어렵다"
                            f"(상한 {max_article}) — 환각 인용 의심")
        cites.append(rec)
    return cites, problems


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

    if os.path.isdir(args.draft):
        files = [os.path.join(args.draft, f) for f in sorted(os.listdir(args.draft)) if f.endswith(".md")]
    elif os.path.isfile(args.draft):
        files = [args.draft]
    else:
        files = []
    if not files:
        print(f"FAIL(usage): 문서를 찾지 못했다({args.draft}) — fail-closed", file=sys.stderr)
        return 2

    whitelist = set(policy.get("whitelist") or DEFAULT_WHITELIST)
    allow_unknown = bool(policy.get("allow_unknown", True))
    max_article = int(policy.get("max_article_no", 1500))
    min_citations = int(policy.get("min_citations", 0))

    print(f"화이트리스트 {len(whitelist)}종 · 미등재 허용={allow_unknown} · 조문 상한 {max_article}")

    fail, total, unknown_all = False, 0, set()
    for path in files:
        name = os.path.basename(path)
        try:
            cites, problems = check_doc(path, whitelist, max_article)
        except OSError as e:
            print(f"FAIL: {name} 읽기 실패 ({e})"); fail = True; continue
        total += len(cites)
        unknown = sorted({c["law"] for c in cites if not c["known"]})
        unknown_all |= set(unknown)
        if problems:
            print(f"FAIL: {name} 인용 형식·타당성 오류 {len(problems)}건")
            for p in problems[:5]:
                print(f"       · {p}")
            fail = True
        else:
            print(f"  ✓ {name} 법령 인용 {len(cites)}건 형식 정상")
        if unknown:
            print(f"  {'FAIL' if not allow_unknown else 'WARNING'}: {name} 화이트리스트 미등재 "
                  f"법령 {unknown} — 실재 여부를 검증자가 확인하라")
            if not allow_unknown:
                fail = True

    if total < min_citations:
        print(f"FAIL: 법령 인용 {total}건 < 최소 {min_citations}건 — 법률 문서는 근거 법령을 "
              f"명시해야 한다")
        fail = True

    print(f"인용 합계 {total}건" + (f" · 미등재 {sorted(unknown_all)}" if unknown_all else ""))
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
