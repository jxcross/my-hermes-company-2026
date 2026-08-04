#!/usr/bin/env python3
"""lecture-course 4게이트를 '일부러 깨뜨린 픽스처'로 검증한다 (docs/13 §5)."""
import json, os, shutil, subprocess, sys
import yaml

ROOT = "/work/company"
FIX = "/tmp/lc"
GATES = os.path.join(ROOT, "scripts", "gates")


def build():
    shutil.rmtree(FIX, ignore_errors=True)
    for d in ("content/slides", "content/assignments", "content/quiz"):
        os.makedirs(os.path.join(FIX, d))

    tpl = yaml.safe_load(open(os.path.join(ROOT, "templates", "lecture-course.yaml"), encoding="utf-8"))
    json.dump({"policy": tpl["policy"]}, open(os.path.join(FIX, "pipeline.json"), "w"), ensure_ascii=False)

    w = lambda p, s: open(os.path.join(FIX, p), "w", encoding="utf-8").write(s)
    w("SCOPE.md", "---\neducation_level: undergraduate\nweeks: 4\n"
                  "outputs: [syllabus, slides, assignments, quiz]\n---\n# 범위\n")

    w("objectives.md", """# 학습목표

```objectives
- id: lo1
  bloom: understand
  statement: 손실함수의 역할을 설명한다
  concepts: [c1]
- id: lo2
  bloom: apply
  statement: 문제 유형에 맞는 손실함수를 선택한다
  concepts: [c2]
- id: lo3
  bloom: analyze
  statement: 학습 곡선을 분석하여 원인을 진단한다
  concepts: [c3]
- id: lo4
  bloom: 평가
  statement: 두 모델의 성능 보고를 비판적으로 평가한다
  concepts: [c4]
- id: lo5
  bloom: create
  statement: 주어진 과제에 맞는 평가 설계를 제안한다
  concepts: [c5]
```
""")
    w("structure.md", """# 주차 구조

```units
- week: 1
  title: 개요
  los: [lo1]
- week: 2
  title: 손실함수
  los: [lo2]
- week: 3
  title: 진단
  los: [lo3]
- week: 4
  title: 평가와 설계
  los: [lo4, lo5]
```
""")
    w("assessment.md", """# 평가 계획

```assignments
- id: a1
  title: 손실함수 비교
  los: [lo1, lo2]
  week: 2
  weight: 30
- id: a2
  title: 평가 설계 제안
  los: [lo4, lo5]
  week: 4
  weight: 30
```

```quizzes
- id: q1
  title: 중간 퀴즈
  los: [lo3]
  week: 3
  weight: 40
```
""")
    w("content/syllabus.md", """# 강의계획서

학습목표: lo1, lo2, lo3, lo4, lo5

## 주차 일정
- 1주차 개요
- 2주차 손실함수
- 3주차 진단
- 4주차 평가와 설계

## 평가 비중
과제 60%, 퀴즈 40%
""")
    w("content/slides/week-01.md", """# 1주차 개요

## 학습목표
- lo1

## 핵심 개념
- 손실함수의 정의
- 오차의 종류

![학습 곡선 그래프: 에폭에 따른 훈련·검증 손실 변화](img/curve.png)

<!-- 발표자 노트: 첫 시간이므로 사례를 먼저 보여준다 -->
""")
    w("content/assignments/a-01.md", """# 과제 1 — 손실함수 비교

대상 학습목표: lo1, lo2

## 채점 루브릭
- 비교 기준의 타당성 40점
- 실험 설계 30점
- 해석 30점
""")
    w("content/quiz/q-01.md", """# 중간 퀴즈

대상 학습목표: lo3

1. 학습 곡선에서 과적합의 징후는 무엇인가?
""")


def run(gate, draft):
    r = subprocess.run(["python3", os.path.join(GATES, f"{gate}.py"),
                        "--policy", os.path.join(FIX, "pipeline.json"),
                        "--sources", os.path.join(FIX, "raw", "sources.yaml"),
                        "--draft", os.path.join(FIX, draft)],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


DRAFTS = {"objective_coverage": "objectives.md", "bloom_distribution": "objectives.md",
          "course_consistency": "content", "content_accessibility": "content"}


def expect(label, gate, want, show=False):
    rc, out = run(gate, DRAFTS[gate])
    print(f"{'OK ' if rc == want else '‼️ '}{label:54s} exit={rc} (기대 {want})")
    if rc != want or show:
        print("      " + "\n      ".join(out.splitlines()[-8:]))
    return rc == want


def patch(path, old, new):
    p = os.path.join(FIX, path)
    t = open(p, encoding="utf-8").read()
    assert old in t, f"픽스처 치환 실패: {old!r} not in {path}"
    open(p, "w", encoding="utf-8").write(t.replace(old, new))


results = []
print("── ① 정상 픽스처: 4게이트 모두 PASS ──")
build()
results.append(expect("정상 · objective_coverage", "objective_coverage", 0, show=True))
results.append(expect("정상 · bloom_distribution", "bloom_distribution", 0, show=True))
results.append(expect("정상 · course_consistency", "course_consistency", 0, show=True))
results.append(expect("정상 · content_accessibility", "content_accessibility", 0))

print("\n── ② objective_coverage 를 깨뜨린다 ──")
build(); patch("assessment.md", "  los: [lo3]\n", "  los: [lo1]\n")
results.append(expect("lo3 이 어느 평가에도 없음", "objective_coverage", 1))

build(); patch("structure.md", "- week: 3\n  title: 진단\n  los: [lo3]",
               "- week: 3\n  title: 진단\n  # lo3 은 여기서 다룬다")
results.append(expect("주석의 스치는 언급은 배치가 아니다(원본은 인정)", "objective_coverage", 1))

build(); patch("structure.md", "- week: 1\n  title: 개요\n  los: [lo1]",
               "- week: 1\n  title: 개요\n  los: []")
patch("structure.md", "  los: [lo4, lo5]", "  los: [lo4, lo5, lo1]")
results.append(expect("학습목표 없는 빈 주차 — 원본에 없던 역방향 검사", "objective_coverage", 1))

build(); patch("objectives.md", """- id: lo4
  bloom: 평가
  statement: 두 모델의 성능 보고를 비판적으로 평가한다
  concepts: [c4]
- id: lo5
  bloom: create
  statement: 주어진 과제에 맞는 평가 설계를 제안한다
  concepts: [c5]
""", "")
patch("structure.md", "  los: [lo4, lo5]", "  los: [lo3]")
patch("assessment.md", "  los: [lo4, lo5]", "  los: [lo1]")
results.append(expect("학습목표 3개 < 최소 5개(분모 축소 방지)", "objective_coverage", 1))

print("\n── ③ bloom_distribution 을 깨뜨린다 ──")
build(); patch("objectives.md", "  bloom: analyze", "  bloom: understand")
patch("objectives.md", "  bloom: 평가", "  bloom: understand")
patch("objectives.md", "  bloom: create", "  bloom: understand")
results.append(expect("평가+창안 0% < 10%", "bloom_distribution", 1))

build(); patch("objectives.md", "  bloom: apply\n  statement: 문제 유형에", "  statement: 문제 유형에")
results.append(expect("Bloom 단계 미표기 LO(분모에서 조용히 빠짐)", "bloom_distribution", 1))

print("\n── ④ course_consistency 를 깨뜨린다 ──")
build(); patch("assessment.md", "  weight: 40", "  weight: 25")
results.append(expect("성적 비중 합계 85% — 원본은 `pass` 죽은 코드", "course_consistency", 1))

build(); patch("content/syllabus.md", "- 3주차 진단\n", "")
results.append(expect("강의계획서에 3주차 누락(국문 주차 인식)", "course_consistency", 1))

build(); patch("content/quiz/q-01.md", "lo3", "lo9")
results.append(expect("정의되지 않은 lo9 참조", "course_consistency", 1))

build(); shutil.rmtree(os.path.join(FIX, "content/assignments"))
results.append(expect("선언된 산출물 assignments 부재", "course_consistency", 1))

print("\n── ⑤ content_accessibility 를 깨뜨린다 ──")
build(); patch("content/slides/week-01.md",
               "![학습 곡선 그래프: 에폭에 따른 훈련·검증 손실 변화](img/curve.png)",
               "![](img/curve.png)")
results.append(expect("대체 텍스트 없는 이미지", "content_accessibility", 1))

print("\n── ⑥ 원본 결함의 회귀 방어 ──")
build()
results.append(expect("국문 Bloom 표기('평가')를 단계로 인정", "bloom_distribution", 0))
build()
results.append(expect("국문 '3주차' 를 주차로 인식", "course_consistency", 0))
build()
patch("content/slides/week-01.md", "- 손실함수의 정의\n- 오차의 종류",
      "- 손실함수의 정의\n- 오차의 종류\n- 회귀와 분류의 차이\n- 이상치 민감도")
results.append(expect("불릿 슬라이드를 긴 문장으로 오판하지 않는다", "content_accessibility", 0))

print(f"\n{sum(results)}/{len(results)} 통과")
sys.exit(0 if all(results) else 1)
