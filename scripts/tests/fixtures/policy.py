#!/usr/bin/env python3
"""policy-brief 3게이트를 '일부러 깨뜨린 픽스처'로 검증한다 (docs/13 §5).
PASS 만 보면 아무것도 측정하지 않는 게이트를 발견할 수 없다."""
import json, os, shutil, subprocess, sys
import yaml

ROOT = "/work/company"
FIX = "/tmp/pf"
GATES = os.path.join(ROOT, "scripts", "gates")


def filler(n):
    """n 어절의 무해한 국문 채움말(근거 id·옵션 토큰이 섞이지 않게)."""
    base = ["본", "정책은", "국내", "산업", "현장의", "안전", "수준을", "높이기", "위한",
            "제도적", "장치로서", "관계", "부처의", "협조가", "필요하다."]
    return " ".join(base[i % len(base)] for i in range(n))


def build():
    shutil.rmtree(FIX, ignore_errors=True)
    os.makedirs(os.path.join(FIX, "formats"))

    tpl = yaml.safe_load(open(os.path.join(ROOT, "templates", "policy-brief.yaml"), encoding="utf-8"))
    json.dump({"policy": tpl["policy"]}, open(os.path.join(FIX, "pipeline.json"), "w"), ensure_ascii=False)

    w = lambda p, s: open(os.path.join(FIX, p), "w", encoding="utf-8").write(s)

    w("SCOPE.md", "---\nformats: [brief, report, memo, infographic]\n---\n# 범위\n")
    w("evidence.md", """# 근거 종합

```evidence
- id: e1
  grade: high
  statement: 사전 신고제는 사고율을 낮춘다
  sources: [gov_a_2024]
- id: e2
  grade: moderate
  statement: 교육 의무화는 준수율을 높인다
  sources: [acad_b_2023]
- id: e4
  grade: low
  statement: 인센티브 효과는 불확실하다
  sources: [ind_c_2022]
```
""")
    w("context.md", """# 정책 환경

```stakeholders
- id: s1
  name: 중소 제조사
  category: industry
  interest: 규제 준수 비용 부담
  position: 유예기간 요구
- id: s2
  name: 산업안전보건공단
  category: government
  interest: 감독 역량
  position: 신고제 확대 찬성
- id: s3
  name: 노동조합
  category: ngo
  interest: 현장 노동자 안전
  position: 즉시 시행 요구
```
""")
    w("options.md", "# 정책 옵션\n\nrecommended_option: O2\n\n- O1 현상유지\n- O2 단계적 신고제\n")

    # ⚠️ 인용을 일부러 **조사 붙은 형태**(e1을 · e2에서)로 쓴다 — 원본 정규식(\\b)이라면
    #    한 건도 못 읽고 '인용 0건'으로 오탐한다. 우리 게이트는 읽어야 한다.
    w("formats/brief.md", f"""# 정책 브리프

중소 제조사와 산업안전보건공단, 노동조합의 의견을 들었다. e1을 근거로 신고제를 제안한다.
e2에서 교육 의무화의 효과가 확인된다.

## 정책 권고

O2를 권고한다. e1을 핵심 근거로 삼는다. 인센티브는 잠정 판단이며 e4는 추가 연구가 필요하다.

{filler(900)}
""")
    w("formats/report.md", f"""# 정책 보고서

중소 제조사, 산업안전보건공단, 노동조합의 이해와 입장을 각각 분석한다. e1을 중심 근거로 한다.
e2도 함께 검토했다.

## 정책 권고

O2를 권고한다(근거 e1, e2).

{filler(5600)}
""")
    w("formats/memo.md", f"""# 결정 메모

중소 제조사·산업안전보건공단·노동조합 영향. e1을 근거로 함.

## 권고

O2를 권고한다. e2도 뒷받침한다.

{filler(500)}
""")
    w("formats/infographic.md", f"""# 인포그래픽 브리프

O2를 시각화한다. e1을 중심 수치로 쓴다.

{filler(400)}
""")


def run(gate, draft="formats"):
    r = subprocess.run(["python3", os.path.join(GATES, f"{gate}.py"),
                        "--policy", os.path.join(FIX, "pipeline.json"),
                        "--sources", os.path.join(FIX, "raw", "sources.yaml"),
                        "--draft", os.path.join(FIX, draft)],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def expect(label, gate, want, show=False):
    rc, out = run(gate)
    ok = "OK " if rc == want else "‼️ "
    print(f"{ok}{label:52s} exit={rc} (기대 {want})")
    if rc != want or show:
        print("      " + "\n      ".join(out.splitlines()[-6:]))
    return rc == want


def patch(path, old, new):
    p = os.path.join(FIX, path)
    t = open(p, encoding="utf-8").read()
    assert old in t, f"픽스처 치환 실패: {old!r} not in {path}"
    open(p, "w", encoding="utf-8").write(t.replace(old, new))


results = []
print("── ① 정상 픽스처: 3게이트 모두 PASS 해야 한다 ──")
build(); results.append(expect("정상 · evidence_grade", "evidence_grade", 0, show=True))
results.append(expect("정상 · stakeholder_coverage", "stakeholder_coverage", 0))
results.append(expect("정상 · format_consistency", "format_consistency", 0, show=True))

print("\n── ② evidence_grade 를 깨뜨린다 ──")
build(); patch("formats/memo.md", "e1을 근거로 함", "근거는 생략한다")
patch("formats/memo.md", "e2도 뒷받침한다", "확신한다")
results.append(expect("근거 인용 0건(memo)", "evidence_grade", 1))

build(); patch("formats/brief.md", "e1을 근거로 신고제", "e99를 근거로 신고제")
results.append(expect("환각 인용 e99 — 원본은 통과시켰다", "evidence_grade", 1))

build(); patch("formats/brief.md", "인센티브는 잠정 판단이며 e4는 추가 연구가 필요하다",
               "인센티브 제도를 e4에 따라 즉시 도입한다")
results.append(expect("low 근거를 유보 표현 없이 인용", "evidence_grade", 1))

build(); patch("formats/report.md", "## 정책 권고\n\nO2를 권고한다(근거 e1, e2).",
               "## 정책 권고\n\nO2를 권고한다(근거 e4). 잠정 판단이다.")
results.append(expect("권고 절이 low 근거만 인용 — 원본 미검사", "evidence_grade", 1))

print("\n── ③ stakeholder_coverage 를 깨뜨린다 ──")
build(); patch("formats/report.md", "중소 제조사, 산업안전보건공단, 노동조합의 이해와 입장을 각각 분석한다.",
               "중소 제조사와 산업안전보건공단의 이해와 입장을 분석한다.")
patch("formats/brief.md", "중소 제조사와 산업안전보건공단, 노동조합의 의견을 들었다.",
      "중소 제조사와 산업안전보건공단의 의견을 들었다.")
patch("formats/memo.md", "중소 제조사·산업안전보건공단·노동조합 영향",
      "중소 제조사·산업안전보건공단 영향")
results.append(expect("s3(노동조합) 전 문서 누락", "stakeholder_coverage", 1))

build(); patch("formats/report.md", "중소 제조사, 산업안전보건공단, 노동조합의 이해와 입장을 각각 분석한다.",
               "중소 제조사와 산업안전보건공단의 이해와 입장을 분석한다.")
results.append(expect("report(전수 문서)에서만 s3 누락", "stakeholder_coverage", 1))

build(); patch("context.md", "  position: 즉시 시행 요구\n", "")
results.append(expect("context 의 position 공란 — 원본 미검사", "stakeholder_coverage", 1))

print("\n── ④ format_consistency 를 깨뜨린다 ──")
build(); os.remove(os.path.join(FIX, "formats", "memo.md"))
results.append(expect("선언된 memo.md 부재 — 원본은 통과시켰다", "format_consistency", 1))

build(); patch("formats/memo.md", "O2를 권고한다", "O3을 권고한다")
results.append(expect("메모만 다른 옵션 권고", "format_consistency", 1))

build(); patch("formats/brief.md", filler(900), filler(120))
results.append(expect("브리프 분량 미달", "format_consistency", 1))

build(); patch("formats/report.md", filler(5600), filler(30000))
results.append(expect("보고서 분량 초과", "format_consistency", 1))

print(f"\n{sum(results)}/{len(results)} 통과")
sys.exit(0 if all(results) else 1)
