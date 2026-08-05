# profiles-src — 전문 profile 정체성 소스 (버전관리)

Stage 1 축소 파이프라인의 전문 에이전트(**named 프로필**) 정체성·설정의 **버전관리 소스**다(시크릿 아님).
`hermes-home/`(컨테이너 `/opt/data`)는 로컬 전용이라 PC 간 이동하지 않으므로, 여기 소스를 새 PC에서 재배포한다.

- `<name>/SOUL.md` — 좁은 역할·경계·운영 원칙(작성자≠검증자 불변식 반영)
- `<name>/config.yaml` — provider/model 설정. **named 프로필은 루트(default) config를 상속하지 않아** 반드시 필요.
  ⚠️ **이 파일의 `model:` 블록은 [`scripts/set_backend.py`](../scripts/set_backend.py)가 생성한다 — 직접 고치지 마라.**

> Solomon 자신은 `default` 프로필이며 정체성 소스는 상위 `../solomon-profile/`에 있다.

## 현재 프로필 (10종 + default)
| profile | 역할 | 티어 | codex 모델 | ollama 모델 | 산출물 |
|---------|------|------|-----------|-------------|--------|
| `scout` | 검색·수집 | 작성자 | terra | gemma4-26b-128k | `raw/` 원문 + 메타(URL·수집일·발행일·source_type) |
| `reader` | 심층 분석 | 작성자 | terra | gemma4-26b-128k | 자료별 주장/근거 분리 |
| `curator` | 선별·정리·지식적재 | 작성자 | terra | gemma4-26b-128k | dedup·관련성 판정 · llm-wiki 반영 |
| `synthesizer` | 종합·구조화 | 작성자 | terra | gemma4-26b-128k | 분류·성숙도·목차 |
| `writer` | 집필 | 작성자 | terra | gemma4-26b-128k | 출처 포함 Markdown 초안 |
| `fact-checker` | 사실·인용 검증 | **검증자** | **sol** | **gemma4-26b-128k** | 교차검증 결과 + `VERDICT:` |
| `reviewer` | 독립 검토 | **검증자** | **sol** | **gemma4-26b-128k** | 완료조건 대조 + `VERDICT:` |
| `architect` | 설계(구조·ERD·화면) | 코더 | terra | gemma4-26b-128k | 설계 문서 + `database/schema.sql` |
| `developer` | 구현 | 코더 | terra | gemma4-26b-128k | 코드 + 단위 테스트 |
| `tester` | 실행 검증 | **검증자** | **sol** | **gemma4-26b-128k** | `test/results.json` + `VERDICT:` |

> **codex 백엔드에서는 검증자가 작성자와 다른 모델을 쓴다**(fact-checker·reviewer·tester).
> 같은 계열은 같은 맹점을 공유하므로 독립검증이 성립하지 않는다.
> **profile 자체는 어느 백엔드에서도 절대 합치지 않는다**(작성자≠검증자 불변식).
>
> **백엔드 전환**(추론 공급자 교체 — 상세 [`../docs/14_local_model_backend.md`](../docs/14_local_model_backend.md)):
> ```bash
> python3 scripts/set_backend.py --show              # 현재 백엔드·배치
> python3 scripts/set_backend.py --build-models      # -64k 파생본 생성(없는 것만)
> python3 scripts/set_backend.py --backend ollama    # 로컬 모델로
> python3 scripts/set_backend.py --backend codex     # OAuth 로 복귀
> ```
> 배치표는 `scripts/set_backend.py` 상단 `TIERS`·`BACKENDS` **한 곳에만** 있다.
> `-128k` 는 Modelfile 로 창을 못박은 파생본이다 — Ollama 의 `/v1` 이 `num_ctx` 를 무시하기
> 때문이다(`docs/14 §3.1`). **131072 이어야 하는 이유는 `docs/14 §3.2`** — 이보다 작으면
> Hermes 압축이 퇴화 분기로 떨어져 파이프라인이 전진하지 못한다.
>
> ⚠️ **로컬 백엔드는 작성자≠검증자를 모델 계열 수준에서 포기했다**(Sam 승인 2026-08-05 ·
> 속도 우선 통일). 남는 분리는 profile·SOUL·객관 게이트 62종이다(`docs/14 §2.2`).
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
# 배치 동기화(hermes 가 새로 만든 config 를 배치표대로 덮는다 — 반드시 실행)
python3 scripts/set_backend.py --backend codex     # 또는 --backend ollama
# 검증: python3 scripts/set_backend.py --show
#       docker compose exec hermes-solomon hermes profile list
#       docker compose exec hermes-solomon scout -z "너의 역할을 한 문장으로"
```
인증은 계정 단위 OAuth(`hermes auth`, `hermes-home/auth.json`)를 공유하므로 프로필별 재로그인은 불필요하다.
(로컬 Ollama 백엔드는 OAuth 자체가 필요 없다 — `docs/14` 참조.)

## 이력
- full 11단계 확장(2026-08-02): `fact-checker`(≠reader) · `synthesizer` · `reviewer`(≠writer) · `curator` 추가. 상세: [`../docs/10_stage1_plan.md`](../docs/10_stage1_plan.md) §5.
- 아키타입 D 도입(2026-08-04): `architect` · `developer` · `tester` 추가. specflow 변환에서 기존 7종으로 덮이지 않는 역할이 나와 신설했다(첫 신규 profile 발생). 근거: [`../docs/13_skill_to_template_conversion.md`](../docs/13_skill_to_template_conversion.md) §7.
- 백엔드 전환기 도입(2026-08-05): codex 주간 한도 소진으로 실미션이 멈춘 것을 계기로 `model:` 블록을 `scripts/set_backend.py` 가 생성하게 바꿨다. 프로필은 그대로, **추론 공급자만 갈아끼운다.** 근거: [`../docs/14_local_model_backend.md`](../docs/14_local_model_backend.md).
