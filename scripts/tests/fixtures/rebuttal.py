#!/usr/bin/env python3
"""reviewer-response(아키타입 R) 게이트를 '일부러 깨뜨린 픽스처'로 검증한다 (docs/13 §5).

원본 rebuttalforge 에서 실측으로 확인한 결함에 **회귀 방어**를 건다:
  · 프론트매터만 있는 **빈 응답 파일**에 커버리지 PASS(파일 존재를 답변으로 셌다)   → ③-1
  · ```comments``` 블록이 비면 `expected comments: 0 · PASS`(공집합 아홉 번째)      → ③-2
  · 커버리지의 **분모를 파이프라인 자신이 만든다**(인자에 리뷰어 원문이 없다)       → ② 전체
  · 원고를 **한 글자도 고치지 않고 태그만** 붙여도 PASS(`--original` 인자가 없다)   → ④-1
  · 변경기록을 **마크다운 목록**으로 쓰면 0건으로 읽어 정상 산출물을 반려           → ④-2(정상)
  · 문서가 말하는 태그 형식 `[CHANGE-r1: …]` 을 따르면 게이트가 막는다              → ④-3(정상)
  · 크리틱 2종(tone·argument)은 **스크립트가 없다**                                 → ⑤ 전체
"""
import json, os, shutil, subprocess, sys
import yaml

ROOT = "/work/company"
FIX = "/tmp/rbf"
GATES = os.path.join(ROOT, "scripts", "gates")

# 리뷰어 원문 — 코멘트는 여기서 verbatim 으로 옮겨진다
REVIEW1 = """# Reviewer 1

1. The experiments are limited to a single public benchmark; validation on
   domestic industrial data is missing entirely.
2. Section 3.2 does not state how the random seed was fixed, so the numbers
   cannot be reproduced.
3. Minor: Table 2 caption has a typo.
"""
REVIEW2 = """# Reviewer 2

1. The claim that the method is the first of its kind is too strong given the
   prior work of Kim et al.
2. Please clarify whether the preprocessing step is applied at training time
   only or also at inference time.
"""
COMMENTS = [
    ("R1.1", "The experiments are limited to a single public benchmark; validation on "
             "domestic industrial data is missing entirely.", "major", "accept"),
    ("R1.2", "Section 3.2 does not state how the random seed was fixed, so the numbers "
             "cannot be reproduced.", "methodological", "accept"),
    ("R1.3", "Minor: Table 2 caption has a typo.", "minor", "accept"),
    ("R2.1", "The claim that the method is the first of its kind is too strong given the "
             "prior work of Kim et al.", "major", "rebut"),
    ("R2.2", "Please clarify whether the preprocessing step is applied at training time "
             "only or also at inference time.", "clarification", "clarification-only"),
]
ORIGINAL = """# 원고

## 3.1 서론
본 연구는 공개 벤치마크에서 제안 기법을 평가한다.

## 3.2 실험 설정
학습률과 배치 크기는 표 1에 정리했다.

## 3.3 결과
표 2에 주요 결과를 제시한다.

## 4 논의
제안 기법은 기존 계열과 다른 접근을 취한다.
"""


def w(rel, s):
    p = os.path.join(FIX, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(s)


def response(cid, verdict):
    """판정별 필수 요소를 갖춘 정상 응답."""
    common = ("말씀하신 지적에 감사드립니다. 저희는 이 부분이 원고의 설득력에 중요하다고 "
              "판단해 아래와 같이 처리했습니다. ")
    if verdict == "accept":
        return f"""---
comment_id: {cid}
verdict: accept
---
{common}지적하신 내용을 3.2절에 반영했습니다. 구체적으로 국내 산업 데이터에 대한
검증 실험을 추가하고 그 결과를 Table 2 아래에 새 문단으로 제시했습니다. 해당 변경은
3.2절과 Table 2 주변에서 확인하실 수 있습니다.

```changes
- action: replace
  section: 3.2
  old_text: 기존 문장
  new_text: 수정 문장
```
"""
    if verdict == "rebut":
        return f"""---
comment_id: {cid}
verdict: rebut
---
{common}다만 이 지적에 대해서는 저희가 달리 보는 근거가 있어 말씀드립니다.
Kim et al. 의 선행 연구는 공개 벤치마크만을 다루었고, 3.2절에 제시한 국내 데이터
설정과는 대상 모집단이 다릅니다. 또한 Table 2 의 수치는 해당 선행 연구가 보고한
0.812 와 직접 비교할 수 없는 조건에서 측정된 값입니다. 따라서 원 주장을 유지하되
범위를 명확히 하는 편이 정확하다고 판단했습니다.
"""
    return f"""---
comment_id: {cid}
verdict: clarification-only
---
{common}질문하신 전처리 단계는 학습 시점에만 적용됩니다. 추론 시점에는 동일한
변환을 적용하지 않으며, 그 이유는 배포 환경에서 입력 분포가 학습 분포와 다르기
때문입니다. 이 점은 원고의 서술을 바꾸지 않아도 이해에 지장이 없다고 보아 원고는
그대로 두었습니다. 필요하시면 각주로 명시하겠습니다.
"""


def build():
    shutil.rmtree(FIX, ignore_errors=True)
    os.makedirs(FIX)
    tpl = yaml.safe_load(open(os.path.join(ROOT, "templates", "reviewer-response.yaml"),
                              encoding="utf-8"))
    json.dump({"policy": tpl["policy"]}, open(os.path.join(FIX, "pipeline.json"), "w"),
              ensure_ascii=False)

    w("SCOPE.md", "---\njournal: J. Test\nmanuscript_no: TST-2026-001\n---\n# 리비전\n")
    w("_private/reviews/R1.md", REVIEW1)
    w("_private/reviews/R2.md", REVIEW2)

    block = "\n".join(f"- id: {cid}\n  category: {cat}" for cid, _t, cat, _v in COMMENTS)
    verbatim = "\n\n".join(f"## {cid}\n{txt}" for cid, txt, _c, _v in COMMENTS)
    w("_private/comments.md", f"""# 리뷰어 코멘트

n_comments: {len(COMMENTS)}
reviewers: [R1, R2]

```comments
{block}
```

{verbatim}
""")
    w("_private/categorized.md", "# 분류\nmajor 2 · minor 1 · methodological 1 · clarification 1\n")

    for cid, _t, _c, verdict in COMMENTS:
        w(f"_private/responses/{cid}.md", response(cid, verdict))

    w("_private/original-ms.md", ORIGINAL)
    w("_private/revised-ms.md", ORIGINAL
      .replace("본 연구는 공개 벤치마크에서 제안 기법을 평가한다.",
               "[CHANGE-R1.1: 국내 데이터 검증 추가] 본 연구는 공개 벤치마크와 국내 산업 "
               "데이터 양쪽에서 제안 기법을 평가한다.")
      .replace("학습률과 배치 크기는 표 1에 정리했다.",
               "[CHANGE-R1.2: seed 고정 명시] 학습률과 배치 크기는 표 1에 정리했으며 "
               "난수 seed 는 42로 고정했다.")
      .replace("표 2에 주요 결과를 제시한다.",
               "[CHANGE-R1.3: 표 2 캡션 오타 수정] 표 2에 주요 결과를 제시한다(캡션 수정)."))
    w("_private/change-log.md", """# 변경기록

- R1.1: 3.1절에 국내 산업 데이터 검증 실험을 추가했다
- R1.2: 3.2절에 난수 seed 고정을 명시했다
- R1.3: 표 2 캡션의 오타를 수정했다
""")

    # 커버레터 250~500 어절
    para = ("이번 개정에서는 리뷰어 두 분이 지적하신 사항을 코멘트 단위로 검토하고 "
            "수용한 지적을 원고에 반영했습니다. 주요 변경은 국내 산업 데이터에 대한 "
            "검증 실험의 추가와 실험 설정의 재현 정보 보완입니다. ")
    w("_private/cover-letter.md", "# 커버레터\n\n편집자님께\n\n" + para * 22 +
      "\n\n감사합니다.\n")

    w("report/summary.md", """# 리비전 요약

코멘트 5건에 전건 응답했고 3건을 원고에 반영했다.

⚠️ 리뷰어 코멘트는 대외비이며 번들은 `_private/` 에만 있다.
최종 확인과 실제 제출은 저자가 수행한다(저자 검토 후 제출).
""")


def run(gate, draft="."):
    r = subprocess.run([sys.executable, os.path.join(GATES, f"{gate}.py"),
                        "--policy", os.path.join(FIX, "pipeline.json"),
                        "--sources", os.path.join(FIX, "raw", "sources.yaml"),
                        "--draft", os.path.join(FIX, draft)],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def expect(label, gate, want, show=False, draft="."):
    rc, out = run(gate, draft)
    print(f"{'OK ' if rc == want else '‼️ '}{label:62s} exit={rc} (기대 {want})")
    if rc != want or show:
        print("      " + "\n      ".join(out.splitlines()[-8:]))
    return rc == want


def patch(path, old, new, count=1):
    p = os.path.join(FIX, path)
    t = open(p, encoding="utf-8").read()
    assert old in t, f"픽스처 치환 실패: {old!r} not in {path}"
    open(p, "w", encoding="utf-8").write(t.replace(old, new, count))


results = []
print("── ① 정상 픽스처: 5게이트 모두 PASS ──")
build()
results.append(expect("정상 · comment_fidelity", "comment_fidelity", 0, show=True))
results.append(expect("정상 · comment_coverage", "comment_coverage", 0, show=True))
results.append(expect("정상 · change_consistency", "change_consistency", 0, show=True))
results.append(expect("정상 · response_quality", "response_quality", 0, show=True))
results.append(expect("정상 · legal_safety(Q 의 공개범위 축 재사용)", "legal_safety", 0))

print("\n── ② comment_fidelity: 원본에 이 검사가 통째로 없다 ──")
build(); patch("_private/comments.md",
               "- id: R2.2\n  category: clarification", "")
patch("_private/comments.md", f"n_comments: {len(COMMENTS)}", f"n_comments: {len(COMMENTS) - 1}")
os.remove(os.path.join(FIX, "_private/responses/R2.2.md"))
results.append(expect("**원본 회귀: 지적을 빠뜨려도 커버리지는 100%**", "comment_fidelity", 1, show=True))
results.append(expect("        (같은 픽스처에서 coverage 는 통과한다 — 짝 게이트)",
                      "comment_coverage", 0))

build(); patch("_private/comments.md",
               "The experiments are limited to a single public benchmark",
               "실험을 더 하라고 하셨다(요약해 옮김)")
results.append(expect("**인용을 요약해 옮겼다(원문에 없는 말)**", "comment_fidelity", 1, show=True))

build(); patch("_private/comments.md", "## R1.3\nMinor: Table 2 caption has a typo.", "## R1.3\n")
results.append(expect("인용 절이 비었다", "comment_fidelity", 1))

build(); patch("_private/comments.md", f"n_comments: {len(COMMENTS)}", "n_comments: 9")
results.append(expect("선언 개수 ≠ 블록 길이(분모 축소)", "comment_fidelity", 1))

build(); patch("_private/comments.md", f"n_comments: {len(COMMENTS)}\n", "")
results.append(expect("`n_comments:` 선언이 없다", "comment_fidelity", 1))

build(); patch("_private/comments.md", "reviewers: [R1, R2]", "reviewers: [R1, R2, R3]")
results.append(expect("선언한 리뷰어 R3 의 코멘트가 하나도 없다", "comment_fidelity", 1, show=True))

build(); patch("_private/comments.md", "- id: R1.1", "- id: 1")
results.append(expect("id 형식 위반(원본은 경고만 했다)", "comment_fidelity", 1))

build(); shutil.rmtree(os.path.join(FIX, "_private/reviews"))
results.append(expect("리뷰어 원문이 없다 → fail-closed", "comment_fidelity", 2))

print("\n── ③ comment_coverage: 파일의 존재를 답변으로 셌다 ──")
build()
for cid, _t, _c, _v in COMMENTS:
    w(f"_private/responses/{cid}.md", f"---\ncomment_id: {cid}\nverdict: accept\n---\n")
results.append(expect("**원본 회귀: 빈 응답 파일 5건에 커버리지 PASS**",
                      "comment_coverage", 1, show=True))

build()
w("_private/comments.md", "n_comments: 0\nreviewers: [R1]\n\n```comments\n\n```\n")
shutil.rmtree(os.path.join(FIX, "_private/responses")); os.makedirs(os.path.join(FIX, "_private/responses"))
results.append(expect("**원본 회귀: 코멘트 0건이면 커버리지 100%**", "comment_coverage", 1, show=True))

build(); os.remove(os.path.join(FIX, "_private/responses/R1.2.md"))
results.append(expect("응답이 없는 코멘트", "comment_coverage", 1))

build(); w("_private/responses/R9.9.md", response("R9.9", "accept"))
results.append(expect("코멘트에 없는 응답(orphan)", "comment_coverage", 1))

build(); w("_private/responses/dup.md", response("R1.1", "accept"))
results.append(expect("같은 코멘트에 응답 둘(duplicate)", "comment_coverage", 1))

build(); w("_private/responses/notes.md", "# 메모\n응답이 아닌 파일이다.\n")
results.append(expect("comment_id 를 알 수 없는 파일(untagged)", "comment_coverage", 1))

print("\n── ④ change_consistency: '바꿨다'가 태그 문자열이었다 ──")
build(); w("_private/revised-ms.md", ORIGINAL
           .replace("본 연구는 공개 벤치마크에서 제안 기법을 평가한다.",
                    "[CHANGE-R1.1: 국내 데이터 검증 추가] 본 연구는 공개 벤치마크에서 제안 기법을 평가한다.")
           .replace("학습률과 배치 크기는 표 1에 정리했다.",
                    "[CHANGE-R1.2: seed 고정 명시] 학습률과 배치 크기는 표 1에 정리했다.")
           .replace("표 2에 주요 결과를 제시한다.",
                    "[CHANGE-R1.3: 캡션 수정] 표 2에 주요 결과를 제시한다."))
results.append(expect("**원본 회귀: 태그만 붙이고 원고는 그대로**",
                      "change_consistency", 1, show=True))

build(); patch("_private/change-log.md", "- R1.1:", "R1.1:")
patch("_private/change-log.md", "- R1.2:", "R1.2:")
patch("_private/change-log.md", "- R1.3:", "R1.3:")
results.append(expect("**원본 회귀(정상): 콜론형 변경기록도 인식한다**", "change_consistency", 0))

build()   # 정상 픽스처는 목록형이다 — 원본은 이것을 0건으로 읽어 반려했다
results.append(expect("**원본 회귀(정상): 목록형 변경기록을 반려하지 않는다**",
                      "change_consistency", 0))

build(); patch("_private/responses/R1.1.md", "verdict: accept", "verdict: rebut")
results.append(expect("반박이라 해 놓고 원고를 고쳤다", "change_consistency", 1, show=True))

build(); patch("_private/change-log.md", "- R1.2: 3.2절에 난수 seed 고정을 명시했다\n", "")
results.append(expect("수용인데 변경기록에 항목이 없다", "change_consistency", 1))

build(); patch("_private/revised-ms.md", "[CHANGE-R1.3: 표 2 캡션 오타 수정] ", "")
results.append(expect("수용인데 원고에 변경 표시가 없다", "change_consistency", 1))

build(); patch("_private/change-log.md", "- R1.3:", "- R7.7:")
results.append(expect("변경기록에만 있는 id(소급 불가한 변경)", "change_consistency", 1))

build(); patch("_private/responses/R2.1.md", "verdict: rebut", "verdict: maybe")
results.append(expect("허용값 밖의 판정", "change_consistency", 1))

build(); patch("_private/responses/R2.1.md", "verdict: rebut\n", "")
results.append(expect("판정 자체가 없다", "change_consistency", 1))

build(); os.remove(os.path.join(FIX, "_private/original-ms.md"))
results.append(expect("원본 원고가 없다(대조 불가)", "change_consistency", 1, show=True))

build(); shutil.rmtree(os.path.join(FIX, "_private/responses")); os.makedirs(os.path.join(FIX, "_private/responses"))
results.append(expect("응답 0건 → fail-closed", "change_consistency", 2))

print("\n── ⑤ response_quality: 원본 크리틱 2종은 스크립트가 없다 ──")
build(); patch("_private/responses/R2.1.md", "다만 이 지적에 대해서는 저희가 달리 보는 근거가 있어 말씀드립니다.",
               "리뷰어가 오해하신 것 같습니다.")
results.append(expect("**금지 표현('리뷰어가 오해')**", "response_quality", 1, show=True))

build()
w("_private/responses/R2.1.md", """---
comment_id: R2.1
verdict: rebut
---
말씀하신 지적에 감사드립니다. 저희는 이 주장이 여전히 타당하다고 생각하며 원고의
표현을 유지하는 편이 정확하다고 판단했습니다. 선행 연구와 저희 연구는 다루는 대상과
전제가 다르고, 그 차이가 주장의 범위를 가른다고 보기 때문입니다. 따라서 원고를
수정하지 않았습니다. 앞으로도 이 입장을 유지하려 하며, 추가로 설명드릴 부분이 있으면
언제든 알려 주시기 바랍니다. 검토해 주셔서 감사합니다.
""")
results.append(expect("**반박인데 근거 인용이 없다**(원본 규칙: 자동 HIGH)",
                      "response_quality", 1, show=True))

build(); patch("_private/responses/R1.1.md",
               "지적하신 내용을 3.2절에 반영했습니다. 구체적으로 국내 산업 데이터에 대한\n검증 실험을 추가하고 그 결과를 Table 2 아래에 새 문단으로 제시했습니다. 해당 변경은\n3.2절과 Table 2 주변에서 확인하실 수 있습니다.",
               "수정했습니다. 지적해 주신 대로 원고에 반영했으며 앞으로도 같은 기준을 "
               "유지하겠습니다. 검토해 주셔서 감사드리며 추가로 확인이 필요한 부분이 "
               "있으면 언제든 말씀해 주시기 바랍니다. 저희는 이번 개정으로 지적하신 "
               "우려가 해소되었다고 생각합니다.")
results.append(expect("수용인데 원고의 **어디에** 반영됐는지 안 가리킨다",
                      "response_quality", 1, show=True))

build(); patch("_private/responses/R1.1.md",
               "```changes\n- action: replace\n  section: 3.2\n  old_text: 기존 문장\n  new_text: 수정 문장\n```\n", "")
results.append(expect("수용인데 changes 블록에 액션이 없다", "response_quality", 1))

build()
w("_private/responses/R2.2.md", """---
comment_id: R2.2
verdict: clarification-only
---
학습 시점에만 적용됩니다.
""")
results.append(expect("설명 답변이 한 문장(질문 감사합니다 류)", "response_quality", 1))

build(); patch("_private/cover-letter.md", "편집자님께", "편집자님께\n\n리뷰어가 틀렸다고 봅니다.")
results.append(expect("커버레터의 금지 표현(편집자가 먼저 읽는다)", "response_quality", 1))

build(); patch("_private/cover-letter.md", "# 커버레터", "# 커버레터\n\n짧게 줄인다.")
w("_private/cover-letter.md", "# 커버레터\n\n편집자님께 짧게 인사드립니다.\n")
results.append(expect("커버레터 분량 규격 밖", "response_quality", 1))

build(); os.remove(os.path.join(FIX, "_private/cover-letter.md"))
results.append(expect("커버레터가 없다", "response_quality", 1))

build()
patch("_private/responses/R1.2.md", "verdict: accept", "verdict: partially-accept")
results.append(expect("부분수용인데 제안과의 차이 설명이 없다", "response_quality", 1, show=True))

print("\n── ⑥ legal_safety: 공개 범위(아키타입 Q 에서 연 축) ──")
build(); shutil.copytree(os.path.join(FIX, "_private/responses"), os.path.join(FIX, "responses"))
results.append(expect("**local_only 인데 응답이 커밋 대상 위치에 있다**", "legal_safety", 1, show=True))

build(); shutil.copy(os.path.join(FIX, "_private/original-ms.md"),
                     os.path.join(FIX, "original-ms.md"))
results.append(expect("심사 중 원고가 커밋 대상 위치에 있다", "legal_safety", 1))

build(); patch("report/summary.md",
               "최종 확인과 실제 제출은 저자가 수행한다(저자 검토 후 제출).", "끝.")
patch("report/summary.md", "⚠️ 리뷰어 코멘트는 대외비이며 번들은 `_private/` 에만 있다.", "")
results.append(expect("요약에 고지 문구가 없다", "legal_safety", 1))

n_ok = sum(1 for r in results if r)
print(f"\n{n_ok}/{len(results)} 통과")
sys.exit(0 if n_ok == len(results) else 1)
