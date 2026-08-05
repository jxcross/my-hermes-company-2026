# 깨뜨린 픽스처 E2E 하네스

`scripts/tests/test_gates.py`(순수함수 단위 테스트)가 잡지 못하는 것을 잡는다 —
**게이트를 CLI 로 실제 실행해 exit code 를 확인한다.**

## 왜 필요한가

`docs/13 §5`의 핵심 교훈이다. 이식한 게이트는 두 방향 모두에서 무너진다:

- **느슨한 쪽** — PASS 만 보면 아무것도 측정하지 않는 게이트를 발견할 수 없다
  (patentforge 의 한국어 정규식 붕괴 · docforge 의 부분 문자열 검사 100% ·
  secforge 의 fail-open 3종).
- **빡빡한 쪽** — 정상 픽스처로 PASS 를 확인하지 않으면, 파이프라인을 막아 놓고
  "게이트를 이식했다"고 기록하게 된다(legalforge 의 게이트 2종은 **어떤 입력에도 FAIL**
  하는 상태였다).

그래서 각 하네스는 **정상 픽스처(PASS 기대) + 고의로 깨뜨린 픽스처(FAIL 기대) +
원본 결함의 회귀 방어**를 함께 돌린다.

실제로 이 하네스가 **내 게이트의 자체 결함도 여러 번 잡았다**:
`week: 1` 필드형 주차 미인식(J) · 블록 부재 시 exit 1/2 불일치(L) ·
픽스처 자신의 truncate-before-read 로 48행 대신 0행을 검사하던 것(M —
게이트는 옳았지만 **테스트가 주장한 것을 테스트하지 않고 있었다**) ·
데이터시트 절 하한과 라이선스 조합을 잘못 고른 픽스처(N — **정상 픽스처가 PASS 하는지**를
확인하지 않았다면 판정 기준이 과도한 채로 남았을 것이다).

## 실행

컨테이너 안에서 돈다(PyYAML·git 필요). 픽스처는 컨테이너의 `/tmp/` 아래에 만들어지고
저장소를 건드리지 않는다.

```bash
# 전체
docker exec hermes-solomon sh -c 'cd /work/company && python3 scripts/tests/fixtures/run_all.py'

# 하나만
docker exec hermes-solomon sh -c 'cd /work/company && python3 scripts/tests/fixtures/sec.py'
```

## 대응 관계

| 하네스 | 아키타입 | 검사하는 게이트 | 케이스 |
|---|---|---|---|
| `policy.py` | G 정책 브리프 | evidence_grade · stakeholder_coverage · format_consistency | 14 |
| `legal.py` | H 법률 문서 | clause_completeness · law_citation · legal_safety | 16 |
| `docs.py` | I 코드 문서화 | symbol_truth · api_coverage · doc_links | 14 |
| `lecture.py` | J 강의 자료 | objective_coverage · bloom_distribution · course_consistency · content_accessibility | 18 |
| `migrate.py` | K 마이그레이션 | atomic_commit · test_pass_rate · behavior_diff | 19 |
| `sec.py` | L 보안 감사 | finding_completeness · owasp_coverage · cve_remediation · secret_redaction | 22 |
| `agent.py` | M AI 시스템 평가 | eval_set_quality · stat_significance · repro_determinism · run_completeness · source_balance · secret_redaction | 43 |
| `dataset.py` | N 데이터셋 배포 | pii_presence · license_compat · schema_conformance · datasheet_completeness · source_balance | 42 |

**게이트를 고칠 때는 해당 하네스를 반드시 다시 돌려라.** 단위 테스트만 통과하는 수정은
판정 경로 전체를 검증하지 않는다.

> 아키타입 A~F(trend-report·academic-paper·systematic-review·webapp-build·lit-monitor·
> patent-spec)의 게이트는 이 하네스가 만들어지기 전에 이식됐다. 단위 테스트는 있지만
> E2E 하네스는 없다 — 후속 과제로 `docs/13 §7`에 등재.
