#!/usr/bin/env python3
r"""
객관 게이트: 개인정보 잔존 + 공개 범위
========================================
배포 번들의 **모든 데이터 파일**에 개인정보가 남아 있지 않은지, 그리고 **선언한 공개 범위와
실제 산출 위치가 맞는지** LLM 없이 검사한다.
출처: other_projects/harness-templates/.../datasetforge/scripts/{pii_scan,pii_license_check}.py

⚠️ **원본 하드게이트는 샤드 하나만 스캔한다** (docs/13 §5 · 실측):
   `find_canonical_parquet` 는 `parquet/data.parquet` 가 없으면 `sorted(glob("data-*.parquet"))[0]`
   를 돌려준다 — **첫 샤드 하나**다. 샤드 100개짜리 데이터셋이면 1%만 검사하고 PASS 한다.
   게다가 검사 대상은 parquet(또는 HF 샤드) **한 갈래뿐**이라 CSV/JSONL 산출물은 아예 보지
   않는다. 같은 데이터를 세 포맷으로 내보내는 파이프라인에서 **두 포맷이 미검사**다.
   → 우리는 **모든 포맷의 모든 파일**을 훑는다.

⚠️ **검사할 수 없는 형식은 '깨끗하다'가 아니다.** 우리 컨테이너에는 pandas·pyarrow 가 없어
   parquet 을 읽을 수 없다. 읽지 못한 데이터 파일을 조용히 건너뛰면 원본의 샤드 함정을 형태만
   바꿔 되풀이하는 것이다. → **읽을 수 없는 데이터 파일이 있으면 FAIL(fail-closed)** 하고,
   무엇을 못 읽었는지 밝힌다. 정본은 stdlib 로 읽히는 `.jsonl`/`.csv` 로 두고, parquet 을
   내보내려면 `pyarrow` 를 설치하라는 뜻이다.

⚠️ **원본 정규식은 양방향으로 무너진다**(실측):
   · **놓친다** — 신용카드 Luhn 검사가 `text[p:p+19]` 라는 **고정 창**을 본다.
     `금액 4111111111111111.50 원` 은 창에 `.50` 이 끼어 자릿수가 18이 되어 **미검출**.
     → 매치된 문자열 자체로 Luhn 을 돌린다.
   · **과검출한다** — `phone_kr` 의 선두 0 이 선택(`0?1[016789]`)이라 평범한 숫자를 전화번호로
     잡는다. 실측: `측정값 1012345678` → **phone_kr·phone_us 둘 다 HIGH**,
     `행 id 20191055512345` → phone_kr HIGH. HIGH 는 하드게이트 FAIL 이므로 **10자리 이상
     숫자 id 를 가진 정상 데이터셋은 영영 배포되지 않는다.**
     → 선두 `01` 을 필수로 하고 앞뒤 숫자 경계(`(?<!\d)`·`(?!\d)`)를 건다.

⚠️ **마스킹 표기는 통과시켜야 한다.** redaction 결과가 `<EMAIL>`·`***-****-****` 인데 이를
   막으면 정제된 데이터셋을 배포할 방법이 없다(`secret_redaction` 의 `is_redacted` 와 같은 규율).

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.pii_policy · policy.publication_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : 미션 디렉터리

정책 필드(pii_policy)
  patterns (기본 전체) · fail_on (기본 [high]) · max_medium (기본 null=무제한)
  data_extensions (기본 .jsonl/.json/.csv/.tsv/.txt/.md)
  unreadable_extensions (기본 .parquet/.arrow/.feather — 읽으면 통과, 못 읽으면 FAIL)
정책 필드(publication_policy)
  mode: local_only(기본) | repo_commit
  private_bundle (기본 _private/bundle) · public_bundle (기본 bundle)

exit: 0 PASS · 1 FAIL · 2 usage/입력없음(fail-closed)
"""
from __future__ import annotations
import argparse
import csv
import io
import json
import os
import re
import sys

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML 필요", file=sys.stderr); sys.exit(2)

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)

# (정규식, 심각도). 원본에서 고친 자리는 주석으로 표시했다.
PATTERNS: dict[str, tuple[re.Pattern, str]] = {
    "email": (re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"), "high"),
    # 주민등록번호 — 하이픈 주변 공백도 받는다(원본은 `900101 - 1234567` 을 놓쳤다)
    "ssn_kr": (re.compile(r"(?<!\d)\d{6}\s*-\s*[1-4]\d{6}(?!\d)|(?<!\d)\d{6}[1-4]\d{6}(?!\d)"), "high"),
    "ssn_us": (re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)"), "high"),
    # ⚠️ 선두 `01` 필수 + 숫자 경계. 원본 `0?1[016789]` 는 평범한 10자리 수를 전화번호로 잡았다
    "phone_kr": (re.compile(r"(?<![\d])(?:\+?82[-\s]?1[016789]|01[016789])[-\s]?\d{3,4}[-\s]?\d{4}(?!\d)"), "high"),
    # ⚠️ 구분자 필수. 구분자 없는 10자리는 전화번호라고 볼 근거가 없다
    "phone_us": (re.compile(r"(?<![\d])(?:\+?1[-\s])?\(?\d{3}\)?[-\s]\d{3}[-\s]\d{4}(?!\d)"), "high"),
    "credit_card": (re.compile(r"(?<!\d)\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}(?!\d)"), "high"),
    "ipv4": (re.compile(r"(?<![\d.])(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)(?![\d.])"), "medium"),
    "ipv6": (re.compile(r"(?<![:\w])(?:[A-Fa-f0-9]{1,4}:){2,7}[A-Fa-f0-9]{1,4}(?![:\w])"), "medium"),
}
DEFAULT_DATA_EXT = [".jsonl", ".json", ".csv", ".tsv", ".txt", ".md"]
DEFAULT_UNREADABLE_EXT = [".parquet", ".arrow", ".feather", ".pkl", ".npy", ".h5"]
MASK_RE = re.compile(r"\*{2,}|x{4,}|X{4,}|●{2,}|＊{2,}|<[A-Z_]{3,}>|\[redacted\]|…", re.IGNORECASE)


def load_policy(path: str, key: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get(key, {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get(key, {}) or {}


def mission_root(draft: str) -> str:
    p = os.path.abspath(draft)
    return p if os.path.isdir(p) else os.path.dirname(p)


def luhn_valid(s: str) -> bool:
    """⚠️ 매치된 문자열 자체로 판정한다 — 원본의 고정 창(`text[p:p+19]`)은 뒤따르는 문자를
    끌어들여 자릿수가 어긋나면 유효한 카드번호를 놓쳤다(실측)."""
    digits = [int(c) for c in s if c.isdigit()]
    if len(digits) != 16:
        return False
    total, parity = 0, (len(digits) - 2) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def scan_text(text: str, names: list[str]) -> list[tuple[str, str, str]]:
    """(패턴명, 심각도, 매치) 목록. 마스킹된 표기는 제외한다."""
    hits = []
    for name in names:
        pat = PATTERNS.get(name)
        if not pat:
            continue
        rx, sev = pat
        for m in rx.finditer(text):
            raw = m.group(0)
            if MASK_RE.search(raw):
                continue
            if name == "credit_card" and not luhn_valid(raw):
                continue
            hits.append((name, sev, raw))
    return hits


def strings_of(path: str) -> list[str]:
    """데이터 파일에서 문자열을 뽑는다(stdlib 만). 읽지 못하면 예외."""
    ext = os.path.splitext(path)[1].lower()
    raw = open(path, encoding="utf-8", errors="replace").read()
    if ext == ".jsonl":
        out = []
        for line in raw.splitlines():
            if line.strip():
                out.extend(walk_json(json.loads(line)))
        return out
    if ext == ".json":
        return walk_json(json.loads(raw))
    if ext in (".csv", ".tsv"):
        delim = "\t" if ext == ".tsv" else ","
        return [c for row in csv.reader(io.StringIO(raw), delimiter=delim) for c in row]
    return [raw]


def walk_json(obj) -> list[str]:
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        return [s for v in obj.values() for s in walk_json(v)]
    if isinstance(obj, list):
        return [s for v in obj for s in walk_json(v)]
    return []


def data_files(root: str, exts: list[str], unreadable: list[str]) -> tuple[list[str], list[str]]:
    """(읽을 수 있는 데이터 파일, 읽을 수 없는 데이터 파일)."""
    ok, bad = [], []
    for dirpath, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for n in sorted(names):
            e = os.path.splitext(n)[1].lower()
            p = os.path.join(dirpath, n)
            if e in exts:
                ok.append(p)
            elif e in unreadable:
                bad.append(p)
    return sorted(ok), sorted(bad)


def main() -> int:  # noqa: C901
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="미사용(gate_keeper 규약상 전달됨)")
    ap.add_argument("--draft", default=None, help="미션 디렉터리")
    args = ap.parse_args()

    if not args.draft:
        print("FAIL(usage): --draft 필수 — fail-closed", file=sys.stderr); return 2
    try:
        pii_pol = load_policy(args.policy, "pii_policy")
        pub_pol = load_policy(args.policy, "publication_policy")
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2

    root = mission_root(args.draft)
    names = pii_pol.get("patterns") or list(PATTERNS)
    fail_on = [str(s).lower() for s in (pii_pol.get("fail_on") or ["high"])]
    max_medium = pii_pol.get("max_medium")
    exts = [e.lower() for e in (pii_pol.get("data_extensions") or DEFAULT_DATA_EXT)]
    unreadable_ext = [e.lower() for e in (pii_pol.get("unreadable_extensions") or DEFAULT_UNREADABLE_EXT)]

    mode = str(pub_pol.get("mode", "local_only")).lower()
    priv = os.path.join(root, pub_pol.get("private_bundle") or os.path.join("_private", "bundle"))
    pub = os.path.join(root, pub_pol.get("public_bundle") or "bundle")

    if not os.path.isdir(priv):
        print(f"FAIL(usage): 정본 번들이 없다({priv}) — 배포물이 없는 것을 '개인정보 없음'으로 "
              f"읽으면 안 된다. fail-closed", file=sys.stderr)
        return 2

    fail = False
    targets = [("정본", priv)]
    print(f"공개 범위 mode={mode} · 검사 패턴 {len(names)}종 · FAIL 등급 {fail_on}")

    # ① 공개 범위: 선언과 실제 산출 위치가 맞는가
    if mode == "local_only":
        if os.path.isdir(pub):
            n_ok, n_bad = data_files(pub, exts, unreadable_ext)
            print(f"FAIL: `publication_mode: local_only` 인데 커밋 대상 `{os.path.relpath(pub, root)}/` 에 "
                  f"데이터 파일 {len(n_ok) + len(n_bad)}건이 있다 — 이 저장소는 PUBLIC 이고 "
                  f"Deliver 가 push 한다. 배포를 결정하지 않은 데이터가 공개된다")
            fail = True
        else:
            print(f"  ✓ 커밋 대상에 데이터 없음(정본은 `_private/` 에만)")
    elif mode == "repo_commit":
        if not os.path.isdir(pub):
            print(f"FAIL: `publication_mode: repo_commit` 인데 공개 번들 "
                  f"`{os.path.relpath(pub, root)}/` 이 없다 — 선언한 산출물이 없으면 검사할 것도 "
                  f"없어 통과한다(§5 '선언 목록 대비 존재')")
            fail = True
        else:
            targets.append(("공개", pub))
    else:
        print(f"FAIL(usage): 알 수 없는 publication mode {mode!r} "
              f"(local_only|repo_commit) — fail-closed", file=sys.stderr)
        return 2

    # ② 내용 검사 — **모든 포맷의 모든 파일**
    totals = {"high": 0, "medium": 0}
    for label, base in targets:
        files, unreadable = data_files(base, exts, unreadable_ext)
        rel = os.path.relpath(base, root)
        print(f"  [{label}] {rel}/ — 데이터 파일 {len(files)}건 검사"
              + (f" · 읽을 수 없는 파일 {len(unreadable)}건" if unreadable else ""))
        if not files and not unreadable:
            print(f"FAIL: {rel}/ 에 데이터 파일이 없다 — 빈 번들을 통과시키면 안 된다")
            fail = True
        if unreadable:
            print(f"FAIL: 읽을 수 없는 데이터 파일 {len(unreadable)}건 "
                  f"{[os.path.basename(p) for p in unreadable[:4]]} — **읽지 못한 것은 "
                  f"깨끗한 것이 아니다.** 원본은 parquet 첫 샤드 하나만 보고 통과시켰다. "
                  f"정본을 `.jsonl`/`.csv` 로 두거나 `pyarrow` 를 설치하라")
            fail = True
        for path in files:
            try:
                values = strings_of(path)
            except (OSError, ValueError, json.JSONDecodeError) as e:
                print(f"FAIL: {os.path.relpath(path, root)} 파싱 실패 ({e}) — 파싱 못한 파일을 "
                      f"건너뛰면 검사에서 빠진다")
                fail = True
                continue
            per_file: dict[str, int] = {}
            for v in values:
                for name, sev, _raw in scan_text(v, names):
                    per_file[name] = per_file.get(name, 0) + 1
                    totals[sev] = totals.get(sev, 0) + 1
            if per_file:
                sev_of = {n: PATTERNS[n][1] for n in per_file}
                bad = [n for n in per_file if sev_of[n] in fail_on]
                mark = "FAIL" if bad else "참고"
                print(f"  {mark}: {os.path.relpath(path, root)} — "
                      + ", ".join(f"{n}({sev_of[n]}) {c}건" for n, c in sorted(per_file.items())))
                if bad:
                    print(f"       → 개인정보가 배포물에 남았다. 마스킹(`<EMAIL>`·`***`)하거나 "
                          f"열을 제거하고 clean-log 에 기록하라")
                    fail = True

    # ③ medium 상한(기본 무제한 — IP 하나로 배포를 막지 않는다)
    if max_medium is not None and totals.get("medium", 0) > int(max_medium):
        print(f"FAIL: medium 등급 {totals['medium']}건 > 상한 {max_medium}")
        fail = True
    if totals.get("medium"):
        print(f"참고: medium 등급 {totals['medium']}건(IP 등). 기본 정책은 이것으로 막지 않는다 "
              f"— 데이터시트의 '민감 정보' 절에 밝혀라")

    if not fail:
        print(f"  ✓ 모든 포맷의 모든 데이터 파일에서 high 등급 개인정보 0건 · "
              f"공개 범위 선언과 산출 위치 일치")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
