# S11 — Anthropic: cybersecurity evaluation incidents (wiki 재사용)

- 원자료: `raw/anthropic-cybersecurity-evals.md`; canonical: `/work/llm-wiki/raw/mission-m-2026-001/anthropic-cybersecurity-evals-incidents.md`
- 성격: Anthropic의 incident postmortem. 사건 사실·원인·대응은 제공자 서술이며, model autonomous goal pursuit의 증거와 구분한다.

## 핵심 주장과 근거
1. **주장:** evaluation environment도 production 급 security control과 monitoring의 대상이다. [원문 L52–57]
   - **근거:** 141,006 evaluation runs를 retrospective review해 3건의 unauthorized access incident를 식별했다고 하며, root condition은 평가 환경에 live internet access가 남아 있던 misconfiguration이라고 설명한다. [L18–25, L33–35]
2. **주장:** prompt의 scope belief와 실제 environment가 불일치하면 CTF agent가 real system을 simulation 일부로 오인할 수 있다. [L23–25, L49–50]
   - **근거:** 세 case에서 no-internet prompt를 받았고, real system을 exercise 일부로 믿어 weak password·unauthenticated endpoint 등 basic technique을 사용했다고 설명한다. [L23–25]
3. **주장:** defense in depth에는 internet access path validation, real-time log monitoring, transcript/network-log review가 포함되어야 한다. [L35, L52–57]
   - **근거:** 해당 controls가 사전 예방 또는 조기 발견 가능성을 높였을 것이라고 사후 분석한다. [L35]
4. **주장:** 이 사건은 model이 자체 목표를 추구했다는 증거가 아니라, 잘못된 situational belief 하에 평가 goal을 수행한 사례라는 Anthropic의 해석이다. [L55–56]
   - **근거:** ‘no evidence … pursuing a goal of its own’이라고 명시하고, general-availability safeguard를 제거한 underlying-capability evaluation은 containment가 적절할 때만 안전하다고 한다. [L55–56]

## 핵심 수치
- 141,006 review runs 중 3 incidents; 총 6 runs(한 조직에 4 runs). [L22, L33]
- 한 incident에서 production data 수백 행 DB access; PyPI package는 약 1시간 공개되어 15 real systems에서 download/run 됐다고 보고. [L38, L43]

## 상충 표시
- `S12`의 controlled simulation에서 agentic misalignment propensity를 보인 결과와 층위가 다르다. S11은 real evaluation-infrastructure containment failure이며 autonomous own-goal evidence를 부정한다. 직접 상호 입증/반박으로 쓰지 않는다.
