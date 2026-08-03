# S07 — WildClawBench

- 원자료: `raw/arxiv-wildclawbench.md` (arXiv preprint, 2026-05)
- 성격: peer review 전 preprint. benchmark 설계와 보고 점수는 저자 실험 설정에서만 해석한다.

## 핵심 주장과 근거
1. **주장:** synthetic sandbox·short-horizon·mock API·final-answer check 중심 benchmark만으로는 deployed runtime의 현실적 장기 작업 완수 여부를 충분히 알기 어렵다. [Abstract, L20–24]
   - **근거:** 60개의 human-authored bilingual·multimodal task를 actual CLI harness와 real tool이 있는 reproducible Docker에서 수행하도록 설계했다. [L24, L34]
2. **주장:** 평가 grading은 rule check·environment-state side-effect audit·LLM/VLM semantic judge를 결합해야 한다. [Abstract, L24; task specification, L68]
   - **근거:** 각 task는 YAML metadata, agent prompt, expected behavior, human rubric, workspace와 executable grading function을 갖는다. [L68]
3. **주장:** 현재 frontier model의 long-horizon native-runtime 성능은 포화되지 않았고 harness choice가 결과에 영향을 준다. [§실험, L36, L183, L268]
   - **근거/수치:** OpenClaw에서 최고 Claude Opus 4.7은 62.2%, 다른 모델은 60% 미만이며 19.3–62.2%의 43-point 범위라고 보고한다. [L36, L183]
   - **근거:** Claude Code에서는 일부 모델이 OpenClaw 대비 10점 이상 하락했고, Hermes Agent는 4개 모델 중 3개에서 best harness라고 보고한다. [L190]

## 한계
- 모든 task가 단일 초기 지시 후 자율 실행하는 single-turn 구조라 실행 중 clarification·correction·follow-up을 포착하지 못한다. [§Limitations, L278]
- 정확한 발행일은 원자료 메타데이터에서 미확인; preprint 상태를 유지한다. [L4–9]

## 상충 표시
- `S10`의 controlled synthetic state-grounded environment 접근과 대비된다. WildClawBench는 native runtime·real tool 접근을, Echoverse는 reset 가능한 synthetic world를 강조한다. 우열 판정 없이 목적(현실성 vs 반복가능 training/RL)을 구분해 검증 단계로 넘긴다.
