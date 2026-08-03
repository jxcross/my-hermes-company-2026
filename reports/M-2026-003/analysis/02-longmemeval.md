# LongMemEval — 자료별 분석 노트

- 자료: `longmemeval-benchmarking-chat-assistants` (academic)
- 원문 범위: arXiv Atom 초록만 보존됨.

## 핵심 주장
1. 지속적 상호작용에서 챗 어시스턴트의 장기기억은 충분히 검토되지 않았으며, 벤치마크는 정보 추출·다중세션 추론·시간 추론·지식 업데이트·abstention의 5개 능력을 측정한다. [원문: XML l.16]
2. 상용 챗 어시스턴트와 long-context LLM은 지속 상호작용에 걸친 정보 기억에서 정확도가 30% 하락했다고 저자들이 보고한다. [원문: XML l.16]
3. 메모리 설계를 indexing–retrieval–reading 3단계로 분해하고, 세션 분해·fact-augmented key expansion·time-aware query expansion이 recall 및 downstream QA를 개선한다고 주장한다. [원문: XML l.16]

## 근거·방법론
- 자유롭게 확장 가능한 user-assistant chat history에 500개 수작업 선별 질문을 삽입한다. [원문: XML l.16]
- 위 3단계 프레임워크와 설계 최적화를 광범위하게 실험했다고 서술한다. [원문: XML l.16]

## 정의·수치
- 5 abilities: information extraction, multi-session reasoning, temporal reasoning, knowledge updates, abstention. [원문: XML l.16]
- 500 curated questions; 지속 상호작용 기억 정확도 30% drop(저자 보고). [원문: XML l.16]

## 한계·검증 이관
- ‘30% drop’의 기준선·모델군·분산/유의성은 초록에 없어 수치를 일반화할 수 없다.
- 효과 개선의 절대 점수와 비용/지연 trade-off는 원문 보존본에서 추출 불가다.

- **외부 검증 상태 이관(02-2):** 30% 정확도 하락은 저자 보고이며 독립 재현·동일 기준 비교가 확인되지 않았다. 성능 사실의 일반 결론이나 설계 우위 근거로 사용하지 않는다. [원문: XML l.16; 검증 기록: verify/verification.md §02-2, §7 잔여 보완 1]
- **외부 검증 상태 이관(02-3):** indexing–retrieval–reading 분해와 세 확장 기법의 개선은 저자 보고이며 제3자 ablation 재현이 확인되지 않았다. [원문: XML l.16; 검증 기록: verify/verification.md §02-3, §7 잔여 보완 1]
