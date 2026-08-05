#!/usr/bin/env python3
"""dataset-release(아키타입 N) 게이트를 '일부러 깨뜨린 픽스처'로 검증한다 (docs/13 §5).

원본 datasetforge 게이트 3종에서 실측으로 확인한 결함 6건에 **회귀 방어**를 건다:
  · 하드게이트가 **샤드 하나만** 스캔(`glob("data-*.parquet")[0]`)          → ③-1·2
  · 라이선스 보고서가 **없어도 PASS**(`{"verdict":"missing"}` 가 죽은 기본값) → ④-1
  · CLAUDE.md 가 선언한 "unknown = red" 가 **코드에 없음**                  → ④-2
  · 라이선스를 **아무 데도 선언하지 않으면 '일관됨'** PASS                    → ④-3
  · 분류 순서가 green→red 라 **독점 조건이 덧붙은 Apache 헤더가 green**      → ④-4
  · 신용카드 Luhn 이 **고정 창**이라 `4111…1111.50` 미검출                   → ③-3
  · phone_kr 선두 0 이 선택이라 **평범한 10자리 수를 PII 로 과검출**          → ⑦-1
"""
import json, os, shutil, subprocess, sys
import yaml

ROOT = "/work/company"
FIX = "/tmp/dsf"
GATES = os.path.join(ROOT, "scripts", "gates")

N_ROWS = 20
COLS = ["id", "text", "label"]

APACHE = """Apache License
Version 2.0, January 2004
http://www.apache.org/licenses/
"""

# 정상 픽스처의 소스 라이선스. 배포 의도(CC-BY-4.0)와 동일해 양립성이 성립한다.
# ⚠️ Apache-2.0 → CC-BY-4.0 은 이식한 표에서 INCOMPATIBLE 이다(코드 라이선스 기준의
#    보수적 표). 데이터에서 다르게 판단하려면 `license_policy.extra_compatible` 로
#    근거와 함께 넓힌다 — 게이트가 몰래 느슨해지지 않게 정책 쪽에 두었다.
CC_BY = """Creative Commons Attribution 4.0 International
CC-BY-4.0
You are free to share and adapt the material with attribution.
"""

GEBRU_SECTIONS = [
    ("동기", "이 데이터셋은 국문 문서 검색 평가를 위해 만들어졌다. 기존 공개 데이터가 영문 중심이라 국문 질의의 형태소 특성과 조사 변형을 반영하지 못한다는 문제의식에서 출발했다."),
    ("구성", "레코드는 문서 식별자와 본문, 이진 분류 라벨로 이루어진다. 총 20건이며 라벨은 두 종류로 균등하게 나뉜다. 결측값은 없고 모든 열이 필수다."),
    ("수집 과정", "공개 매뉴얼 문서를 내려받아 문단 단위로 분할했다. 수집 시점은 2025년이며 재배포가 허용되지 않는 저작권 표시가 있는 문서는 제외했다. 수집 경로와 시각은 출처 대장에 문서별로 남겼다."),
    ("전처리", "공백 정규화와 인코딩 통일, id 기준 중복 제거를 적용했다. 개인정보로 판단된 열은 제거했고 어떤 규칙으로 몇 행이 줄었는지를 정제 로그에 단계별로 남겼다."),
    ("용도", "국문 문서 검색 모델의 평가에 쓸 수 있다. 개인 식별이나 프로파일링, 실제 서비스의 학습 데이터로 쓰지 말 것을 권고한다. 규모가 작아 일반화된 성능 주장에는 적합하지 않다."),
    ("배포", "CC-BY-4.0 으로 배포하며 출처 표시를 요구한다. 파일은 jsonl 과 csv 두 형식으로 제공되고 두 형식은 동일한 행과 열을 담는다. 배포 경로는 릴리스 노트에 적었다."),
    ("유지보수", "오류 신고는 저장소 이슈로 받는다. 중대한 오류가 확인되면 판올림하고 무엇이 바뀌었는지 변경 이력에 남긴다. 유지보수 주체가 바뀌면 데이터시트에 반영한다."),
]
BENDER_SECTIONS = [
    ("큐레이션 기준", "국문 기술 문서 중 공개 라이선스가 확인된 것만 선별했다. 라이선스가 불명확하거나 재배포 조건을 확인할 수 없는 문서는 규모를 줄이더라도 전부 제외했다."),
    ("언어", "표준 한국어로 작성된 기술 문서이며 영문 외래어 표기가 다수 포함된다. 방언이나 구어체는 포함되지 않으며, 코드 예시와 명령어가 본문에 섞여 있는 경우가 있다."),
    ("화자 인구", "문서 작성자는 해당 제품의 기술 문서 작성자 집단이며 개별 신원 정보는 수집하지 않았다. 연령·성별·지역 정보는 확인할 수 없으므로 인구 통계적 대표성을 주장하지 않는다."),
    ("주석자", "라벨은 문서 구조에 기반한 규칙으로 자동 부여했고 사람 주석자는 참여하지 않았다. 따라서 주석자 간 일치도 지표는 제공하지 않으며 규칙의 한계가 그대로 라벨 품질의 한계가 된다."),
    ("발화 상황", "제품 매뉴얼과 설치 안내라는 비대화형 문어체 상황에서 생성된 텍스트다. 독자를 상정한 설명문이므로 대화나 즉흥 발화의 특성은 나타나지 않는다."),
    ("텍스트 특성", "문단 길이는 평균 300자 내외이며 목록과 표가 자주 등장한다. 자유 서술 열에는 정규식으로 잡히지 않는 형태의 재식별 위험이 남을 수 있으므로 사용 전 검토를 권고한다."),
    ("출처", "출처는 raw/sources.yaml 에 문서별로 기록했으며 라이선스와 수집 연도를 함께 남겼다. 재배포가 허용되지 않는 문서는 수집 단계에서 제외했고 그 목록도 함께 보관한다."),
]


def w(rel, s):
    p = os.path.join(FIX, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(s)


def records():
    return [{"id": f"r{i:03d}", "text": f"문서 {i} 의 본문 내용이다", "label": i % 2}
            for i in range(N_ROWS)]


def build():
    shutil.rmtree(FIX, ignore_errors=True)
    os.makedirs(FIX)

    tpl = yaml.safe_load(open(os.path.join(ROOT, "templates", "dataset-release.yaml"), encoding="utf-8"))
    json.dump({"policy": tpl["policy"]}, open(os.path.join(FIX, "pipeline.json"), "w"),
              ensure_ascii=False)

    # ── 소스 ──────────────────────────────────────────────────────────────
    w("_private/raw/LICENSE", CC_BY)
    w("_private/raw/docs.txt", "원본 문서 내용")
    w("raw/sources.yaml", yaml.safe_dump([
        {"id": "doc1", "title": "제품 매뉴얼", "published_year": 2025,
         "source_type": "primary", "license": "CC-BY-4.0", "status": "selected"},
        {"id": "doc2", "title": "설치 안내", "published_year": 2025,
         "source_type": "primary", "license": "CC-BY-4.0", "status": "selected"},
    ], allow_unicode=True))
    w("ingest.md", f"# 수집\n파일 2건 · 행 {N_ROWS + 2} · 컬럼 3\n")
    w("clean-log.md", f"# 정제 로그\n\nrows_in: {N_ROWS + 2}\nrows_out: {N_ROWS}\n\n"
                      "- 파싱 실패 1행 제거\n- 중복 1행 제거(id 기준)\n")
    w("records-summary.md", f"# 확정 요약\n{N_ROWS}행 · 3열 · CC-BY-4.0 → CC-BY-4.0\n")

    # ── 스키마 ────────────────────────────────────────────────────────────
    w("schema.json", json.dumps({
        "n_rows": N_ROWS,
        "columns": [
            {"name": "id", "dtype": "string", "nullable": False, "description": "레코드 식별자"},
            {"name": "text", "dtype": "string", "nullable": False, "description": "문서 본문"},
            {"name": "label", "dtype": "int", "nullable": False, "description": "분류 라벨(0 또는 1)"},
        ]}, ensure_ascii=False, indent=2))
    w("schema.md", "# 스키마\n| 열 | 타입 | 설명 |\n|---|---|---|\n| id | string | 식별자 |\n")

    # ── 스캔 ──────────────────────────────────────────────────────────────
    w("scan/license-report.md", "verdict: green\nsource_license: CC-BY-4.0\n")
    w("scan/pii-report.md", "# PII\nhigh 0건\n")
    w("scan/scan-summary.md", "# 스캔 요약\n라이선스 green · 개인정보 high 0건\n")

    # ── 번들(정본은 _private/) ────────────────────────────────────────────
    recs = records()
    w("_private/bundle/data/jsonl/data.jsonl",
      "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs))
    csv_rows = ",".join(COLS) + "\n" + "".join(
        f'{r["id"]},"{r["text"]}",{r["label"]}\n' for r in recs)
    w("_private/bundle/data/csv/data.csv", csv_rows)
    w("_private/bundle/manifest.json", json.dumps(
        {"formats": ["jsonl", "csv"], "n_rows": N_ROWS}, ensure_ascii=False))

    # ── 데이터시트 ────────────────────────────────────────────────────────
    w("datasheets/datasheet.md", "---\nlicense: CC-BY-4.0\n---\n\n# 데이터시트\n\n"
      + "\n".join(f"## {t}\n\n{b}\n" for t, b in GEBRU_SECTIONS))
    w("datasheets/data-statement.md", "---\nlicense: CC-BY-4.0\n---\n\n# 데이터 진술서\n\n"
      + "\n".join(f"## {t}\n\n{b}\n" for t, b in BENDER_SECTIONS))
    w("datasheets/croissant.json", json.dumps({
        "@context": "https://schema.org/",
        "@type": "sc:Dataset",
        "name": "korean-manual-qa",
        "description": "국문 기술 문서에서 만든 검색 평가용 데이터셋이다. 문단 단위 본문과 이진 분류 라벨로 이루어져 있으며 공개 라이선스가 확인된 문서만 포함한다.",
        "license": "CC-BY-4.0",
        "recordSet": [{"@type": "cr:RecordSet", "name": "default", "field": COLS}],
    }, ensure_ascii=False, indent=2))

    # ── 보고서 ────────────────────────────────────────────────────────────
    w("report/release-notes.md", """---
license: CC-BY-4.0
---

# 릴리스 노트

- 규모: 20행 · 3열
- 라이선스: 소스 CC-BY-4.0 → 배포 CC-BY-4.0
- 개인정보: 패턴 검사에서 high 0건. 자유 서술 열에 재식별 위험이 남을 수 있다.
- 공개 범위: local_only — 데이터 파일은 저장소에 커밋되지 않는다.
""")
    w("report/usage-disclaimer.md", "# 고지\n본 데이터셋의 개인정보 검사는 패턴 기반이며 법률 자문이 아닙니다.\n")


def run(gate, draft):
    r = subprocess.run(["python3", os.path.join(GATES, f"{gate}.py"),
                        "--policy", os.path.join(FIX, "pipeline.json"),
                        "--sources", os.path.join(FIX, "raw", "sources.yaml"),
                        "--draft", os.path.join(FIX, draft)],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def expect(label, gate, want, show=False, draft="."):
    rc, out = run(gate, draft)
    print(f"{'OK ' if rc == want else '‼️ '}{label:60s} exit={rc} (기대 {want})")
    if rc != want or show:
        print("      " + "\n      ".join(out.splitlines()[-8:]))
    return rc == want


def patch(path, old, new):
    p = os.path.join(FIX, path)
    t = open(p, encoding="utf-8").read()
    assert old in t, f"픽스처 치환 실패: {old!r} not in {path}"
    open(p, "w", encoding="utf-8").write(t.replace(old, new, 1))


def edit_json(rel, fn):
    """JSON 산출물은 indent=2 로 쓰여 있어 압축형 문자열 치환이 맞지 않는다 — 값을 직접 고친다."""
    p = os.path.join(FIX, rel)
    d = json.load(open(p, encoding="utf-8"))
    fn(d)
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def set_mode(mode):
    p = os.path.join(FIX, "pipeline.json")
    d = json.load(open(p, encoding="utf-8"))
    d["policy"]["publication_policy"]["mode"] = mode
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False)


def copy_public():
    shutil.copytree(os.path.join(FIX, "_private/bundle"), os.path.join(FIX, "bundle"))


results = []
print("── ① 정상 픽스처: 5게이트 모두 PASS ──")
build()
results.append(expect("정상 · pii_presence(local_only)", "pii_presence", 0, show=True))
results.append(expect("정상 · license_compat", "license_compat", 0, show=True))
results.append(expect("정상 · schema_conformance", "schema_conformance", 0, show=True))
results.append(expect("정상 · datasheet_completeness", "datasheet_completeness", 0, show=True))
results.append(expect("정상 · source_balance", "source_balance", 0))

print("\n── ② 공개 범위: 선언과 산출 위치가 어긋나면 막는다 ──")
build(); copy_public()
results.append(expect("local_only 인데 커밋 대상에 데이터가 있다", "pii_presence", 1, show=True))

build(); set_mode("repo_commit")
results.append(expect("repo_commit 인데 공개 번들이 없다(선언 대비 부재)", "pii_presence", 1))

build(); set_mode("repo_commit"); copy_public()
results.append(expect("repo_commit + 공개 번들 존재 → PASS", "pii_presence", 0))

build(); set_mode("repo_commit"); copy_public()
patch("bundle/data/jsonl/data.jsonl", "문서 0 의 본문 내용이다", "연락은 hong@example.com 으로")
results.append(expect("공개본에만 개인정보(정본은 깨끗) — 양쪽 다 훑는다", "pii_presence", 1, show=True))

print("\n── ③ pii_presence: **원본이 놓치던 자리** ──")
build()
patch("_private/bundle/data/csv/data.csv", "문서 7 의 본문 내용이다", "메일 kim@corp.co.kr 참고")
results.append(expect("**csv 포맷의 개인정보 — 원본은 parquet 만 봤다**", "pii_presence", 1, show=True))

build()
w2 = os.path.join(FIX, "_private/bundle/data/jsonl/data-00007.jsonl")
open(w2, "w", encoding="utf-8").write(json.dumps(
    {"id": "r999", "text": "주민 900101-1234567", "label": 0}, ensure_ascii=False) + "\n")
results.append(expect("**뒤쪽 샤드의 주민번호 — 원본은 첫 샤드만 봤다**", "pii_presence", 1, show=True))

build()
patch("_private/bundle/data/jsonl/data.jsonl", "문서 3 의 본문 내용이다", "금액 4111111111111111.50 원")
results.append(expect("**카드번호+소수점 — 원본 Luhn 고정 창이 놓쳤다**", "pii_presence", 1, show=True))

build()
patch("_private/bundle/data/jsonl/data.jsonl", "문서 5 의 본문 내용이다", "연락처 010-1234-5678")
results.append(expect("전화번호", "pii_presence", 1))

build()
shutil.copyfile(os.path.join(FIX, "_private/bundle/data/jsonl/data.jsonl"),
                os.path.join(FIX, "_private/bundle/data/jsonl/data.parquet"))
results.append(expect("**읽을 수 없는 형식(parquet) — '못 읽었다'≠'깨끗하다'**",
                      "pii_presence", 1, show=True))

build(); shutil.rmtree(os.path.join(FIX, "_private/bundle"))
results.append(expect("정본 번들 자체가 없음 → fail-closed", "pii_presence", 2))

print("\n── ④ license_compat: **원본 결함 4건의 회귀 방어** ──")
build(); os.remove(os.path.join(FIX, "_private/raw/LICENSE"))
results.append(expect("**LICENSE 파일 없음 — 원본 하드게이트는 PASS 였다**",
                      "license_compat", 1, show=True))

build(); w("_private/raw/LICENSE", "이 데이터는 내부용입니다. All Rights Reserved.")
results.append(expect("독점 라이선스", "license_compat", 1))

build(); w("_private/raw/LICENSE", APACHE + "\nAll Rights Reserved. Proprietary and Confidential.")
results.append(expect("**독점 조건이 덧붙은 Apache 헤더 — 원본은 green**",
                      "license_compat", 1, show=True))

build(); w("_private/raw/LICENSE", "알 수 없는 형식의 이용 약관입니다.")
results.append(expect("**식별 불가(UNKNOWN) — CLAUDE.md 선언이 코드에 없었다**",
                      "license_compat", 1, show=True))

build(); patch("datasheets/datasheet.md", "---\nlicense: CC-BY-4.0\n---\n", "---\n---\n")
patch("datasheets/data-statement.md", "---\nlicense: CC-BY-4.0\n---\n", "---\n---\n")
patch("datasheets/croissant.json", '"license": "CC-BY-4.0",', '')
patch("report/release-notes.md", "---\nlicense: CC-BY-4.0\n---\n", "---\n---\n")
results.append(expect("**어디에도 라이선스 선언 없음 — 원본은 '일관됨' PASS**",
                      "license_compat", 1, show=True))

build(); patch("datasheets/croissant.json", '"license": "CC-BY-4.0"', '"license": "MIT"')
results.append(expect("산출물마다 라이선스 선언이 다르다", "license_compat", 1))

build(); w("_private/raw/LICENSE", "GNU GENERAL PUBLIC LICENSE\nVersion 3, 29 June 2007\n")
results.append(expect("**카피레프트인데 release-notes 에 미명시 — 원본은 무경고 통과**",
                      "license_compat", 1, show=True))

build(); w("_private/raw/LICENSE", "GNU GENERAL PUBLIC LICENSE\nVersion 3, 29 June 2007\n")
patch("report/release-notes.md", "- 라이선스: 소스 CC-BY-4.0 → 배포 CC-BY-4.0",
      "- 라이선스: 소스 GPL-3.0(카피레프트 상속) → 배포 GPL-3.0")
patch("datasheets/datasheet.md", "license: CC-BY-4.0", "license: GPL-3.0")
patch("datasheets/data-statement.md", "license: CC-BY-4.0", "license: GPL-3.0")
patch("datasheets/croissant.json", '"license": "CC-BY-4.0"', '"license": "GPL-3.0"')
patch("report/release-notes.md", "license: CC-BY-4.0", "license: GPL-3.0")
p = os.path.join(FIX, "pipeline.json"); d = json.load(open(p, encoding="utf-8"))
d["policy"]["license_policy"]["intent_license"] = "GPL-3.0"
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False)
results.append(expect("카피레프트라도 명시하면 통과", "license_compat", 0))

print("\n── ⑤ schema_conformance: 선언 ↔ 실제 ──")
build(); edit_json("schema.json", lambda d: d["columns"].append(
    {"name": "score", "dtype": "float", "nullable": True, "description": "예측 점수"}))
results.append(expect("**데이터에 없는 컬럼을 선언(환각)**", "schema_conformance", 1, show=True))

build()
lines = open(os.path.join(FIX, "_private/bundle/data/csv/data.csv"), encoding="utf-8").read().splitlines()
open(os.path.join(FIX, "_private/bundle/data/csv/data.csv"), "w", encoding="utf-8").write(
    "\n".join(lines[:-2]) + "\n")
results.append(expect("**포맷마다 행 수가 다르다 — 원본은 선언만 했다**",
                      "schema_conformance", 1, show=True))

build(); patch("clean-log.md", f"rows_out: {N_ROWS}", f"rows_out: {N_ROWS + 5}")
results.append(expect("정제 로그 rows_out ≠ 산출 행 수(조용한 소실)", "schema_conformance", 1, show=True))

build(); patch("clean-log.md", f"rows_in: {N_ROWS + 2}", f"rows_in: {N_ROWS - 5}")
results.append(expect("rows_in < rows_out(정제가 행을 만들 수는 없다)", "schema_conformance", 1))

build(); patch("schema.json", f'"n_rows": {N_ROWS}', f'"n_rows": {N_ROWS * 2}')
results.append(expect("schema.n_rows ≠ 실제", "schema_conformance", 1))

build(); patch("schema.json", '"description": "문서 본문"', '"description": "TBD"')
results.append(expect("컬럼 설명이 플레이스홀더", "schema_conformance", 1))

build(); os.remove(os.path.join(FIX, "clean-log.md"))
results.append(expect("정제 로그 부재(무슨 변환을 거쳤는지 모른다)", "schema_conformance", 1))

build(); os.remove(os.path.join(FIX, "schema.json"))
results.append(expect("schema.json 부재 → fail-closed", "schema_conformance", 2))

print("\n── ⑥ datasheet_completeness ──")
build(); os.remove(os.path.join(FIX, "datasheets/data-statement.md"))
results.append(expect("**표준 하나가 통째로 없다(병렬 워커 사망)**",
                      "datasheet_completeness", 1, show=True))

build(); patch("datasheets/datasheet.md", GEBRU_SECTIONS[6][1], "TBD")
results.append(expect("절이 플레이스홀더", "datasheet_completeness", 1))

build(); patch("datasheets/datasheet.md", f"## {GEBRU_SECTIONS[4][0]}", "## 잡담")
results.append(expect("필수 절 누락(용도)", "datasheet_completeness", 1))

build(); patch("datasheets/data-statement.md", BENDER_SECTIONS[3][1], "없음")
results.append(expect("절 제목만 있고 본문이 없다", "datasheet_completeness", 1))

build(); edit_json("datasheets/croissant.json", lambda d: d.update({"recordSet": []}))
results.append(expect("croissant recordSet 이 빈 목록", "datasheet_completeness", 1))

build(); edit_json("datasheets/croissant.json", lambda d: d.pop("@context"))
results.append(expect("croissant 필수 필드 누락", "datasheet_completeness", 1))

build(); shutil.rmtree(os.path.join(FIX, "datasheets"))
results.append(expect("datasheets/ 부재 → fail-closed", "datasheet_completeness", 2))

print("\n── ⑦ 설계 판단의 회귀 방어 ──")
build()
patch("_private/bundle/data/jsonl/data.jsonl", "문서 2 의 본문 내용이다", "측정값 1012345678 과 행 id 20191055512345")
results.append(expect("**평범한 10자리 수는 PII 가 아니다 — 원본은 HIGH 로 잡았다**",
                      "pii_presence", 0, show=True))

build()
patch("_private/bundle/data/jsonl/data.jsonl", "문서 4 의 본문 내용이다", "연락처 <EMAIL> 참조")
results.append(expect("마스킹 표기는 통과(막으면 정제 결과를 배포할 수 없다)", "pii_presence", 0))

build()
patch("_private/bundle/data/jsonl/data.jsonl", "문서 6 의 본문 내용이다", "서버 192.168.0.11 접속")
results.append(expect("medium(IP)만으로는 막지 않는다(정책 fail_on=[high])", "pii_presence", 0, show=True))

build()
results.append(expect("`_private/raw/` 는 배포물이 아니다(번들만 검사)", "pii_presence", 0))

print(f"\n{sum(results)}/{len(results)} 통과")
sys.exit(0 if all(results) else 1)
