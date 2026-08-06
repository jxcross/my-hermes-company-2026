# SCOPE.md: M-2026-007

## 1. 연구 주제 (Research Topics)
- **온디바이스 SLM을 위한 양자화 기술 최점화**: 4-bit 이하 극저비트 양자화가 추론 성능 및 정확도에 미치는 영향 분석.
- **KV 캐시 효율화 및 메모리 관리**: 긴 컨텍스트 처리 시 On-device 메모리 제약을 극복하기 위한 KV Cache 압축 및 캐싱 전략.
- **병렬 추론 최적화 (Parallel Inference)**: 모바일/엣지 GPU 및 NPU 가속을 위한 연산 병렬화 및 레이어별 분할 기법.

## 2. 기여 (Contributions)
- 온디바이스 환경에 특화된 효율적 추론 매커니즘의 종합적인 분석 및 체계화.
- 양자화, KV 캐시, 병렬화 기술 간의 상호작용이 추론 속도 및 에너지 효율에 미치는 임팩트 규명.
- 차세대 소형 언어모델(SLM) 연구를 위한 핵심 벤치마크 지표 및 프레임워크 가이드라인 제시.

## 3. 범위 (Scope)
- **포함 (In-Scope)**:
    - Quantization (INT4, NF4, AWQ 등), KV Cache compression/management, Parallelism in edge hardware.
    - SLM (Small Language Models, <10B parameters).
- **제외 (Ex-Scope)**:
    - 대규모 LLM (Llamas 70B+) 전용 아키텍처 연구.
    - 하드웨어 가속기 자체의 물리적 설계 변경 (알고리즘/소프트웨어 레벨에 집중).

## 4. 완료 기준 (Acceptance Criteria)
- `pipeline.json`에 정의된 `source_balance_policy` 및 `recency_policy` 충족.
- 모든 분석 섹션이 `analysis_substance_policy`의 최소 요건(150자 이상, 근거 불릿 3개 이상 등)을 준수할 것.

## 5. 목표 인용 수 (Target Citations)
- N = 40+ papers.

## 6. 정책 (Policies)
### Recency Policy
- 최근 3년 이내 논문 비중 50% 이상 유지.
- 15년 이전 논문은 엄격히 제외(Seminal works 제외).

### Source Balance Policy
- Peer-reviewed: min 6
- Preprint: min 2
- Survey: min 1
- 기타 (web, dataset_code 등) 포함하여 다양성 확보.
