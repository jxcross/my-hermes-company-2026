#!/usr/bin/env python3
r"""
객관 게이트: DOE 설계점 ↔ 실행 회계
====================================
설계한 실험점이 **전부 실행됐고**, 실패가 **조용히 사라지지 않았으며**, 출력 스키마가
run 마다 **일관**한지 LLM 없이 검사한다.
출처: simforge 의 Gate 3(output-completeness) — **스크립트가 없다**(LLM 크리틱뿐). 신설.

⚠️ **원본 CLAUDE.md 가 규약으로 적어 둔 셋을 코드로 옮겼다**(docs/13 §5 계열):
     · "Every design point in 03-doe.md MUST have a corresponding `runs/run-NN/outputs.json`"
     · "**No silent failures** (failed runs must be marked `failed` in the queue, not missing)"
     · "Output schema consistent across runs"
   판정자는 LLM 크리틱 하나이고 검사 코드는 없다. **설계점 20개 중 3개를 지우고 DOE 표에서도
   지우면** 아무도 모른다 — 파라미터 스윕에서 이것은 결과를 바꾼다(수렴하지 않은 구간을
   빼면 그래프가 예뻐진다).

⚠️ **`run_completeness`(아키타입 M)와 합치지 않았다.** 이름이 비슷하고 하는 일도 겹쳐
   보이지만 **선언의 모양이 다르다** — M 은 `시스템(역할) × seed` 행렬이고 여기는
   `DOE 설계점(파라미터 조합)` 목록이다. 하나로 합치면 미션마다 절반만 쓰이는 게이트가
   되고, 어느 도메인의 규칙인지 흐려진다(lecture-course 의 이름 충돌 교훈과 같은 계열).

⚠️ **DOE 표는 스스로를 선언하고 스스로를 만족시킨다** — 설계점을 표에서도 지우고 run 도
   지우면 회계는 **내부적으로 완벽히 일관**해진다(픽스처가 잡은 자체 결함). 파라미터 스윕에서
   이것은 결과를 바꾼다(수렴하지 않는 구간을 통째로 없애면 그래프가 예뻐진다).
   → `doe.md` 가 `n_design_points:` 를 **명시**하게 하고 블록 길이와 대조한다.
     code-docs 의 '분모 자기결정'을 한 단계 위에서 막는 것이다 — 분모를 고정하는 선언을
     따로 두면 나중에 조용히 줄일 수 없다.

⚠️ **실패를 벌하지 않는다.** 실패한 run 이 있는 것 자체는 정상이다(발산·비수렴은 결과다).
   막는 것은 **실패를 숨기는 것**이다 — `status: failed` 로 남기고 사유를 적으면 통과한다.
   기본 상한은 정책(`max_failed_ratio`)이고 0 이 아니다(secforge 에서 배운 것 — 게이트가
   발견을 벌하면 안 된다).

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.doe_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : 미션 디렉터리

기대 형식 (doe.md)
  n_design_points: 6            # 블록 길이와 대조된다(조용한 축소 방지)

  ```runs
  - id: run-01
    inputs: runs/run-01/inputs.json
    design_point: {mesh: 0.1, reynolds: 100}
    status: done
  ```

정책 필드(doe_policy)
  min_design_points (기본 4) · max_failed_ratio (기본 0.2)
  require_declared_count (기본 true) — `n_design_points:` 선언과 블록 길이 대조
  require_failure_reason (기본 true) · require_schema_consistency (기본 true)
  outputs_file (기본 outputs.json) · allowed_status (기본 [done, failed])

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
RUNS_BLOCK_RE = re.compile(r"```runs\s*\n(.*?)\n```", re.DOTALL)
RUN_ID_RE = re.compile(r"^\s*-\s*id:\s*(\S+)", re.MULTILINE)
FIELD_RE = re.compile(r"^\s+(\w+):\s*(.*)$")


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("doe_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("doe_policy", {}) or {}


def mission_root(draft: str) -> str:
    p = os.path.abspath(draft)
    return p if os.path.isdir(p) else os.path.dirname(p)


def declared_count(root: str) -> int | None:
    """doe.md 의 `n_design_points:` — 블록이 스스로 줄어드는 것을 막는 고정 분모."""
    for name in ("doe.md", "03-doe.md"):
        p = os.path.join(root, name)
        if os.path.isfile(p):
            m = re.search(r"^\s*n_design_points\s*:\s*(\d+)\s*$",
                          open(p, encoding="utf-8").read(), re.MULTILINE)
            return int(m.group(1)) if m else None
    return None


def parse_runs_block(root: str) -> list[dict] | None:
    for name in ("doe.md", "03-doe.md"):
        p = os.path.join(root, name)
        if not os.path.isfile(p):
            continue
        m = RUNS_BLOCK_RE.search(open(p, encoding="utf-8").read())
        if not m:
            return None
        block = m.group(1)
        starts = list(RUN_ID_RE.finditer(block))
        items = []
        for i, s in enumerate(starts):
            body = block[s.end():(starts[i + 1].start() if i + 1 < len(starts) else len(block))]
            it = {"id": s.group(1).strip()}
            for line in body.splitlines():
                mf = FIELD_RE.match(line)
                if mf:
                    it[mf.group(1)] = mf.group(2).strip()
            items.append(it)
        return items
    return None


def schema_of(path: str) -> frozenset | None:
    try:
        d = json.loads(open(path, encoding="utf-8").read())
    except (OSError, ValueError):
        return None
    return frozenset(d.keys()) if isinstance(d, dict) else frozenset()


def main() -> int:  # noqa: C901
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="미사용(gate_keeper 규약상 전달됨)")
    ap.add_argument("--draft", default=None, help="미션 디렉터리")
    args = ap.parse_args()

    if not args.draft:
        print("FAIL(usage): --draft 필수 — fail-closed", file=sys.stderr); return 2
    try:
        policy = load_policy(args.policy)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2

    root = mission_root(args.draft)
    points = parse_runs_block(root)
    if points is None:
        print(f"FAIL(usage): doe.md 의 ```runs``` 블록을 찾지 못했다({root}) — 무엇을 "
              f"돌리기로 했는지 모르면 다 돌았는지도 알 수 없다. fail-closed", file=sys.stderr)
        return 2

    min_points = int(policy.get("min_design_points", 4))
    max_failed = float(policy.get("max_failed_ratio", 0.2))
    need_reason = bool(policy.get("require_failure_reason", True))
    need_schema = bool(policy.get("require_schema_consistency", True))
    out_name = policy.get("outputs_file") or "outputs.json"
    allowed_status = [s.lower() for s in (policy.get("allowed_status") or ["done", "failed"])]

    fail = False
    ids = [p["id"] for p in points]
    print(f"DOE 설계점 {len(points)}건 (하한 {min_points}) · 출력 파일 {out_name}")

    if len(points) < min_points:
        print(f"FAIL: 설계점 {len(points)}건 < 하한 {min_points} — 파라미터 스윕이라 하기에 "
              f"표본이 없다(**빈 블록도 원본은 크리틱 서술로만 봤다**)")
        fail = True
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        print(f"FAIL: 중복 run id {dup}")
        fail = True

    # 선언한 설계점 수 ↔ 블록 길이 — 표가 스스로 줄어드는 것을 막는다
    if bool(policy.get("require_declared_count", True)):
        want = declared_count(root)
        if want is None:
            print(f"FAIL: doe.md 에 `n_design_points:` 선언이 없다 — 설계점을 표에서도 "
                  f"지우면 회계가 **내부적으로 일관**해져 아무도 모른다. 분모를 따로 고정하라")
            fail = True
        elif want != len(points):
            print(f"FAIL: `n_design_points: {want}` 인데 ```runs``` 블록은 {len(points)}건 "
                  f"— 설계점이 조용히 {'줄었다' if want > len(points) else '늘었다'}")
            fail = True

    runs_dir = os.path.join(root, "runs")
    actual = sorted(n for n in os.listdir(runs_dir)) if os.path.isdir(runs_dir) else []
    actual = [a for a in actual if os.path.isdir(os.path.join(runs_dir, a))]

    missing = [i for i in ids if i not in actual]
    undeclared = [a for a in actual if a not in ids]
    if missing:
        print(f"FAIL: 설계했지만 실행 디렉터리가 없는 run {missing[:8]} — **조용한 누락**. "
              f"실패했다면 `status: failed` 로 남겨라(파라미터 스윕에서 수렴하지 않은 구간을 "
              f"지우면 그래프만 예뻐진다)")
        fail = True
    if undeclared:
        print(f"FAIL: DOE 에 없는 run {undeclared[:8]} — 설계 밖의 실행은 결과 선택의 여지를 "
              f"만든다")
        fail = True

    n_failed = 0
    schemas: dict[frozenset, list[str]] = {}
    for p in points:
        rid = p["id"]
        st = str(p.get("status", "")).lower()
        rd = os.path.join(runs_dir, rid)
        if st not in allowed_status:
            print(f"FAIL: {rid} 의 `status: {st or '없음'}` 이 허용값 {allowed_status} 밖이다 "
                  f"— 끝나지 않은 실험을 결과로 쓸 수 없다")
            fail = True
            continue
        if st == "failed":
            n_failed += 1
            if need_reason and not str(p.get("failure_reason", "")).strip():
                print(f"FAIL: {rid} 가 실패인데 `failure_reason:` 이 없다 — 실패는 결과이지만 "
                      f"사유 없는 실패는 결과가 아니다")
                fail = True
            continue
        if rid in missing:
            continue
        outp = os.path.join(rd, out_name)
        if not os.path.isfile(outp):
            # outputs/ 아래도 본다
            alt = os.path.join(rd, "outputs", out_name)
            outp = alt if os.path.isfile(alt) else None
        if not outp:
            print(f"FAIL: {rid} 가 성공으로 표시됐는데 {out_name} 이 없다 — "
                  f"**성공한 척한 실패다**")
            fail = True
            continue
        s = schema_of(outp)
        if s is None:
            print(f"FAIL: {rid} 의 {out_name} 을 읽을 수 없다(JSON 아님)")
            fail = True
            continue
        schemas.setdefault(s, []).append(rid)

    n_done = len([p for p in points if str(p.get("status", "")).lower() == "done"])
    ratio = n_failed / len(points) if points else 0.0
    print(f"  성공 {n_done} · 실패 {n_failed} ({ratio:.0%}, 상한 {max_failed:.0%})")
    if ratio > max_failed:
        print(f"FAIL: 실패 비율 {ratio:.0%} > 상한 {max_failed:.0%} — 실험 설계나 솔버 설정을 "
              f"다시 보라(실패 자체를 벌하는 것이 아니라 결과를 신뢰할 수 없는 수준이다)")
        fail = True

    if need_schema and len(schemas) > 1:
        print(f"FAIL: 출력 스키마가 run 마다 다르다 — {len(schemas)}종")
        for s, rids in list(schemas.items())[:3]:
            print(f"       · {sorted(s)[:6]} ← {rids[:4]}")
        print(f"       → 키가 다른 출력을 한 표로 묶으면 빈칸이 0 으로 읽힌다")
        fail = True

    if not fail:
        print(f"  ✓ 설계점 {len(points)}건이 전부 회계됐고(성공 {n_done}·실패 {n_failed}) "
              f"출력 스키마가 일관하다")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
