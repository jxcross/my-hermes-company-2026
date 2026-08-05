#!/usr/bin/env python3
"""research-proposal(아키타입 Q) 게이트를 '일부러 깨뜨린 픽스처'로 검증한다 (docs/13 §5).

원본 proposalforge 에서 실측으로 확인한 결함에 **회귀 방어**를 건다:
  · 섹션 파일 5개가 **전부 비어도** `overall: PASS` (존재만 확인 · 분량 하한 없음)  → ②-1
  · gantt 블록이 ````mermaid\\ngantt\\n```` 한 줄이어도 "timeline_format PASS"      → ②-2
  · **Sum 열을 빼면** 예산 산술 검사가 통째로 사라진다("ok")                        → ③-1
  · **짧은 행**(열 부족)은 금액이 합계에서 증발한다(9억 누락 실측)                  → ③-2
  · **음수 조정 행**으로 연차 상한을 깎는다(연 3억 → 1.4억 보고)                    → ③-3
  · 키워드 나열 한 줄로 평가지표 5종 전건 통과(창의성 20/3 …)                       → ④-1
  · **미상 사업명이면 자격 검사가 꺼진다**(박사 30년차가 신진 사업에 PASS)          → ④-2
  · 대표논문을 **남의 인용 bibkey** 로 센다(리더 자격 충족)                          → ④-3
  · "Gantt 는 methods 활동과 1:1 매칭"은 CLAUDE.md 선언일 뿐 코드에 없다            → ⑤ 전체
"""
import json, os, shutil, subprocess, sys
import yaml

ROOT = "/work/company"
FIX = "/tmp/pfg"
GATES = os.path.join(ROOT, "scripts", "gates")
TOOLS = os.path.join(ROOT, "scripts", "tools")

CAP = 150_000_000
N_YEARS = 5
PAGE_LIMIT = 4          # 픽스처를 작게 유지한다(허용 2.0~4.0쪽 = 1200~2400 어절)
SENT = ("본 연구는 국내 산업 데이터를 대상으로 제안 기법의 실효성을 정량 지표로 검증한다 "
        "그리고 재현 가능한 절차를 문서로 남긴다 ")   # 24 어절

SOURCES = (
    [{"id": f"acad_{i}", "title": f"학술문헌 {i}", "published_year": 2023 + (i % 2),
      "source_type": "academic", "status": "selected"} for i in range(1, 8)]
    + [{"id": f"ntis_{i}", "title": f"수행과제 {i}", "published_year": 2022 + (i % 3),
        "source_type": "funded", "status": "selected"} for i in range(1, 5)]
    + [{"id": f"pat_{i}", "title": f"특허 {i}", "published_year": 2022 + i,
        "source_type": "patent", "status": "selected"} for i in range(1, 4)]
)
ALL_IDS = [s["id"] for s in SOURCES]
ACTS = [("a1", "s1", 1, "데이터 수집·정제 프로토콜 설계"),
        ("a2", "s1", 2, "검증 체계 구현"),
        ("a3", "s2", 3, "산업 현장 적용 실험"),
        ("a4", "s2", 4, "결과 일반화 및 배포")]


def w(rel, s):
    p = os.path.join(FIX, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(s)


def body(n_eojeol):
    """대략 n 어절짜리 국문 본문."""
    return (SENT * (n_eojeol // 24 + 1)) + "\n"


def build(program="신진연구자", years_post_phd=4, page_limit=PAGE_LIMIT,
          n_years=N_YEARS, mode="local_only"):
    shutil.rmtree(FIX, ignore_errors=True)
    os.makedirs(FIX)
    tpl = yaml.safe_load(open(os.path.join(ROOT, "templates", "research-proposal.yaml"),
                              encoding="utf-8"))
    pol = tpl["policy"]
    pol["publication_policy"]["mode"] = mode
    json.dump({"policy": pol}, open(os.path.join(FIX, "pipeline.json"), "w"),
              ensure_ascii=False)

    w("SCOPE.md", f"""---
nrf_program: {program}
page_limit: {page_limit}
budget_cap_per_year_krw: {CAP}
n_years: {n_years}
indirect_rate: 0.17
deadline: 2026-09-30
publication_mode: {mode}
---
# 미션 스펙
국내 산업 데이터 기반 검증 체계 연구를 {program} 사업에 신청한다.
""")
    w("raw/sources.yaml", yaml.safe_dump(SOURCES, allow_unicode=True))

    w("_private/context.md", f"""# PI 이력

career_years_post_phd: {years_post_phd}

소속·연락처는 제출 시 신청자가 직접 입력한다. 주민등록번호는 `000-00-00000` 로 둔다.

```representative
- bibkey: kim2024gnn
  title: 산업 데이터 검증 기법
  role: 제1저자
- bibkey: kim2023eval
  title: 평가 프로토콜 연구
  role: 교신저자
```

## 참고문헌(남의 논문 — 대표논문 아님)
- bibkey: other2021a
- bibkey: other2021b
- bibkey: other2022c
""")

    cites = " ".join(f"[{i}]" for i in ALL_IDS)
    w("_private/landscape.md", f"""# 지형 조사

학술·수행과제·특허 지형을 조사했다. 조사 대상 출처: {cites}

```gaps
- id: g1
  sources: [acad_1, ntis_1]
  statement: 제안 기법이 국내 산업 데이터에서 검증된 사례가 없다
- id: g2
  sources: [pat_1, acad_3]
  statement: 특허는 있으나 재현 가능한 평가 절차가 공개되지 않았다
```
""")

    acts_block = "\n".join(
        f"- id: {aid}\n  objective: {oid}\n  year: {yr}\n  title: {t}"
        for aid, oid, yr, t in ACTS)
    w("_private/outline.md", f"""# 제안 뼈대

최종목표: 국내 산업 데이터 기반 검증 체계 구축

```objectives
- id: s1
  gaps: [g1]
  statement: 국내 산업 데이터 기반 검증 체계를 구축한다
- id: s2
  gaps: [g2]
  statement: 재현 가능한 평가 절차를 공개한다
```

```activities
{acts_block}
```

```criteria
- id: 창의성
  section: aims
  evidence: 기존 계열은 공개 벤치마크에 그쳤다 본 연구는 국내 산업 데이터에 대한 검증 체계를 처음으로 제시한다
- id: 우수성
  section: background
  evidence: 선행 연구 대비 검증 대상 데이터의 규모와 다양성에서 앞서며 지형 조사로 그 차별을 근거한다
- id: 구체성
  section: methods
  evidence: 연차별 활동 a1 a2 a3 a4 마다 산출물과 정량 지표를 명시하고 측정 방법을 규정한다
- id: 추진전략
  section: methods
  evidence: 연차별로 설계 구현 적용 일반화의 순서를 두고 각 단계의 위험과 대안을 함께 제시한다
- id: 기대효과
  section: impact
  evidence: 산업 현장의 검증 비용을 줄이고 공개된 평가 절차로 후속 연구의 재현성을 높인다
```
""")

    w("_private/plan.md", """# 실행 계획

```resources
- id: r1
  kind: personnel
  item: 박사후연구원 1인 (FTE 1.0)
  year: 1
  rationale: a1·a2 의 데이터 처리 전담
- id: r2
  kind: equipment
  item: GPU 서버 1식
  year: 1
  rationale: a2 의 검증 체계 구현에 필요
```
""")

    # ── 예산: 산출 도구로 만든다(도구+게이트 E2E) ──────────────────────────
    spec = {"years": n_years, "indirect_rate": 0.17,
            "team": [{"role": "PI", "fte": 0.3, "months": 12},
                     {"role": "PostDoc", "fte": 1.0, "months": 12},
                     {"role": "PhDStudent", "fte": 1.0, "months": 12}],
            "equipment": [{"item": "GPU 서버", "year": 1, "cost_krw": 30_000_000}]}
    w("_private/budget-spec.json", json.dumps(spec, ensure_ascii=False))
    subprocess.run([sys.executable, os.path.join(TOOLS, "budget_build.py"),
                    "--input", os.path.join(FIX, "_private/budget-spec.json"),
                    "--md", os.path.join(FIX, "_private/bundle/budget.md"),
                    "--csv", os.path.join(FIX, "_private/bundle/budget.csv")],
                   capture_output=True, check=True)

    tasks = "\n".join(f"    {t} :{aid}, 2026-0{yr}-01, 90d" for aid, _o, yr, t in ACTS)
    w("_private/bundle/timeline.md", f"""# 연구 일정

```mermaid
gantt
    title 연구 일정
    dateFormat YYYY-MM-DD
    section 연차별 활동
{tasks}
```
""")

    # ── 절 5종 · 각 300 어절(총 1500 = 2.5쪽 · 허용 2.0~4.0) ────────────────
    secs = {}
    for name in ("aims", "background", "impact", "team"):
        secs[name] = f"# {name}\n\n{body(350)}"
    secs["methods"] = ("# methods\n\n연차별 활동은 a1 을 시작으로 a2 와 a3 의 순서로 두고 "
                       "마지막에 a4 로 일반화한다.\n\n" + body(340))
    for name, text in secs.items():
        w(f"_private/bundle/sections/{name}.md", text)
    w("_private/bundle/proposal.md",
      "# 연구개발계획서\n\n본 초안은 소속 기관 연구처 검토를 거쳐 신청자 본인이 제출한다.\n\n"
      + "\n".join(secs[k] for k in ("aims", "background", "methods", "impact", "team")))
    w("_private/bundle/abstract-en.md", "# Abstract\n\n" + (
        "This project builds a validation framework for domestic industrial data and "
        "publishes a reproducible evaluation procedure that others can follow. " * 8))
    w("_private/bundle/references.bib",
      "@article{kim2024gnn, title={Industrial data validation}, year={2024}}\n")

    w("report/summary.md", """# 제출 요약

대상 공고 마감은 2026-09-30 이며 번들은 `_private/bundle/` 에 있다.

⚠️ 이 산출물은 소속 기관 연구처 검토를 전제로 한 초안이며, 실제 제출은 신청자 본인이 수행한다.
예산 항목은 추정치로 회계·법률 자문이 아니다.
""")


def run(gate, draft, sources="raw/sources.yaml"):
    r = subprocess.run([sys.executable, os.path.join(GATES, f"{gate}.py"),
                        "--policy", os.path.join(FIX, "pipeline.json"),
                        "--sources", os.path.join(FIX, sources),
                        "--draft", os.path.join(FIX, draft)],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


DRAFTS = {"proposal_format": ".", "budget_integrity": ".", "call_alignment": ".",
          "proposal_traceability": ".", "legal_safety": ".",
          "source_balance": "_private/landscape.md", "recency_check": "_private/landscape.md"}


def expect(label, gate, want, show=False, draft=None):
    rc, out = run(gate, draft or DRAFTS[gate])
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
print("── ① 정상 픽스처: 7게이트 모두 PASS ──")
build()
results.append(expect("정상 · proposal_format", "proposal_format", 0, show=True))
results.append(expect("정상 · budget_integrity", "budget_integrity", 0, show=True))
results.append(expect("정상 · call_alignment(final)", "call_alignment", 0, show=True))
results.append(expect("정상 · proposal_traceability(final)", "proposal_traceability", 0, show=True))
results.append(expect("정상 · legal_safety(+공개범위)", "legal_safety", 0))
results.append(expect("정상 · source_balance(A·G 재사용)", "source_balance", 0))
results.append(expect("정상 · recency_check(A·G 재사용)", "recency_check", 0))

print("\n── ② proposal_format: 원본은 '빈 제안서' 를 통과시켰다 ──")
build()
for s in ("aims", "background", "methods", "impact", "team"):
    w(f"_private/bundle/sections/{s}.md", "---\nstage: section\n---\n")
results.append(expect("**원본 회귀: 절 5개가 전부 빈 파일**(원본 PASS)",
                      "proposal_format", 1, show=True))

build(); patch("_private/bundle/timeline.md",
               open(os.path.join(FIX, "_private/bundle/timeline.md"),
                    encoding="utf-8").read().split("```mermaid\n")[1].split("```")[0],
               "gantt\n")
results.append(expect("**원본 회귀: gantt 가 한 줄짜리 빈 도표**(원본 PASS)",
                      "proposal_format", 1, show=True))

build(); os.remove(os.path.join(FIX, "_private/bundle/sections/impact.md"))
results.append(expect("필수 절 하나가 없다(병렬 워커 사망)", "proposal_format", 1))

build(); w("_private/bundle/sections/team.md", "# team\n\n" + body(60))
results.append(expect("절 하나가 분량 하한 미만", "proposal_format", 1))

build()
for s in ("aims", "background", "methods", "impact", "team"):
    w(f"_private/bundle/sections/{s}.md", f"# {s}\n\n{body(900)}")
results.append(expect("페이지 한도 초과", "proposal_format", 1))

build(); w("_private/bundle/abstract-en.md", "# 초록\n\n" + body(200))
results.append(expect("**원본에 없던 검사: 영문 초록이 국문**", "proposal_format", 1, show=True))

build(); w("_private/bundle/abstract-en.md", "# Abstract\n\nToo short.\n")
results.append(expect("영문 초록 분량 미달", "proposal_format", 1))

build(); w("_private/bundle/proposal.md", "# 목차\n\n1. 연구목표\n2. 연구배경\n3. 연구방법\n")
results.append(expect("본문이 목차뿐(조립 누락)", "proposal_format", 1))

build(); os.remove(os.path.join(FIX, "_private/bundle/references.bib"))
results.append(expect("필수 산출물 references.bib 부재", "proposal_format", 1))

build()
os.rename(os.path.join(FIX, "_private/bundle/sections/aims.md"),
          os.path.join(FIX, "_private/bundle/sections/연구목표.md"))
results.append(expect("설계 방어: 국문 별칭 파일명(연구목표.md)은 정상", "proposal_format", 0))

build(); patch("SCOPE.md", f"page_limit: {PAGE_LIMIT}\n", "")
results.append(expect("page_limit 선언 없음 → fail-closed", "proposal_format", 2))

print("\n── ③ budget_integrity: 상한을 빠져나가는 세 가지 방법 ──")
build()
csvp = os.path.join(FIX, "_private/bundle/budget.csv")
lines = open(csvp, encoding="utf-8").read().splitlines()
open(csvp, "w", encoding="utf-8").write(
    "\n".join(",".join(r.split(",")[:-1]) for r in lines) + "\n")
results.append(expect("**원본 회귀: Sum 열을 빼면 산술 검사가 사라진다**",
                      "budget_integrity", 1, show=True))

build()
open(csvp, "a", encoding="utf-8").write("대형장비,900000000\n")
results.append(expect("**원본 회귀: 짧은 행의 9억이 증발한다**", "budget_integrity", 1, show=True))

build()
open(csvp, "a", encoding="utf-8").write(
    "조정," + ",".join(["-160000000"] * N_YEARS) + f",{-160000000 * N_YEARS}\n")
results.append(expect("**원본 회귀: 음수 조정 행으로 상한을 깎는다**",
                      "budget_integrity", 1, show=True))

build(); patch("_private/bundle/budget.csv", "인건비,66000000", "인건비,99000000")
results.append(expect("행 합계 불일치", "budget_integrity", 1))

build(); patch("SCOPE.md", f"budget_cap_per_year_krw: {CAP}",
               "budget_cap_per_year_krw: 100000000")
results.append(expect("연차 총계가 상한 초과", "budget_integrity", 1))

build(); patch("SCOPE.md", f"n_years: {N_YEARS}", "n_years: 3")
results.append(expect("연차 열 수 ≠ SCOPE 선언(분모 축소)", "budget_integrity", 1, show=True))

build(); patch("SCOPE.md", "indirect_rate: 0.17", "indirect_rate: 0.25")
results.append(expect("간접비율이 SCOPE 선언과 다르다", "budget_integrity", 1, show=True))

build(); patch("_private/bundle/budget.csv", "장비비,30000000", "장비비,삼천만원")
results.append(expect("비수치 셀(원본은 0 으로 읽었다)", "budget_integrity", 1))

build(); patch("_private/plan.md", "```resources", "```planned_resources")
results.append(expect("plan.md 의 resources 블록 부재", "budget_integrity", 1))

build(); patch("_private/bundle/budget.csv", "출장비,0", "출장비,7000000")
results.append(expect("계획에 없는 비목에 예산(근거 없는 예산)", "budget_integrity", 1, show=True))

build(); patch("_private/bundle/budget.csv", "장비비,30000000", "장비비,0")
results.append(expect("계획한 장비를 계상하지 않았다", "budget_integrity", 1, show=True))

build(); patch("SCOPE.md", f"n_years: {N_YEARS}\n", "")
results.append(expect("n_years 선언 없음 → fail-closed", "budget_integrity", 2))

print("\n── ④ call_alignment: 키워드 세기를 구조화 대응으로 바꿨다 ──")
build(); patch("_private/outline.md", "```criteria", "```keywords")
results.append(expect("**원본 회귀: 대응 선언이 없다**(원본은 키워드 빈도로 통과)",
                      "call_alignment", 1, show=True))

build(program="창의도전연구")
results.append(expect("**원본 회귀: 미상 사업명 → 자격 검사가 꺼졌다**",
                      "call_alignment", 1, show=True))

build(program="리더연구자", years_post_phd=12)
patch("_private/context.md", "```representative", "```other_refs")
results.append(expect("**원본 회귀: 대표논문을 남의 인용에서 셌다**",
                      "call_alignment", 1, show=True))

build(program="리더연구자", years_post_phd=12)
results.append(expect("리더 자격: 대표논문 2편 < 5편", "call_alignment", 1))

build(years_post_phd=9)
results.append(expect("신진 자격 초과(박사 후 9년 > 7년)", "call_alignment", 1, show=True))

build(); patch("_private/outline.md", "- id: 기대효과\n  section: impact\n", "- id: 미상지표\n  section: impact\n")
results.append(expect("평가지표 누락 + 공고에 없는 지표 선언", "call_alignment", 1))

build(); patch("_private/outline.md",
               "evidence: 기존 계열은 공개 벤치마크에 그쳤다 본 연구는 국내 산업 데이터에 대한 검증 체계를 처음으로 제시한다",
               "evidence: 창의적이다")
results.append(expect("근거 서술이 하한 미만", "call_alignment", 1))

build(); patch("_private/outline.md", "- id: 창의성\n  section: aims", "- id: 창의성\n  section: novelty")
results.append(expect("가리키는 절이 실재하지 않는다", "call_alignment", 1))

build(); w("_private/bundle/sections/aims.md", "# aims\n\n" + body(30))
results.append(expect("가리키는 절이 사실상 빈 절", "call_alignment", 1))

build(); patch("_private/context.md", "career_years_post_phd: 4\n", "")
results.append(expect("PI 경력 연수 선언 없음", "call_alignment", 1))

build(); shutil.rmtree(os.path.join(FIX, "_private/bundle/sections"))
results.append(expect("설계 방어: plan 모드(절이 아직 없다) → 선언만 검사",
                      "call_alignment", 0, show=True))

print("\n── ⑤ proposal_traceability: 원본이 '1:1 매칭' 이라 선언만 하던 것 ──")
build(); patch("_private/bundle/timeline.md", "    결과 일반화 및 배포 :a4, 2026-04-01, 90d\n", "")
results.append(expect("**원본 회귀: 활동 a4 가 일정표에 없다**(원본은 블록 존재만 확인)",
                      "proposal_traceability", 1, show=True))

build(); patch("_private/bundle/timeline.md", "    section 연차별 활동\n",
               "    section 연차별 활동\n    외부 자문 회의 :zz9, 2026-05-01, 30d\n")
results.append(expect("계획에 없는 일정 task(고아)", "proposal_traceability", 1, show=True))

build(); w("_private/bundle/sections/methods.md", "# methods\n\n" + body(300))
results.append(expect("방법 절이 활동을 서술하지 않는다", "proposal_traceability", 1, show=True))

build(); patch("_private/landscape.md", "sources: [acad_1, ntis_1]", "sources: [acad_99]")
results.append(expect("환각 인용(sources.yaml 에 없는 출처)", "proposal_traceability", 1, show=True))

build(); patch("_private/landscape.md", "  sources: [pat_1, acad_3]\n", "")
results.append(expect("공백에 조사 근거 인용이 없다", "proposal_traceability", 1))

build(); patch("_private/outline.md", "  gaps: [g2]\n", "")
results.append(expect("세부목표가 공백을 참조하지 않는다", "proposal_traceability", 1))

build(); patch("_private/outline.md", "  gaps: [g2]", "  gaps: [g9]")
results.append(expect("실재하지 않는 공백 참조 + 고아 공백", "proposal_traceability", 1))

build()
patch("_private/outline.md", "- id: s2\n  gaps: [g2]\n  statement: 재현 가능한 평가 절차를 공개한다\n", "")
results.append(expect("세부목표 1개(범위 밖) + 고아 활동", "proposal_traceability", 1, show=True))

build(); patch("_private/outline.md", "- id: a3\n  objective: s2", "- id: a3\n  objective: s9")
results.append(expect("실재하지 않는 목표를 참조하는 활동", "proposal_traceability", 1))

build(); patch("_private/outline.md", "- id: a4\n  objective: s2\n  year: 4", "- id: a4\n  objective: s2\n  year: 9")
results.append(expect("활동 연차가 연구기간 밖", "proposal_traceability", 1))

build(); os.remove(os.path.join(FIX, "_private/bundle/timeline.md"))
results.append(expect("설계 방어: plan 모드(일정표가 아직 없다)", "proposal_traceability", 0, show=True))

build()
w("_private/bundle/sections/methods.md",
  "# methods\n\n활동 a1 을 시작으로 a2 의 구현을 거쳐 a3 를 수행하고 a4 로 일반화한다.\n\n" + body(340))
results.append(expect("**한국어 조사 방어**: `a1 을`·`a2 의` 도 인식한다",
                      "proposal_traceability", 0))

print("\n── ⑥ legal_safety: 공개 범위 축(아키타입 Q 에서 열었다) ──")
build()
os.makedirs(os.path.join(FIX, "bundle"), exist_ok=True)
shutil.copy(os.path.join(FIX, "_private/bundle/proposal.md"),
            os.path.join(FIX, "bundle/proposal.md"))
results.append(expect("**local_only 인데 본문이 커밋 대상 위치에 있다**", "legal_safety", 1, show=True))

build(); os.remove(os.path.join(FIX, "_private/outline.md"))
results.append(expect("선언한 본문 산출물의 부재", "legal_safety", 1))

build(mode="repo_commit")
results.append(expect("repo_commit 인데 커밋 위치에 본문이 없다", "legal_safety", 1, show=True))

build(mode="publish_all")
results.append(expect("알 수 없는 공개 범위 mode → fail-closed 판정", "legal_safety", 1))

build(); patch("_private/context.md", "`000-00-00000`", "`860101-1234567`")
results.append(expect("PI 주민등록번호 평문", "legal_safety", 1, show=True))

build(); patch("report/summary.md", "소속 기관 연구처 검토를 전제로 한 초안이며, 실제 제출은 신청자 본인이 수행한다.\n예산 항목은 추정치로 회계·법률 자문이 아니다.", "제출 준비가 끝났다.")
results.append(expect("요약에 고지 문구가 없다", "legal_safety", 1))

build(); os.remove(os.path.join(FIX, "report/summary.md"))
results.append(expect("고지 대상 파일 자체가 없다(선언 목록 대비 존재)", "legal_safety", 1))

print("\n── ⑦ source_balance · recency_check 재사용(A·G) ──")
build()
w("raw/sources.yaml", yaml.safe_dump([s for s in SOURCES if s["source_type"] != "patent"],
                                     allow_unicode=True))
results.append(expect("특허 지형 0건(하한 2)", "source_balance", 1, show=True))

build()
w("raw/sources.yaml", yaml.safe_dump(
    [{**s, "published_year": 2009} for s in SOURCES], allow_unicode=True))
results.append(expect("전 출처가 15년 이상 지났다", "recency_check", 1))

n_ok = sum(1 for r in results if r)
print(f"\n{n_ok}/{len(results)} 통과")
sys.exit(0 if n_ok == len(results) else 1)
