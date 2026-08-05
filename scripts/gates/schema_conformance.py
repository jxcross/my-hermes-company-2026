#!/usr/bin/env python3
"""
객관 게이트: 스키마 적합성(선언 ↔ 실제 데이터)
==============================================
선언한 스키마가 **실제 산출 데이터와 맞는지**, 그리고 **모든 포맷이 같은 데이터인지**
LLM 없이 검사한다.
출처: datasetforge 의 `schema-consistency-check` critic — **스크립트가 없다**(LLM 크리틱뿐). 신설.

⚠️ **원본 CLAUDE.md 가 선언만 하고 아무도 검사하지 않는 규칙 3개를 코드로 옮겼다**
   (docs/13 §5 의 docstring-vs-코드 함정과 같은 계열):
     · "3 출력 format (HF / Parquet / CSV) 은 **동일 row count + 동일 schema**"
     · "04-schema 의 모든 column 은 02-ingest 의 **실제 column 에서 유래**"(환각 금지)
     · "02-ingest 의 stats / schema 는 실제 데이터 기반 — **환각 금지**"
   `schema-consistency-check` 는 이것을 "cross-validate 한다"고 서술하지만 실행 가능한
   검사는 어디에도 없다. 세 포맷의 행 수가 달라도, 스키마에만 있는 열이 있어도 통과한다.

⚠️ **행 수 대조가 이 아키타입의 사실성 검증이다.** 정제 로그가 "1,000행 중 12행 제거"라고
   적었는데 산출이 1,000행이면 정제가 반영되지 않은 것이고, 900행이면 조용히 88행이 더
   사라진 것이다. code-migration 의 '기준선 대비'와 같은 판단 — **선언한 수를 실제로 센다.**

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.schema_policy · policy.publication_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : 미션 디렉터리

기대 형식
  schema.json : {"n_rows": 1000, "columns": [{"name": "id", "dtype": "string",
                 "nullable": false, "description": "레코드 식별자"}, ...]}
                (JSON Schema draft 의 `properties` 형태도 받는다)
  clean-log.md: `rows_in: 1012` · `rows_out: 1000` 줄

정책 필드(schema_policy)
  require_description (기본 true) · min_description_chars (기본 5)
  placeholder_terms (기본 TBD·TODO·미정·N/A)
  require_row_match (기본 true) · allowed_dtypes (기본 자유)

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
DEFAULT_PLACEHOLDERS = ["TBD", "TODO", "미정", "N/A", "작성 예정", "FIXME", "lorem ipsum"]
READABLE = (".jsonl", ".csv", ".tsv")


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


def parse_schema(path: str) -> tuple[list[dict], int | None]:
    """(컬럼 목록, 선언 행 수). `columns` 형태와 JSON Schema `properties` 형태를 모두 받는다."""
    d = json.loads(open(path, encoding="utf-8").read())
    n_rows = d.get("n_rows")
    if isinstance(d.get("columns"), list):
        return [c for c in d["columns"] if isinstance(c, dict)], n_rows
    props = d.get("properties") or {}
    cols = []
    for name, spec in props.items():
        spec = spec if isinstance(spec, dict) else {}
        cols.append({"name": name, "dtype": spec.get("type"),
                     "description": spec.get("description")})
    return cols, n_rows


def read_shape(path: str) -> tuple[set[str], int]:
    """(컬럼 집합, 행 수). 읽지 못하면 예외."""
    ext = os.path.splitext(path)[1].lower()
    raw = open(path, encoding="utf-8", errors="replace").read()
    if ext == ".jsonl":
        cols: set[str] = set()
        n = 0
        for line in raw.splitlines():
            if not line.strip():
                continue
            obj = json.loads(line)
            if isinstance(obj, dict):
                cols |= set(obj.keys())
            n += 1
        return cols, n
    delim = "\t" if ext == ".tsv" else ","
    rows = list(csv.reader(io.StringIO(raw), delimiter=delim))
    rows = [r for r in rows if r and any(c.strip() for c in r)]
    if not rows:
        return set(), 0
    return set(h.strip() for h in rows[0]), len(rows) - 1


def int_field(text: str, key: str) -> int | None:
    m = re.search(rf"^\s*{re.escape(key)}\s*:\s*([\d,]+)\s*$", text, re.MULTILINE)
    return int(m.group(1).replace(",", "")) if m else None


def format_dirs(base: str) -> list[str]:
    """번들 아래 포맷 디렉터리(data/<format>/)."""
    data = os.path.join(base, "data")
    root = data if os.path.isdir(data) else base
    if not os.path.isdir(root):
        return []
    subs = [os.path.join(root, n) for n in sorted(os.listdir(root))
            if os.path.isdir(os.path.join(root, n))]
    return subs or [root]


def main() -> int:  # noqa: C901
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="미사용(gate_keeper 규약상 전달됨)")
    ap.add_argument("--draft", default=None, help="미션 디렉터리")
    args = ap.parse_args()

    if not args.draft:
        print("FAIL(usage): --draft 필수 — fail-closed", file=sys.stderr); return 2
    try:
        policy = load_policy(args.policy, "schema_policy")
        pub = load_policy(args.policy, "publication_policy")
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2

    root = mission_root(args.draft)
    schema_path = os.path.join(root, "schema.json")
    if not os.path.isfile(schema_path):
        print(f"FAIL(usage): schema.json 이 없다({schema_path}) — 선언이 없으면 대조할 것도 "
              f"없다. fail-closed", file=sys.stderr)
        return 2
    try:
        cols, declared_rows = parse_schema(schema_path)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"FAIL(usage): schema.json 파싱 실패 ({e}) — fail-closed", file=sys.stderr)
        return 2
    if not cols:
        print("FAIL(usage): schema.json 에 컬럼 선언이 없다 — fail-closed", file=sys.stderr)
        return 2

    require_desc = bool(policy.get("require_description", True))
    min_desc = int(policy.get("min_description_chars", 5))
    placeholders = policy.get("placeholder_terms") or DEFAULT_PLACEHOLDERS
    require_rows = bool(policy.get("require_row_match", True))

    bundle = os.path.join(root, pub.get("private_bundle") or os.path.join("_private", "bundle"))
    fmts = format_dirs(bundle)
    if not fmts:
        print(f"FAIL(usage): 번들에 포맷 디렉터리가 없다({bundle}) — fail-closed", file=sys.stderr)
        return 2

    fail = False
    names = [str(c.get("name", "")).strip() for c in cols]
    print(f"스키마 컬럼 {len(cols)}종 · 선언 행 수 {declared_rows} · 포맷 {len(fmts)}종")

    # ① 스키마 선언 자체의 충실도
    if any(not n for n in names):
        print("FAIL: 이름 없는 컬럼 선언이 있다")
        fail = True
    dup = sorted({n for n in names if n and names.count(n) > 1})
    if dup:
        print(f"FAIL: 중복 컬럼명 {dup}")
        fail = True
    if require_desc:
        thin = [c.get("name") for c in cols
                if len(str(c.get("description") or "").strip()) < min_desc]
        holder = [c.get("name") for c in cols
                  if any(t.lower() in str(c.get("description") or "").lower() for t in placeholders)]
        if thin:
            print(f"FAIL: 설명이 없거나 {min_desc}자 미만인 컬럼 {thin[:8]} — 열 이름만으로는 "
                  f"쓰는 쪽이 의미를 알 수 없다")
            fail = True
        if holder:
            print(f"FAIL: 설명이 플레이스홀더인 컬럼 {holder[:8]} ({placeholders[:3]}…)")
            fail = True

    # ② 환각 컬럼 — 스키마의 컬럼이 실제로 데이터에 있는가
    schema_set = {n for n in names if n}
    shapes = []
    for d in fmts:
        files = [os.path.join(d, n) for n in sorted(os.listdir(d))
                 if os.path.splitext(n)[1].lower() in READABLE]
        unreadable = [n for n in sorted(os.listdir(d))
                      if os.path.splitext(n)[1].lower() not in READABLE
                      and os.path.isfile(os.path.join(d, n))
                      and not n.lower().endswith((".md", ".json", ".txt"))]
        if not files:
            print(f"FAIL: {os.path.relpath(d, root)}/ 에 읽을 수 있는 데이터 파일이 없다"
                  + (f" (읽을 수 없는 파일 {unreadable[:3]}) — 검사할 수 없는 형식을 "
                     f"'맞다'고 볼 수 없다" if unreadable else ""))
            fail = True
            continue
        cset: set[str] = set()
        total = 0
        for f in files:
            try:
                c, n = read_shape(f)
            except (OSError, ValueError, json.JSONDecodeError) as e:
                print(f"FAIL: {os.path.relpath(f, root)} 파싱 실패 ({e})")
                fail = True
                continue
            cset |= c
            total += n
        shapes.append((os.path.basename(d), cset, total, len(files)))
        print(f"  {os.path.basename(d):10s} 파일 {len(files)}건 · 행 {total} · 컬럼 {len(cset)}종")

    if not shapes:
        print("VERDICT: FAIL")
        return 1

    for name, cset, total, _n in shapes:
        extra = sorted(schema_set - cset)
        missing = sorted(cset - schema_set)
        if extra:
            print(f"FAIL: {name} 에 없는 컬럼을 스키마가 선언했다 {extra[:8]} — **환각 컬럼**. "
                  f"원본은 '모든 column 은 실제 column 에서 유래'라고 선언만 했다")
            fail = True
        if missing:
            print(f"FAIL: {name} 에 있는데 스키마에 없는 컬럼 {missing[:8]} — 문서화되지 않은 "
                  f"열이 배포된다")
            fail = True

    # ③ 포맷 간 동일성 — 원본이 선언만 하던 규칙
    row_counts = {n: t for n, _c, t, _f in shapes}
    if len(set(row_counts.values())) > 1:
        print(f"FAIL: 포맷마다 행 수가 다르다 {row_counts} — **같은 데이터셋의 세 표현이 "
              f"아니다.** 원본은 이 대조를 크리틱 서술로만 두었다")
        fail = True
    col_sets = [frozenset(c) for _n, c, _t, _f in shapes]
    if len(set(col_sets)) > 1:
        print(f"FAIL: 포맷마다 컬럼 구성이 다르다 "
              f"{ {n: len(c) for n, c, _t, _f in shapes} }")
        fail = True

    # ④ 선언 행 수 ↔ 실제 · 정제 로그 대조
    actual = next(iter(row_counts.values()))
    if require_rows:
        if declared_rows is None:
            print("FAIL: schema.json 에 `n_rows` 선언이 없다 — 대조할 기준이 없다")
            fail = True
        elif int(declared_rows) != actual:
            print(f"FAIL: schema.n_rows={declared_rows} 인데 실제 {actual}행")
            fail = True
        log = os.path.join(root, "clean-log.md")
        if os.path.isfile(log):
            text = open(log, encoding="utf-8").read()
            rows_out = int_field(text, "rows_out")
            rows_in = int_field(text, "rows_in")
            if rows_out is None:
                print("FAIL: clean-log.md 에 `rows_out:` 선언이 없다 — 정제가 몇 행을 남겼는지 "
                      "밝히지 않으면 조용한 소실을 잡을 수 없다")
                fail = True
            elif rows_out != actual:
                print(f"FAIL: clean-log rows_out={rows_out} 인데 산출은 {actual}행 — 정제 이후 "
                      f"{abs(rows_out - actual)}행이 설명 없이 {'사라졌다' if rows_out > actual else '늘었다'}")
                fail = True
            elif rows_in is not None and rows_in < rows_out:
                print(f"FAIL: clean-log rows_in={rows_in} < rows_out={rows_out} — 정제가 행을 "
                      f"만들어 낼 수는 없다")
                fail = True
        else:
            print("FAIL: clean-log.md 가 없다 — 어떤 변환을 거쳤는지 기록 없이 배포할 수 없다")
            fail = True

    if not fail:
        print(f"  ✓ 스키마 {len(cols)}컬럼이 실제 데이터와 일치 · 포맷 {len(shapes)}종이 "
              f"동일 행수({actual})·동일 컬럼 · 정제 로그와 대조됨")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
