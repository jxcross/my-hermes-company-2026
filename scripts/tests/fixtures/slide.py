#!/usr/bin/env python3
"""conference-slides(아키타입 T) 게이트를 '일부러 깨뜨린 픽스처'로 검증한다 (docs/13 §5).

원본 slideforge 에서 실측으로 확인한 결함에 **회귀 방어**를 건다:
  · 20분 발표에 슬라이드 2장이 PASS(상한만 잰다)                                → ②-1
  · 분모를 산출물이 정한다 — `min_per_slide: 0.1` 이면 15분에 60장이 PASS       → ②-2
  · `--notes` 가 죽은 인자 — 존재하지 않는 경로를 줘도 PASS                     → ②-3
  · 노트 플레이스홀더 필터가 완전 일치라 `TBD.` 와 `작성 예정` 이 통과          → ②-4,5
  · .mmd 가 하나도 없으면 PASS(공집합 열한 번째)                                → ④-1
  · 괄호 균형을 파일 총계로 세어 `A[입력) --> B(인코더]` 가 PASS                → ④-2
  · 슬라이드 규율(불릿 5개·1 figure)을 지시로만 적어 두고 검사하지 않는다       → ③-1
"""
import json, os, shutil, subprocess, sys
import yaml

ROOT = "/work/company"
FIX = "/tmp/sfg"
GATES = os.path.join(ROOT, "scripts", "gates")

LAUNCH = "2026-09-15"
TALK = 15

# (id, section, title, time_min, 본문)
PLAN = [
    (1, "intro", "연구 배경", 0.8,
     "- 산업 현장 데이터는 공개 벤치마크와 분포가 다르다\n"
     "- 그래서 기존 평가가 그대로 통하지 않는다\n"),
    (2, "intro", "무엇을 했나", 1.0,
     "- 국내 산업 데이터에 대한 검증 체계를 만들었다 [e2]\n"
     "- 절차를 공개해 다른 팀이 따라 할 수 있게 했다 [e2]\n"),
    (3, "method", "데이터 구성", 1.2,
     "- 세 기관에서 수집한 로그를 같은 스키마로 정규화했다\n"
     "- 개인정보 항목은 수집 단계에서 제외했다\n"),
    (4, "method", "평가 절차", 1.5,
     "- 동일 조건에서 반복 측정했다 [e2]\n"
     "- 측정마다 환경 지문을 남겼다\n"),
    (5, "method", "제안 구조", 1.5,
     "{{mermaid:d1}}\n\n- 입력에서 판정까지의 경로를 단순화했다 [e2]\n"),
    (6, "result", "평가 지표", 1.5,
     "- 정확도와 지연을 함께 본다\n- 두 지표는 서로 맞바꿔진다\n"),
    (7, "result", "정확도 비교", 1.5,
     "![정확도 비교 막대그림](../source/figures/fig2.png)\n\n"
     "- 국내 산업 데이터에서 정확도 0.873 을 얻었다 [e1]\n"),
    (8, "result", "질의 흐름", 1.5,
     "{{mermaid:d2}}\n\n- 질의와 응답의 순서를 그대로 옮겼다 [e2]\n"),
    (9, "result", "3.2배 빠른 추론", 1.5,
     "- 동일 정확도에서 처리 속도가 개선됐다 [e3]\n"
     "- 배치 크기를 키워도 경향이 유지됐다 [e3]\n"),
    (10, "discussion", "한계", 1.2,
     "- 표본이 한 기관에 치우쳐 있다 [e5]. 예비 결과이며 추가 검증이 필요하다\n"),
    (11, "discussion", "적용 가능성", 1.0,
     "- 같은 절차를 다른 도메인에 옮길 수 있다\n- 다만 스키마 정규화는 도메인마다 다르다\n"),
    (12, "closing", "요약", 0.8,
     "- 현장 데이터로 검증 체계를 만들었다\n- 절차와 자료를 공개한다\n"),
]

NOTE = {
    1: "이 장에서는 배경을 짧게 말하고 바로 문제로 넘어간다 청중의 관심을 먼저 잡는다",
    2: "무엇을 만들었는지 한 문장으로 말하고 자세한 것은 뒤에서 다룬다고 예고한다",
    3: "데이터의 출처를 밝히고 왜 이 구성이 필요했는지 한 마디로 덧붙인다",
    4: "절차를 설명하되 세부 수치는 말하지 않고 다음 장의 그림으로 넘어간다",
    5: "그림을 따라가며 입력에서 판정까지 손으로 짚어 준다 여기서 천천히 말한다",
    6: "지표 두 개가 왜 함께 필요한지 설명하고 다음 장의 비교로 이어 간다",
    7: "이 숫자가 오늘 발표의 핵심이다 잠시 멈추고 청중이 그림을 보게 둔다",
    8: "질의 흐름을 순서대로 읽어 주고 병목이 어디였는지 한 마디 덧붙인다",
    9: "속도 개선이 어디서 왔는지 한 문장으로 말하고 과장하지 않는다",
    10: "한계를 먼저 말하는 편이 질문을 줄인다 정직하게 표본 문제를 인정한다",
    11: "적용 가능성을 말하되 확언하지 않는다 조건을 함께 말한다",
    12: "요약을 세 문장으로 마치고 공개 위치를 알려 준 뒤 질문을 받는다",
}

SOURCE_MD = """# 발표 주장

```evidence
- id: e1
  kind: claim
  grade: verified
  value: 0.873
  locator: _private/source/results.md
  statement: 국내 산업 데이터에서 정확도 0.873 을 얻었다
- id: e2
  kind: claim
  grade: verified
  locator: _private/source/results.md
  statement: 검증 절차를 공개했다
- id: e3
  kind: claim
  grade: verified
  value: 3.2
  locator: _private/source/results.md
  statement: 기존 대비 3.2배 빠르다
- id: e4
  kind: figure
  grade: verified
  locator: _private/source/figures/fig2.png
  statement: 정확도 비교 막대그림
- id: e5
  kind: claim
  grade: preliminary
  locator: _private/source/results.md
  statement: 표본이 한 기관에 치우쳐 있다
```
"""

MMD1 = """flowchart LR
    A[입력] --> B[인코더]
    B --> C{판정}
    C -->|yes| D[출력 A]
    C -->|no| E[출력 B]
"""

MMD2 = """sequenceDiagram
    participant U as 사용자
    participant S as 시스템
    U->>S: 질의
    S-->>U: 응답
"""

CHECKLIST = f"""# 발표 체크리스트

- T-7일: 리허설 1회 (시간 측정)
- T-1일: 백업 PDF 준비 · 어댑터 확인
- T-0 ({LAUNCH}): 발표

⚠️ 이 파이프라인은 발표하지 않는다. 사람이 최종 확인 후 직접 발표한다.
슬라이드 공개는 발표 종료 후 저장소 릴리스에 붙인다.
"""


def w(rel, s):
    p = os.path.join(FIX, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(s)


def slide_text(sid, section, title, body, note=None):
    return (f"---\nslide_number: {sid}\nsection: {section}\ntitle: {title}\n---\n\n"
            f"## {title}\n\n{body}\n<!-- speaker:\n{note or NOTE[sid]}\n-->\n")


def outline_text(plan, n_diagrams=2, extra_fm=""):
    slides = "".join(
        f"- id: {sid}\n  section: {sec}\n  title: {title}\n  time_min: {t}\n"
        for sid, sec, title, t, _b in plan)
    diagrams = ""
    if n_diagrams >= 1:
        diagrams += "- id: d1\n  type: flowchart\n  used_in_slide: 5\n  source_basis: [e2, e4]\n"
    if n_diagrams >= 2:
        diagrams += ("- id: d2\n  type: sequenceDiagram\n  used_in_slide: 8\n"
                     "  source_basis: [e2]\n")
    return (f"---\nn_slides: {len(plan)}\nn_diagrams: {n_diagrams}\n{extra_fm}---\n\n"
            f"# 발표 구성\n\n```slides\n{slides}```\n\n```diagrams\n{diagrams}```\n")


def notes_text(plan):
    out = ["# 발표자 노트\n"]
    for sid, _sec, title, t, _b in plan:
        out.append(f"## Slide {sid}: {title}\n- **시간**: {t}분\n- **할 말**: {NOTE[sid]}\n"
                   f"- **전환**: 다음 장으로 자연스럽게 넘어간다\n")
    out.append("## 예상 질문과 답변 골자\n- 표본 편향에 대한 질문 · 후속 수집 계획을 답한다\n")
    return "\n".join(out)


def build(plan=None, talk=TALK, n_diagrams=2, patent="none", embargo="", basis="arxiv",
          ref="2601.01234", launch=LAUNCH, mode="local_only", scope_extra="", bundle=False):
    plan = plan or PLAN
    shutil.rmtree(FIX, ignore_errors=True)
    os.makedirs(FIX)
    tpl = yaml.safe_load(open(os.path.join(ROOT, "templates", "conference-slides.yaml"),
                              encoding="utf-8"))
    pol = tpl["policy"]
    pol["publication_policy"]["mode"] = mode
    json.dump({"policy": pol}, open(os.path.join(FIX, "pipeline.json"), "w"),
              ensure_ascii=False)

    w("SCOPE.md", f"""---
talk_time_minutes: {talk}
sections: [intro, method, result, discussion, closing]
audience: 학회-전문가
venue: 국내 학회
emphasis: balanced
release_basis: {basis}
release_ref: {ref}
patent_status: {patent}
launch_date: {launch}
embargo_until: {embargo}
{scope_extra}---
# 발표 스펙
""")
    w("_private/source/results.md",
      "# 결과\n정확도 0.873 (baseline 0.812).\n처리 속도는 baseline 대비 3.2배 빨랐다.\n"
      "검증 절차는 reproduce.sh 로 공개한다.\n표본은 한 기관 비중이 높다.\n")
    w("_private/source/figures/fig2.png", "(binary placeholder)")
    w("_private/source.md", SOURCE_MD)
    w("_private/outline.md", outline_text(plan, n_diagrams))
    for sid, sec, title, _t, body in plan:
        w(f"_private/slides/slide-{sid:02d}.md", slide_text(sid, sec, title, body))
    w("_private/notes.md", notes_text(plan))
    if n_diagrams >= 1:
        w("_private/mermaid/diagram-1.mmd", MMD1)
        w("_private/mermaid/diagram-1.mmd.meta.yml",
          "diagram_id: d1\ntype: flowchart\nused_in_slide: 5\nsource_basis: [e2, e4]\n")
    if n_diagrams >= 2:
        w("_private/mermaid/diagram-2.mmd", MMD2)
        w("_private/mermaid/diagram-2.mmd.meta.yml",
          "diagram_id: d2\ntype: sequenceDiagram\nused_in_slide: 8\nsource_basis: [e2]\n")
    w("_private/visuals.md", """# 그림 권리

```visuals
- id: v1
  slide: 7
  description: 정확도 비교 막대그림
  source: _private/source/figures/fig2.png
  license: own
```
""")
    w("_private/cite-pack.md", "# 인용팩\ne1 → slide 7\ne3 → slide 9\ne2 → slide 2·4·5·8\n")
    w("_private/talk-checklist.md", CHECKLIST)
    w("report/summary.md", "# 발표 자료 요약\n슬라이드 12장을 만들었고 발표는 사람이 한다.\n")
    if bundle:
        assemble()


def assemble(mermaid=True, files=("slides.md", "speaker-notes.md", "handout.md")):
    """Deliver 가 하는 번들 조립(marp_export 와 같은 동작)."""
    plan = PLAN
    chunks = []
    mmap = {"d1": MMD1.rstrip(), "d2": MMD2.rstrip()}
    for sid, sec, title, _t, body in plan:
        text = f"## {title}\n\n{body}"
        for did, mm in mmap.items():
            token = "{{mermaid:%s}}" % did
            text = text.replace(token, f"```mermaid\n{mm}\n```" if mermaid
                                else f"<!-- missing mermaid: {did} -->")
        chunks.append(text.rstrip())
    if "slides.md" in files:
        w("_private/slide-bundle/slides.md",
          "---\nmarp: true\ntheme: default\npaginate: true\n---\n\n"
          + "\n\n---\n\n".join(chunks) + "\n")
    if "speaker-notes.md" in files:
        w("_private/slide-bundle/speaker-notes.md",
          "\n".join(f"## Slide {sid}: {title}\n{NOTE[sid]}\n"
                    for sid, _s, title, _t, _b in plan))
    if "handout.md" in files:
        w("_private/slide-bundle/handout.md", "# 발표 요약 (1쪽)\n\n"
          + ("현장 데이터로 검증 체계를 만들고 절차를 공개했다. " * 30) + "\n")
    w("_private/slide-bundle/mermaid/diagram-1.mmd", MMD1)


def run(gate, draft="."):
    r = subprocess.run([sys.executable, os.path.join(GATES, f"{gate}.py"),
                        "--policy", os.path.join(FIX, "pipeline.json"),
                        "--sources", os.path.join(FIX, "raw", "sources.yaml"),
                        "--draft", os.path.join(FIX, draft)],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


# ⚠️ **템플릿이 선언한 draft 를 그대로 쓴다.** 한 stage 의 객관 게이트는 `--draft` 를 하나만
#    공유하므로, 하네스가 게이트마다 편한 draft 를 골라 주면 실미션에서만 깨지는 조합을
#    영영 발견하지 못한다(아키타입 S 에서 실제로 그랬다 · docs/13 §5).
DRAFTS = {                       # 값 = conference-slides.yaml 의 stages[].gate.draft
    "claim_provenance": ".",             # stage 3·10
    "slide_budget": "_private/slides",   # stage 11(stage 5 는 ".")
    "deck_format": "_private/slides",    # stage 11
    "evidence_grade": "_private/slides",  # stage 11
    "content_accessibility": "_private/slides",  # stage 11
    "diagram_integrity": ".",            # stage 10
    "release_readiness": ".",            # stage 13
}


def expect(label, gate, want, show=False, draft=None):
    rc, out = run(gate, draft or DRAFTS[gate])
    print(f"{'OK ' if rc == want else '‼️ '}{label:64s} exit={rc} (기대 {want})")
    if rc != want or show:
        print("      " + "\n      ".join(out.splitlines()[-8:]))
    return rc == want


def patch(path, old, new, count=1):
    p = os.path.join(FIX, path)
    t = open(p, encoding="utf-8").read()
    assert old in t, f"픽스처 치환 실패: {old!r} not in {path}"
    open(p, "w", encoding="utf-8").write(t.replace(old, new, count))


def set_policy(section, key, value):
    p = os.path.join(FIX, "pipeline.json")
    d = json.load(open(p))
    d["policy"][section][key] = value
    json.dump(d, open(p, "w"), ensure_ascii=False)


results = []
print("── ① 정상 픽스처: 게이트 7종 모두 PASS ──")
build()
results.append(expect("정상 · slide_budget(final)", "slide_budget", 0, show=True))
results.append(expect("정상 · deck_format(deck)", "deck_format", 0, show=True))
results.append(expect("정상 · diagram_integrity", "diagram_integrity", 0, show=True))
results.append(expect("정상 · claim_provenance(full · file scope)", "claim_provenance", 0, show=True))
results.append(expect("정상 · evidence_grade(G 재사용)", "evidence_grade", 0))
results.append(expect("정상 · content_accessibility(J 재사용)", "content_accessibility", 0))
results.append(expect("정상 · release_readiness(S 재사용)", "release_readiness", 0, show=True))

build(bundle=True)
results.append(expect("정상 · deck_format(bundle 모드)", "deck_format", 0, show=True))

build(); shutil.rmtree(os.path.join(FIX, "_private/slides"))
results.append(expect("설계 방어: plan 모드(집필 전 설계 검증 · stage 5)",
                      "slide_budget", 0, show=True, draft="."))

print("\n── ② slide_budget: 상한만 재고 분모를 산출물이 정하던 하드게이트 ──")
short = [PLAN[0], PLAN[11]]
short = [(1, "intro", "연구 배경", 10.0, PLAN[0][4]), (2, "closing", "요약", 10.0, PLAN[11][4])]
build(plan=short, talk=20, n_diagrams=0)
results.append(expect("**원본 회귀: 20분 발표에 슬라이드 2장**", "slide_budget", 1, show=True))

build(scope_extra="min_per_slide: 0.1\n")
patch("_private/outline.md", "n_slides: 12", "n_slides: 12\nmin_per_slide: 0.1")
results.append(expect("**원본 회귀: 산출물이 `min_per_slide: 0.1` 이라 적어도 정책이 이긴다**",
                      "slide_budget", 0, show=True))

build(); os.remove(os.path.join(FIX, "_private/notes.md"))
results.append(expect("**원본 회귀: 통합 노트가 없다(죽은 `--notes` 인자)**",
                      "slide_budget", 1, show=True))

build(); patch("_private/slides/slide-03.md", NOTE[3], "TBD.")
results.append(expect("**원본 회귀: 노트가 `TBD.`(마침표 하나)**", "slide_budget", 1, show=True))

build(); patch("_private/slides/slide-03.md", NOTE[3], "작성 예정")
results.append(expect("**원본 회귀: 노트가 '작성 예정'(국문 플레이스홀더)**", "slide_budget", 1))

build()
for n in (3, 4, 5):
    os.remove(os.path.join(FIX, f"_private/slides/slide-{n:02d}.md"))
results.append(expect("섹션 워커 하나가 죽어 method 슬라이드가 통째로 없다",
                      "slide_budget", 1, show=True))

build(); w("_private/slides/slide-13.md", slide_text(13, "closing", "덤", "- 덤 슬라이드다\n",
                                                     NOTE[12]))
results.append(expect("목차에 없는 슬라이드 파일이 있다(승인 범위 밖)", "slide_budget", 1))

build(); patch("_private/outline.md", "n_slides: 12\n", "")
results.append(expect("목차에 `n_slides:` 선언이 없다(분모 미고정)", "slide_budget", 1, show=True))

build(); patch("_private/outline.md", "n_slides: 12", "n_slides: 14")
results.append(expect("`n_slides` 선언과 블록 길이가 다르다", "slide_budget", 1))

build(); patch("_private/outline.md", "  time_min: 1.5\n", "  time_min: 4.0\n", 6)
results.append(expect("시간 배분 합계가 발표 시간과 어긋난다", "slide_budget", 1, show=True))

build(); patch("_private/outline.md", "  time_min: 1.2\n", "", 1)
results.append(expect("`time_min` 이 없는 슬라이드가 있다", "slide_budget", 1))

build(); patch("_private/outline.md", "  section: discussion\n", "  section: 잡담\n", 1)
results.append(expect("선언 밖 section", "slide_budget", 1))

build(); patch("_private/outline.md", "  section: closing\n", "  section: result\n", 1)
patch("_private/slides/slide-12.md", "section: closing", "section: result")
results.append(expect("선언한 섹션 하나가 목차에서 사라졌다", "slide_budget", 1, show=True))

build(); patch("_private/slides/slide-06.md", "section: result", "section: method")
results.append(expect("슬라이드 파일의 section 이 목차 선언과 다르다", "slide_budget", 1))

build(); patch("_private/notes.md", "## Slide 7:", "## Slide 77:")
results.append(expect("통합 노트의 슬라이드 항목이 어긋난다", "slide_budget", 1, show=True))

build(); patch("_private/slides/slide-05.md", NOTE[5], "짧다")
results.append(expect("노트가 어절 하한 미달", "slide_budget", 1))

build(); patch("SCOPE.md", f"talk_time_minutes: {TALK}\n", "")
results.append(expect("SCOPE 에 발표 시간 선언이 없다 → fail-closed", "slide_budget", 2))

build(); os.remove(os.path.join(FIX, "_private/outline.md"))
results.append(expect("목차가 없다 → fail-closed", "slide_budget", 2))

print("\n── ③ deck_format: 지시로만 있고 검사되지 않던 슬라이드 규율 ──")
build(); patch("_private/slides/slide-01.md",
               "- 산업 현장 데이터는 공개 벤치마크와 분포가 다르다\n",
               "".join(f"- 불릿 {i} 을 넣는다\n" for i in range(1, 9)))
results.append(expect("**원본 회귀: 불릿 8개(정보 과적재)**", "deck_format", 1, show=True))

build(); patch("_private/slides/slide-07.md",
               "- 국내 산업 데이터에서 정확도 0.873 을 얻었다 [e1]\n",
               "- 국내 산업 데이터에서 정확도 0.873 을 얻었다 [e1]\n- 둘\n- 셋\n- 넷\n")
results.append(expect("시각자료가 있는 장에 불릿 4개", "deck_format", 1, show=True))

build(); patch("_private/slides/slide-07.md", "![정확도 비교 막대그림](../source/figures/fig2.png)",
               "![정확도 비교 막대그림](../source/figures/fig2.png)\n\n{{mermaid:d1}}")
results.append(expect("한 장에 시각자료 2개", "deck_format", 1))

build(); patch("_private/slides/slide-02.md", "## 무엇을 했나\n\n", "")
results.append(expect("본문에 제목이 없다(frontmatter title 은 안 보인다)", "deck_format", 1, show=True))

build(); patch("_private/slides/slide-02.md", "---\nslide_number: 2\nsection: intro\ntitle: 무엇을 했나\n---\n\n", "")
results.append(expect("frontmatter 가 없다", "deck_format", 1))

build(); patch("_private/slides/slide-04.md", "slide_number: 4", "slide_number: 40")
results.append(expect("slide_number 가 파일명과 다르다(병합 순서가 어긋난다)", "deck_format", 1))

build(); patch("_private/slides/slide-04.md", "section: method\n", "")
results.append(expect("필수 필드(section) 누락", "deck_format", 1))

build(); patch("_private/slides/slide-11.md",
               "- 같은 절차를 다른 도메인에 옮길 수 있다\n- 다만 스키마 정규화는 도메인마다 다르다\n",
               "")
results.append(expect("제목만 있고 본문이 비었다(**상한만 재면 가장 안전한 슬라이드**)",
                      "deck_format", 1, show=True))

build(); patch("_private/slides/slide-11.md", "- 같은 절차를 다른 도메인에 옮길 수 있다\n",
               "- " + "같은 절차를 다른 도메인으로 옮길 수 있으나 스키마 정규화가 다르다 " * 6 + "\n")
results.append(expect("본문 어절 상한 초과(슬라이드가 문서가 됐다)", "deck_format", 1))

build(); shutil.rmtree(os.path.join(FIX, "_private/slides"))
results.append(expect("슬라이드가 하나도 없다 → fail-closed", "deck_format", 2))

print("\n── ③' deck_format(bundle): 조용히 남는 미치환 placeholder ──")
build(); assemble(mermaid=False)
results.append(expect("**번들에 `<!-- missing mermaid -->` 주석이 남았다(빈 슬라이드가 뜬다)**",
                      "deck_format", 1, show=True))

build(bundle=True); patch("_private/slide-bundle/slides.md", "```mermaid\nflowchart LR",
                          "{{mermaid:d1}}\n```mermaid\nflowchart LR")
results.append(expect("번들에 미치환 `{{mermaid:d1}}` 이 남았다", "deck_format", 1))

build(bundle=True); os.remove(os.path.join(FIX, "_private/slide-bundle/handout.md"))
results.append(expect("번들에 handout.md 가 없다", "deck_format", 1))

build(bundle=True); w("_private/slide-bundle/handout.md", "# 발표 요약\n한 줄이다.\n")
results.append(expect("handout 이 어절 하한 미달(배포할 것이 없다)", "deck_format", 1, show=True))

build(bundle=True); patch("_private/slide-bundle/slides.md", "marp: true", "marp: false")
results.append(expect("slides.md 에 `marp: true` 가 없다", "deck_format", 1))

build(bundle=True); patch("_private/slide-bundle/slides.md", "theme: default\n", "")
results.append(expect("slides.md 에 theme 선언이 없다", "deck_format", 1))

build(bundle=True); patch("_private/slide-bundle/slides.md", "\n\n---\n\n## 요약", "\n\n## 요약")
results.append(expect("병합에서 슬라이드 조각이 하나 사라졌다", "deck_format", 1, show=True))

build(bundle=True); patch("_private/slide-bundle/speaker-notes.md", "## Slide 9:", "## Slide 99:")
results.append(expect("번들 발표자 노트의 항목이 어긋난다", "deck_format", 1))

print("\n── ④ diagram_integrity: 파일이 없으면 PASS 이던 mermaid 검사 ──")
build(); shutil.rmtree(os.path.join(FIX, "_private/mermaid"))
results.append(expect("**원본 회귀: 선언 2개인데 .mmd 가 하나도 없다**",
                      "diagram_integrity", 1, show=True))

build(); w("_private/mermaid/diagram-1.mmd", "flowchart LR\n    A[입력) --> B(인코더]\n")
results.append(expect("**원본 회귀: 괄호 총계는 맞고 짝은 틀리다**", "diagram_integrity", 1, show=True))

build(); patch("_private/outline.md", "n_diagrams: 2\n", "")
results.append(expect("목차에 `n_diagrams:` 선언이 없다", "diagram_integrity", 1, show=True))

build(); patch("_private/outline.md", "n_diagrams: 2", "n_diagrams: 3")
results.append(expect("`n_diagrams` 선언과 블록 길이가 다르다", "diagram_integrity", 1))

build(); os.remove(os.path.join(FIX, "_private/mermaid/diagram-1.mmd.meta.yml"))
results.append(expect("사이드카(.meta.yml)가 없다", "diagram_integrity", 1))

build(); patch("_private/mermaid/diagram-1.mmd.meta.yml", "type: flowchart", "type: erDiagram")
results.append(expect("사이드카의 type 이 실제 다이어그램과 다르다", "diagram_integrity", 1, show=True))

build(); patch("_private/mermaid/diagram-1.mmd.meta.yml", "source_basis: [e2, e4]", "source_basis:")
results.append(expect("`source_basis` 가 비었다(무엇을 근거로 그렸는지 없다)",
                      "diagram_integrity", 1))

build(); patch("_private/mermaid/diagram-1.mmd.meta.yml", "source_basis: [e2, e4]",
               "source_basis: [e2, e99]")
results.append(expect("`source_basis` 가 원자료에 없는 id 를 가리킨다(환각 근거)",
                      "diagram_integrity", 1, show=True))

build(); w("_private/mermaid/diagram-1.mmd", "flowchart LR\n" + "".join(
    f"    N{i}[노드{i}] --> N{i + 1}[노드{i + 1}]\n" for i in range(1, 12)))
results.append(expect("노드 12개 > 상한 8(슬라이드에서 읽히지 않는다)", "diagram_integrity", 1, show=True))

build(); w("_private/mermaid/diagram-1.mmd", "flowchartt LR\n    A[입력] --> B[출력]\n")
results.append(expect("알 수 없는 다이어그램 타입", "diagram_integrity", 1))

build(); w("_private/mermaid/diagram-1.mmd", "flowchart LR\n")
results.append(expect("타입 선언만 있고 본문이 없다", "diagram_integrity", 1))

build(); patch("_private/slides/slide-05.md", "{{mermaid:d1}}", "{{mermaid:d7}}")
results.append(expect("슬라이드가 선언되지 않은 다이어그램을 참조한다", "diagram_integrity", 1, show=True))

build(); patch("_private/slides/slide-08.md", "{{mermaid:d2}}\n\n", "")
results.append(expect("만들어 놓고 아무 슬라이드도 쓰지 않는다(고아)", "diagram_integrity", 1))

build(); patch("_private/mermaid/diagram-2.mmd.meta.yml", "used_in_slide: 8", "used_in_slide: 6")
results.append(expect("`used_in_slide` 선언이 실제 참조 슬라이드와 다르다", "diagram_integrity", 1))

build(); w("_private/mermaid/diagram-9.mmd", MMD2)
results.append(expect("목차에 없는 다이어그램 파일이 있다", "diagram_integrity", 1))

build(n_diagrams=0)
patch("_private/slides/slide-05.md", "{{mermaid:d1}}\n\n", "")
patch("_private/slides/slide-08.md", "{{mermaid:d2}}\n\n", "")
results.append(expect("설계 방어: 다이어그램 0개를 명시 선언했다", "diagram_integrity", 0, show=True))

build(); w("_private/mermaid/diagram-2.mmd",
           "erDiagram\n    CUSTOMER ||--o{ ORDER : places\n    ORDER ||--|{ LINE : has\n")
patch("_private/mermaid/diagram-2.mmd.meta.yml", "type: sequenceDiagram", "type: erDiagram")
results.append(expect("설계 방어: erDiagram 카디널리티(`||--o{`)를 괄호로 오독하지 않는다",
                      "diagram_integrity", 0, show=True))

print("\n── ⑤ claim_provenance 재사용(S): 슬라이드는 파일 하나가 한 화면이다 ──")
build(); set_policy("claim_policy", "citation_scope", "paragraph")
results.append(expect("**축을 연 이유: 문단 단위면 제목의 수치가 반려된다**",
                      "claim_provenance", 1, show=True))

build(); patch("_private/slides/slide-07.md", "정확도 0.873 을 얻었다 [e1]", "정확도 0.873 을 얻었다")
results.append(expect("슬라이드의 수치에 claim 인용이 없다", "claim_provenance", 1))

build(); patch("_private/slides/slide-07.md", "정확도 0.873 을 얻었다 [e1]",
               "정확도 0.941 을 얻었다 [e1]")
results.append(expect("인용한 claim 의 값과 슬라이드의 수치가 다르다", "claim_provenance", 1, show=True))

build(); patch("_private/slides/slide-09.md", "[e3]", "[e9]", 1)
results.append(expect("존재하지 않는 claim 인용(환각)", "claim_provenance", 1))

build(); shutil.rmtree(os.path.join(FIX, "_private/slides"))
results.append(expect("설계 방어: source 모드(집필 전 stage 3)", "claim_provenance", 0, show=True))

print("\n── ⑥ evidence_grade 재사용(G): 예비 결과를 확정처럼 말하는 것 ──")
build(); patch("_private/slides/slide-10.md",
               "- 표본이 한 기관에 치우쳐 있다 [e5]. 예비 결과이며 추가 검증이 필요하다\n",
               "- 표본 편향은 없다 [e5]\n")
results.append(expect("**예비 등급 claim 인용에 유보 표현이 없다**", "evidence_grade", 1, show=True))

build(); patch("_private/slides/slide-02.md", "[e2]", "[e9]", 1)
results.append(expect("근거 목록에 없는 id 인용", "evidence_grade", 1))

print("\n── ⑦ content_accessibility 재사용(J): 원래 강의 슬라이드용 게이트다 ──")
build(); patch("_private/slides/slide-07.md", "![정확도 비교 막대그림](", "![](")
results.append(expect("**그림에 대체 텍스트가 없다**", "content_accessibility", 1, show=True))

print("\n── ⑧ release_readiness 재사용(S): 학회 발표도 공개다 ──")
build(patent="planned")
results.append(expect("**출원 예정 발명 — 발표하면 신규성을 잃는다(아키타입 F 와 충돌)**",
                      "release_readiness", 1, show=True))

build(embargo="2026-10-01")
results.append(expect("엠바고 해제일이 발표일보다 늦다", "release_readiness", 1, show=True))

build(basis="")
results.append(expect("공개 근거 선언이 없다", "release_readiness", 1))

build(basis="owner_approval", ref="sam-2026-08", mode="repo_commit")
results.append(expect("미공개 자료인데 커밋 범위가 repo_commit", "release_readiness", 1, show=True))

build(mode="repo_commit")
results.append(expect("설계 방어: arXiv 공개 자료면 repo_commit 허용", "release_readiness", 0))

build(); patch("_private/slides/slide-12.md", "- 절차와 자료를 공개한다\n", "- 공개 위치는 TBD\n")
results.append(expect("슬라이드에 플레이스홀더가 남았다", "release_readiness", 1, show=True))

build(); patch("_private/visuals.md", "  license: own\n", "")
results.append(expect("그림에 라이선스 표기가 없다(남의 그림 무단 사용)", "release_readiness", 1))

build(); patch("_private/talk-checklist.md",
               "⚠️ 이 파이프라인은 발표하지 않는다. 사람이 최종 확인 후 직접 발표한다.\n", "")
results.append(expect("체크리스트에 '우리는 발표하지 않는다' 고지가 없다", "release_readiness", 1))

build(); patch("_private/talk-checklist.md", f"T-0 ({LAUNCH})", "T-0 (발표일)")
results.append(expect("체크리스트에 발표일이 없다", "release_readiness", 1))

build(); os.remove(os.path.join(FIX, "_private/talk-checklist.md"))
results.append(expect("발표 체크리스트가 없다", "release_readiness", 1))

n_ok = sum(1 for r in results if r)
print(f"\n{n_ok}/{len(results)} 통과")
sys.exit(0 if n_ok == len(results) else 1)
