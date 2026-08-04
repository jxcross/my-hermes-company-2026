#!/usr/bin/env python3
"""legal-draft 3게이트를 '일부러 깨뜨린 픽스처'로 검증한다 (docs/13 §5).
원본 2종은 항상 FAIL 하는 상태였으므로, **정상 픽스처가 PASS 하는지**가 먼저다."""
import json, os, shutil, subprocess, sys
import yaml

ROOT = "/work/company"
FIX = "/tmp/lf"
GATES = os.path.join(ROOT, "scripts", "gates")


def build():
    shutil.rmtree(FIX, ignore_errors=True)
    os.makedirs(os.path.join(FIX, "docs"))

    tpl = yaml.safe_load(open(os.path.join(ROOT, "templates", "legal-draft.yaml"), encoding="utf-8"))
    json.dump({"policy": tpl["policy"]}, open(os.path.join(FIX, "pipeline.json"), "w"), ensure_ascii=False)

    w = lambda p, s: open(os.path.join(FIX, p), "w", encoding="utf-8").write(s)
    w("SCOPE.md", "---\ndoc_types: [contract, opinion]\ndomain: it_sw\n---\n# 범위\n")

    # 계약서: 필수 11조항 + it_sw 도메인 3조항. 일부러 **별칭**(용역대금·계약기간)을 섞는다.
    w("docs/contract.md", """# 소프트웨어 용역 계약서

## 제1조 (당사자)
갑: [갑의 상호] (사업자등록번호: 000-00-00000)

## 제2조 (정의)
본 계약에서 사용하는 용어는 다음과 같다.

## 제3조 (목적)
본 계약은 소프트웨어 개발 용역을 목적으로 한다.

## 제4조 (권리와 의무)
을은 「민법」 제390조에 따라 채무를 이행하여야 한다.

## 제5조 (용역대금)
대금은 일천만원(10,000,000원)으로 한다.

## 제6조 (계약기간)
2026년 1월 1일부터 12개월간으로 한다.

## 제7조 (비밀유지)
갑과 을은 상대방의 영업비밀을 5년간 비밀로 유지한다.

## 제8조 (손해배상)
민법 제393조에 따라 통상손해를 배상한다.

## 제9조 (해지)
30일 이상의 시정 요구에 응하지 않는 경우 해지할 수 있다.

## 제10조 (분쟁해결)
갑의 본점 소재지 관할 지방법원을 제1심 관할 법원으로 한다.

## 제11조 (서명)
갑: ______  을: ______

## 제12조 (라이센스 범위)
산출물의 라이센스 범위는 다음과 같다.

## 제13조 (데이터 처리 및 개인정보 보호)
개인정보보호법 제29조에 따라 안전조치를 이행한다.

## 제14조 (보안 사고 통지)
보안 사고 발생 시 24시간 이내에 통지한다.

---
본 문서는 법률 자문이 아닙니다. 법적 효력 발생 전 자격 있는 변호사 검토 필수.
""")
    w("docs/opinion.md", """# 법률 의견서

## 1. 사실관계
갑과 을은 용역 계약을 체결하였다.

## 2. 법적 쟁점
산출물의 저작권 귀속이 쟁점이다.

## 3. 적용법령
저작권법 제9조 및 민법 제105조가 적용된다.

## 4. 법률 분석
업무상저작물 요건을 검토한다.

## 5. 결론
저작권은 갑에게 귀속되는 것으로 판단된다.

---
본 문서는 법률 자문이 아닙니다. 자격 있는 변호사 검토를 권장합니다.
""")


def run(gate, draft="docs"):
    r = subprocess.run(["python3", os.path.join(GATES, f"{gate}.py"),
                        "--policy", os.path.join(FIX, "pipeline.json"),
                        "--sources", os.path.join(FIX, "raw", "sources.yaml"),
                        "--draft", os.path.join(FIX, draft)],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def expect(label, gate, want, show=False):
    rc, out = run(gate)
    print(f"{'OK ' if rc == want else '‼️ '}{label:50s} exit={rc} (기대 {want})")
    if rc != want or show:
        print("      " + "\n      ".join(out.splitlines()[-7:]))
    return rc == want


def patch(path, old, new):
    p = os.path.join(FIX, path)
    t = open(p, encoding="utf-8").read()
    assert old in t, f"픽스처 치환 실패: {old!r} not in {path}"
    open(p, "w", encoding="utf-8").write(t.replace(old, new))


results = []
print("── ① 정상 픽스처: 3게이트 모두 PASS 해야 한다(원본 2종은 여기서 이미 FAIL 했다) ──")
build()
results.append(expect("정상 · clause_completeness", "clause_completeness", 0, show=True))
results.append(expect("정상 · law_citation", "law_citation", 0, show=True))
results.append(expect("정상 · legal_safety", "legal_safety", 0))

print("\n── ② clause_completeness 를 깨뜨린다 ──")
build(); patch("docs/contract.md", "## 제9조 (해지)", "## 제9조 (중도종료)")
results.append(expect("필수 조항 '해지' 누락(별칭 아닌 이름)", "clause_completeness", 1))

build(); patch("docs/contract.md", "## 제14조 (보안 사고 통지)", "## 제14조 (기타)")
results.append(expect("도메인(it_sw) 추가 조항 누락", "clause_completeness", 1))

build(); os.remove(os.path.join(FIX, "docs", "opinion.md"))
results.append(expect("선언된 opinion.md 부재", "clause_completeness", 1))

build(); patch("docs/contract.md", "## 제7조 (비밀유지)\n갑과 을은",
               "갑과 을은 비밀유지 의무를 진다.\n\n갑과 을은")
results.append(expect("조항이 제목 아닌 본문 언급뿐", "clause_completeness", 1))

print("\n── ③ law_citation 을 깨뜨린다 ──")
build(); patch("docs/contract.md", "민법 제393조", "민법 393조")
results.append(expect("'제' 누락 형식 오류", "law_citation", 1))

build(); patch("docs/opinion.md", "저작권법 제9조", "저작권법 제9999조")
results.append(expect("환각 조문 번호(상한 초과)", "law_citation", 1))

build(); patch("docs/contract.md", "개인정보보호법 제29조", "개인정보보호법 제29조 2항")
results.append(expect("항 표기의 '제' 누락", "law_citation", 1))

print("\n── ④ legal_safety 를 깨뜨린다 ──")
build(); patch("docs/contract.md", "사업자등록번호: 000-00-00000", "사업자등록번호: 214-86-53075")
results.append(expect("사업자등록번호 평문(PUBLIC repo)", "legal_safety", 1))

build(); patch("docs/contract.md", "갑: ______  을: ______", "갑 대표자 주민등록번호 850101-1234567")
results.append(expect("주민등록번호 평문", "legal_safety", 1))

build(); patch("docs/opinion.md", "본 문서는 법률 자문이 아닙니다. 자격 있는 변호사 검토를 권장합니다.", "끝.")
results.append(expect("고지 문구 누락", "legal_safety", 1))

print("\n── ⑤ 원본 결함의 회귀 방어(우리 게이트는 이 정상 입력을 통과시켜야 한다) ──")
build()
ok = expect("별칭 조항명(용역대금·계약기간·권리와 의무)", "clause_completeness", 0)
results.append(ok)
build()
results.append(expect("문장 중간 법령 인용('본 계약은 민법 제390조')", "law_citation", 0))
build()
results.append(expect("플레이스홀더 000-00-00000 은 개인정보 아님", "legal_safety", 0))

print(f"\n{sum(results)}/{len(results)} 통과")
sys.exit(0 if all(results) else 1)
