# S10 — Microsoft Echoverse (wiki 재사용)

- 원자료: `raw/microsoft-echoverse.md`; canonical 보존본: `/work/llm-wiki/raw/mission-m-2026-001/microsoft-echoverse-computer-use-agents.md`
- 성격: 공식 연구 블로그. 훈련·평가 world와 모델 성능 수치는 Microsoft 실험 결과다.

## 핵심 주장과 근거
1. **주장:** computer-use agent 평가/훈련에는 화면 외형보다 stateful consequence와 state-grounded verifier가 중요하다. [L29–40]
   - **근거:** synthetic world를 reset 가능·안전한 owned database로 구축하고, task는 SQL-derived answer key와 before/after DB diff로 grade한다고 설명한다. [L30, L37–40]
2. **주장:** world의 depth, capability targeting, co-evolution이 단순 environment 수보다 중요한 leverage다. [L33–35, L51–53]
   - **근거:** shallow/deep 동일 domain 비교에서 shallow training은 regressed, deep training은 improved라고 보고한다. [L20–24, L46]
3. **주장:** grounded verifier가 있는 resettable world는 benchmark뿐 아니라 RL environment가 될 수 있다. [L55–57]
   - **근거:** live web은 reset·parallel scale·ground truth가 부족해 RL reward가 noisy해지지만 Echoverse는 snapshot/reset/parallel/database grade를 제공한다고 설명한다. [L55–57]
4. **주장:** task/world/verifier 결함을 model failure로 오인하면 잘못된 curriculum이 된다. [L52–54]
   - **근거/수치:** EchoStay guest control 수정 후 completion 가능 booking은 48%→78%(24개 중 15개 회복), EchoChat verifier realignment로 gradable task는 34%→99%가 됐다고 보고한다. [L52–53]

## 핵심 수치
- 12 worlds로 학습한 9B model base score 36.5%→67.1%, GPT-5.4와 14점 차이라고 보고. [L20]
- held-out datepicker 34.0%→54.0%, held-out filter 62.8%→84.1%; Online-Mind2Web 29.5%→34.3%. [L47]

## 상충 표시
- `S07` WildClawBench의 native runtime/real tool 평가와 대비: Echoverse는 통제·재현·RL reward를 위해 synthetic stateful world를 택한다. 양자는 다른 목적/설계 trade-off이며 성능값 직접 비교 불가.
