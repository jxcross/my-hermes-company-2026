# monitors/ — 미션 간 지속 상태 (주기 실행 아키타입 전용)

우리 모델은 **미션 1건 = 파이프라인 1회 실행**이다. 그런데 아키타입 E(주기 문헌 모니터,
`templates/lit-monitor.yaml`)는 매 회차가 새 미션(`M-2026-0NN`)으로 돌면서도
**"이미 본 논문" 기억은 미션을 가로질러 살아야 한다.**

그래서 회차 간 지속되는 상태만 여기에 둔다. 미션 디렉터리(`reports/<MID>/`)에는
**그 회차의 산출만** 담는다.

## 레이아웃

```
monitors/<monitor_id>/
  watchlist.yaml     감시 대상(키워드·저자·학회·주제). Scoping 에서 확정, 회차마다 재사용
  _seen.tsv          본 논문 id 로그(append-only): "<id>\t<YYYY-MM-DD>"
  history/           회차별 다이제스트 보관: <YYYY-WW>.md
```

`monitor_id`는 미션의 `reports/<MID>/SCOPE.md` **frontmatter에 `monitor_id:`로 선언**한다.
`scripts/gates/seen_dedup.py`가 이 값으로 상태 디렉터리를 찾는다(선언이 없으면 fail-closed).

## watchlist.yaml

```yaml
keywords: [on-device inference, quantization]
authors:  [Han Song]
venues:   [NeurIPS, MLSys]
topics:   ["효율적 LLM 추론"]
max_score: 5.0      # 선택(기본 5.0)
```

`scripts/tools/relevance_score.py`가 이 선언을 읽어 회차 간 **재현 가능한** 점수를 매긴다.

## 다루는 명령

```bash
# 이미 본 것 걸러내기(수집 단계)
python3 scripts/tools/monitor_state.py --monitor <id> filter --ids-file <후보id파일>
# 회차 봉인(Deliver 단계) — 다이제스트에 올린 것만이 아니라 후보 '전부'를 넣는다
python3 scripts/tools/monitor_state.py --monitor <id> add <id...> --date 2026-08-04
python3 scripts/tools/monitor_state.py --monitor <id> count
python3 scripts/tools/monitor_state.py --monitor <id> prune --days 365 --today 2026-08-04
```

> `HERMES_MONITORS_ROOT` 환경변수로 이 디렉터리를 덮어쓸 수 있다(테스트용).
>
> **git 추적 대상이다** — `hermes-home/`과 달리 PC 간 이동해야 모니터가 이어진다.
> 다만 `_seen.tsv`는 회차마다 자라므로 주기적으로 `prune` 한다.
