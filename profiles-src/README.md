# profiles-src — 전문 profile 정체성 소스 (버전관리)

Stage 1 축소 파이프라인의 전문 에이전트(**named 프로필**) 정체성·설정의 **버전관리 소스**다(시크릿 아님).
`hermes-home/`(컨테이너 `/opt/data`)는 로컬 전용이라 PC 간 이동하지 않으므로, 여기 소스를 새 PC에서 재배포한다.

- `<name>/SOUL.md` — 좁은 역할·경계·운영 원칙(작성자≠검증자 불변식 반영)
- `<name>/config.yaml` — provider/model 설정. **named 프로필은 루트(default) config를 상속하지 않아** 반드시 필요.

> Solomon 자신은 `default` 프로필이며 정체성 소스는 상위 `../solomon-profile/`에 있다.

## 현재 프로필 (10종 + default)
| profile | 역할 | 모델 | 산출물 |
|---------|------|------|--------|
| `scout` | 검색·수집 | terra | `raw/` 원문 + 메타(URL·수집일·발행일·source_type) |
| `reader` | 심층 분석 | terra | 자료별 주장/근거 분리 |
| `curator` | 선별·정리·지식적재 | terra | dedup·관련성 판정 · llm-wiki 반영 |
| `synthesizer` | 종합·구조화 | terra | 분류·성숙도·목차 |
| `writer` | 집필 | terra | 출처 포함 Markdown 초안 |
| `fact-checker` | 사실·인용 검증 | **sol** | 교차검증 결과 + `VERDICT:` |
| `reviewer` | 독립 검토 | **sol** | 완료조건 대조 + `VERDICT:` |
| `architect` | 설계(구조·ERD·화면) | terra | 설계 문서 + `database/schema.sql` |
| `developer` | 구현 | terra | 코드 + 단위 테스트 |
| `tester` | 실행 검증 | **sol** | `test/results.json` + `VERDICT:` |

> **검증자는 `gpt-5.6-sol`**(fact-checker·reviewer·tester), 작성자 계열은 `gpt-5.6-terra`.
> 검증자 profile 은 절대 작성자와 합치지 않는다(작성자≠검증자 불변식).
>
> **profile 신설은 Sam 승인 사항이다.** 늘어날수록 새 PC 부트스트랩이 길어진다.
> 판정 기준·절차: [`../docs/13_skill_to_template_conversion.md`](../docs/13_skill_to_template_conversion.md) §3·§7 ·
> [`../docs/12_pipeline_negotiation.md`](../docs/12_pipeline_negotiation.md) §2⑤.
> 템플릿이 없는 profile 을 쓰면 `scripts/lint_template.py`가 경고하고 인스턴스화는 중단된다.

**아키타입별 사용**: A 동향보고서 = scout·reader·curator·synthesizer·writer·fact-checker·reviewer ·
B 논문 = 동일 · **D 웹개발 = architect·developer·tester + reviewer·curator**.

## 배포 방법 (새 PC 부트스트랩 시)
```bash
for p in scout reader curator synthesizer writer fact-checker reviewer architect developer tester; do
  docker compose exec hermes-solomon hermes profile create "$p" --description "<역할 요약>"
  cp profiles-src/$p/SOUL.md     hermes-home/profiles/$p/SOUL.md
  cp profiles-src/$p/config.yaml hermes-home/profiles/$p/config.yaml
done
# 검증: docker compose exec hermes-solomon hermes profile list   (모델이 terra/sol 로 맞는지)
#       docker compose exec hermes-solomon scout -z "너의 역할을 한 문장으로"
```
인증은 계정 단위 OAuth(`hermes auth`, `hermes-home/auth.json`)를 공유하므로 프로필별 재로그인은 불필요하다.

## 이력
- full 11단계 확장(2026-08-02): `fact-checker`(≠reader) · `synthesizer` · `reviewer`(≠writer) · `curator` 추가. 상세: [`../docs/10_stage1_plan.md`](../docs/10_stage1_plan.md) §5.
- 아키타입 D 도입(2026-08-04): `architect` · `developer` · `tester` 추가. specflow 변환에서 기존 7종으로 덮이지 않는 역할이 나와 신설했다(첫 신규 profile 발생). 근거: [`../docs/13_skill_to_template_conversion.md`](../docs/13_skill_to_template_conversion.md) §7.
