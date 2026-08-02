# profiles-src — 전문 profile 정체성 소스 (버전관리)

Stage 1 축소 파이프라인의 전문 에이전트(**named 프로필**) 정체성·설정의 **버전관리 소스**다(시크릿 아님).
`hermes-home/`(컨테이너 `/opt/data`)는 로컬 전용이라 PC 간 이동하지 않으므로, 여기 소스를 새 PC에서 재배포한다.

- `<name>/SOUL.md` — 좁은 역할·경계·운영 원칙(작성자≠검증자 불변식 반영)
- `<name>/config.yaml` — provider/model 설정. **named 프로필은 루트(default) config를 상속하지 않아** 반드시 필요.

> Solomon 자신은 `default` 프로필이며 정체성 소스는 상위 `../solomon-profile/`에 있다.

## 현재 프로필 (축소 슬라이스)
| profile | 역할 | 산출물 |
|---------|------|--------|
| `scout` | 검색·수집 | `raw/` 원문 + 메타(URL·수집일·발행일) |
| `reader` | 심층 분석 | 자료별 주장/근거 분리 |
| `writer` | 보고서 집필 | 출처 포함 Markdown 초안 |

## 배포 방법 (새 PC 부트스트랩 시)
```bash
for p in scout reader writer; do
  docker compose exec hermes-solomon hermes profile create "$p" --description "<역할 요약>"
  cp profiles-src/$p/SOUL.md   hermes-home/profiles/$p/SOUL.md
  cp profiles-src/$p/config.yaml hermes-home/profiles/$p/config.yaml
done
# 검증: docker compose exec hermes-solomon scout -z "너의 역할을 한 문장으로"
```
인증은 계정 단위 OAuth(`hermes auth`, `hermes-home/auth.json`)를 공유하므로 프로필별 재로그인은 불필요하다.

## full 11단계 확장 시 추가 예정
`fact-checker`(≠reader) · `synthesizer` · `reviewer`(≠writer) · `curator`. 상세: [`../docs/10_stage1_plan.md`](../docs/10_stage1_plan.md) §5.
