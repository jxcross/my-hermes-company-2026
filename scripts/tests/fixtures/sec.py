#!/usr/bin/env python3
"""security-audit 4게이트를 '일부러 깨뜨린 픽스처'로 검증한다 (docs/13 §5).
원본 3종은 전부 fail-open 이었으므로 **입력이 없을 때 막는지**를 특히 본다."""
import json, os, shutil, subprocess, sys
import yaml

ROOT = "/work/company"
FIX = "/tmp/sf"
GATES = os.path.join(ROOT, "scripts", "gates")

OWASP = "\n".join(
    f"- id: A{i:02d}\n  name: 범주 {i}\n  status: audited\n  findings: 0\n"
    f"  evidence: src/ 전수 검토, 해당 패턴 없음"
    for i in range(1, 11))


def build():
    shutil.rmtree(FIX, ignore_errors=True)
    os.makedirs(os.path.join(FIX, "_private"))
    os.makedirs(os.path.join(FIX, "report"))

    tpl = yaml.safe_load(open(os.path.join(ROOT, "templates", "security-audit.yaml"), encoding="utf-8"))
    json.dump({"policy": tpl["policy"]}, open(os.path.join(FIX, "pipeline.json"), "w"), ensure_ascii=False)

    w = lambda p, s: open(os.path.join(FIX, p), "w", encoding="utf-8").write(s)
    w("SCOPE.md", "---\ncodebase: src\naudit_types: [owasp, cwe, cve, stride]\n---\n# 범위\n")

    w("_private/findings.md", f"""# 발견

n_critical: 0
n_high: 1

```findings
- id: f1
  title: SQL 인젝션 가능성
  severity: high
  category: A03
  location: src/db/query.py:88
  evidence: 사용자 입력을 문자열 포매팅으로 쿼리에 결합한다
  impact: 인증 우회 및 테이블 전체 유출 가능
  remediation: 파라미터 바인딩으로 교체한다
- id: f2
  title: 로그 마스킹 미흡
  severity: low
  category: A09
  location: src/log.py:12
```

```owasp
{OWASP}
```

scanned_manifests: 2
scanned_packages: 137

```cves
- cve_id: CVE-2024-12345
  package: requests
  installed: 2.25.1
  severity: high
  fixed_in: 2.32.0
  remediation: 2.32.0 이상으로 올린다
- cve_id: CVE-2023-9999
  package: urllib3
  installed: 1.26.0
  severity: low
  fixed_in: 1.26.18
```
""")

    w("report/security-report.md", """# 보안 감사 보고서

본 보고서는 정식 보안 감사가 아닙니다. 보안 전문가 검토를 권장합니다.

## 심각도 분포
- Critical 0 · High 1 · Low 1

## 주요 위험
데이터 접근 계층에서 입력이 질의문에 직접 결합되는 패턴이 확인됐다.
상세 위치와 재현은 `_private/` 에 있다.

## 조치 계획
1. 파라미터 바인딩 도입 (2주)
2. 의존성 requests 를 2.32.0 이상으로 갱신 (1주)
""")
    w("report/usage-disclaimer.md", """# 고지

본 문서는 정식 보안 감사가 아닙니다. 침투 테스트를 대체하지 않습니다.
""")
    # _private 에는 진짜 비밀이 있어도 된다(커밋되지 않으므로 게이트 검사 대상 아님)
    w("_private/scan.secrets.md", """# 비밀 스캔
발견 위치: config/settings.py:14
값(내부용): AKIAIOSFODNN7EXAMPLE
""")


def run(gate, draft):
    r = subprocess.run(["python3", os.path.join(GATES, f"{gate}.py"),
                        "--policy", os.path.join(FIX, "pipeline.json"),
                        "--sources", os.path.join(FIX, "raw", "sources.yaml"),
                        "--draft", os.path.join(FIX, draft)],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


DRAFTS = {"finding_completeness": "_private/findings.md", "owasp_coverage": "_private/findings.md",
          "cve_remediation": "_private/findings.md", "secret_redaction": "report"}


def expect(label, gate, want, show=False, draft=None):
    rc, out = run(gate, draft or DRAFTS[gate])
    print(f"{'OK ' if rc == want else '‼️ '}{label:56s} exit={rc} (기대 {want})")
    if rc != want or show:
        print("      " + "\n      ".join(out.splitlines()[-8:]))
    return rc == want


def patch(path, old, new):
    p = os.path.join(FIX, path)
    t = open(p, encoding="utf-8").read()
    assert old in t, f"픽스처 치환 실패: {old!r} not in {path}"
    open(p, "w", encoding="utf-8").write(t.replace(old, new, 1))


results = []
print("── ① 정상 픽스처: 4게이트 모두 PASS ──")
build()
results.append(expect("정상 · finding_completeness", "finding_completeness", 0, show=True))
results.append(expect("정상 · owasp_coverage", "owasp_coverage", 0))
results.append(expect("정상 · cve_remediation", "cve_remediation", 0, show=True))
results.append(expect("정상 · secret_redaction", "secret_redaction", 0, show=True))

print("\n── ② fail-open 이던 지점: 입력이 없으면 막아야 한다 ──")
build(); open(os.path.join(FIX, "_private/findings.md"), "w").write("# 빈 보고서\n")
results.append(expect("findings 블록 없음 → fail-closed", "finding_completeness", 2))
results.append(expect("owasp 블록 없음 → fail-closed", "owasp_coverage", 2))
results.append(expect("cves 블록 없음 → fail-closed", "cve_remediation", 2))

print("\n── ③ finding_completeness 를 깨뜨린다 ──")
build(); patch("_private/findings.md", "n_critical: 0", "n_critical: 3")
results.append(expect("선언 수치≠목록 — 원본은 자기 신고만 봄", "finding_completeness", 1))

build(); patch("_private/findings.md", "  remediation: 파라미터 바인딩으로 교체한다\n", "")
results.append(expect("High 발견에 조치 없음(고칠 수 없는 보고)", "finding_completeness", 1))

build(); patch("_private/findings.md", "  location: src/db/query.py:88\n", "")
results.append(expect("High 발견에 위치 없음", "finding_completeness", 1))

build(); patch("_private/findings.md", "  severity: high\n  category: A03", "  category: A03")
results.append(expect("severity 누락(분류에서 빠짐)", "finding_completeness", 1))

print("\n── ④ owasp_coverage 를 깨뜨린다 ──")
build(); patch("_private/findings.md",
               "- id: A07\n  name: 범주 7\n  status: audited\n  findings: 0\n"
               "  evidence: src/ 전수 검토, 해당 패턴 없음\n", "")
results.append(expect("A07 항목 누락", "owasp_coverage", 1))

build(); patch("_private/findings.md",
               "- id: A05\n  name: 범주 5\n  status: audited\n  findings: 0\n"
               "  evidence: src/ 전수 검토, 해당 패턴 없음",
               "- id: A05\n  name: 범주 5\n  status: audited\n  findings: 0")
results.append(expect("점검 근거 없음 — '했다'는 주장만", "owasp_coverage", 1))

build(); patch("_private/findings.md", "- id: A02\n  name: 범주 2\n  status: audited",
               "- id: A02\n  name: 범주 2\n  status: 나중에")
results.append(expect("허용되지 않는 status", "owasp_coverage", 1))

print("\n── ⑤ cve_remediation 을 깨뜨린다 ──")
build(); patch("_private/findings.md", "scanned_manifests: 2\nscanned_packages: 137\n", "")
results.append(expect("스캔 증거 없음 — 대조 없이 'CVE 0건' 불가", "cve_remediation", 1))

build(); patch("_private/findings.md", "  remediation: 2.32.0 이상으로 올린다\n", "")
results.append(expect("고위험 CVE에 조치 없음", "cve_remediation", 1))

build(); patch("_private/findings.md", "  severity: high\n  fixed_in: 2.32.0", "  fixed_in: 2.32.0")
results.append(expect("severity 비우면 고위험에서 빠지던 구멍", "cve_remediation", 1))

print("\n── ⑥ secret_redaction 을 깨뜨린다 ──")
build(); patch("report/security-report.md", "데이터 접근 계층에서",
               "노출된 키 AKIAIOSFODNN7EXAMPLE 를 확인했다. 데이터 접근 계층에서")
results.append(expect("커밋 대상에 AWS 키 평문(감사가 유출이 된다)", "secret_redaction", 1))

build(); patch("report/security-report.md", "본 보고서는 정식 보안 감사가 아닙니다. 보안 전문가 검토를 권장합니다.\n", "")
results.append(expect("고지 문구 누락", "secret_redaction", 1))

build(); patch("report/security-report.md", "데이터 접근 계층에서",
               "개인키가 발견됐다:\n-----BEGIN RSA PRIVATE KEY-----\n데이터 접근 계층에서")
results.append(expect("개인키 블록 노출", "secret_redaction", 1))

print("\n── ⑦ 설계 판단의 회귀 방어 ──")
build(); patch("_private/findings.md", "n_critical: 0", "n_critical: 2")
patch("_private/findings.md", """- id: f2
  title: 로그 마스킹 미흡
  severity: low
  category: A09
  location: src/log.py:12""", """- id: f2
  title: 인증 우회
  severity: critical
  category: A01
  location: src/auth.py:5
  evidence: 토큰 검증이 없다
  impact: 전체 계정 탈취 가능
  remediation: 서명 검증 추가
- id: f3
  title: 원격 코드 실행
  severity: critical
  category: A03
  location: src/exec.py:9
  evidence: eval 로 사용자 입력 실행
  impact: 서버 장악
  remediation: eval 제거""")
results.append(expect("Critical 2건이어도 통과 — **게이트가 발견을 벌하지 않는다**",
                      "finding_completeness", 0, show=True))

build()
results.append(expect("_private/ 의 진짜 비밀은 검사 대상이 아니다(커밋 안 됨)",
                      "secret_redaction", 0, draft="report"))

print(f"\n{sum(results)}/{len(results)} 통과")
sys.exit(0 if all(results) else 1)
