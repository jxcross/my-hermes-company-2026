# 단일 원자료 분석 노트: QAI AppBuilder - WoS

## 1. 자료 식별과 원문 접근범위

- **자료 식별자:** `qualcomm-qai-appbuilder-wos` (인벤토리 레코드, `raw/sources.yaml` 72–78행)
- **제목:** *QAI AppBuilder - WoS* (인벤토리 73행; 원문 표지/목차에도 동일 표기, 원문 3행)
- **발행 주체:** Qualcomm Technologies, Inc. (원문 1–3행)
- **문서 식별·개정:** `80-94755-1 Rev. AA`; 개정 이력은 **AA / 2025년 10월 / Initial Release**로 표기된다(원문 3행).
- **URL:** <https://docs.qualcomm.com/doc/80-94755-1/80-94755-1_REV_AA_QAI_AppBuilder_-_WoS.pdf> (인벤토리 74행)
- **인벤토리 메타데이터:** vendor 자료, `published_year: 2025`, 2026-08-03 수집, selected 상태(인벤토리 75–78행). 이는 원문의 실증 근거가 아니라 수집·선정 메타데이터다.
- **원문 접근범위:** 제공된 `raw/qualcomm-qai-appbuilder-wos.md`의 텍스트 추출본만 검토했다. 이는 51쪽짜리 슬라이드형 PDF의 추출 텍스트이며, 표지·목차·본문·법률 고지까지 포함되어 있다(원문 3, 54–62행). 다만 페이지별 레이아웃, 도표/스크린샷의 실제 시각 정보와 일부 긴 명령행의 완전한 표시는 보장되지 않는다. **abstract-only 자료는 아니지만**, 성능 그래프·벤치마크 표·실행 로그는 텍스트 원문에서 제공되지 않는다.

## 2. 핵심 주장 — 저자/발행 주체의 서술

1. **QAI AppBuilder는 Snapdragon AI PC의 로컬 NPU에 AI 모델을 배포하기 위한 최적화 API 툴킷이며, 배포 복잡성을 낮춘다.**
   - 원문은 이 도구가 로컬 NPU 추론을 위한 API 집합을 제공하며, 모델 로딩·추론을 위한 소수 API로 개발자가 앱 설계에 집중할 수 있다고 설명한다(원문 3행, p.5–6).
   - 이는 도구 제공자의 제품 설명·가치 제안이며, 비교 실험 결과로 제시되지는 않는다.

2. **로컬 실행은 낮은 지연, 프라이버시·보안, 클라우드 비의존성이라는 이점을 제공한다.**
   - 원문은 로컬 실행의 장점으로 “low latency and high responsiveness”, 데이터 프라이버시·콘텐츠 보안, 클라우드 비의존 및 무료를 열거한다(원문 5행, p.5).
   - 문서의 “모든 데이터는 디바이스에 남는다”, “privacy guaranteed” 등의 표현도 같은 제품 주장에 속한다(원문 8행, p.6).

3. **LLM은 Python `GenieContext` 또는 OpenAI 호환 `GenieAPIService`로 로컬 NPU에서 실행·통합할 수 있다.**
   - `GenieContext`는 Python LLM 파이프라인 배포를 단순화하는 Qualcomm Genie 라이브러리를 감싼 API로 설명되며, Llama 3 초기화 및 질의 코드 예가 제시된다(원문 9, 12–19행, p.10–11).
   - `GenieAPIService`는 로컬 호스트 `http://localhost:8910/v1`에서 OpenAI 클라이언트의 `base_url`로 설정하는 예를 제공한다(원문 19행, p.12). 원문은 endpoint만 바꿔 OpenAI API 지원 제3자 앱을 로컬 NPU 모델로 전환할 수 있고 코드 변경이 필요 없다고 주장한다(원문 11행, p.10).

4. **CV/LVM 배포는 모델 로딩·추론·자원 해제의 세 단계와 대응 API로 간결화되며, Stable Diffusion 계열도 유사한 패턴으로 다룰 수 있다.**
   - 이미지 초해상도 RealESRGan 예로 `QNNContext` 상속, `Inference`, 객체 삭제(`del`)를 포함한 Python 코드가 제공된다(원문 20–21, 22행, p.14–15).
   - 원문은 Stable Diffusion 같은 LVM은 여러 모델을 함께 쓰므로 약간 더 복잡하나 사용 패턴은 대체로 유사하다고 설명한다(원문 21행, p.14).

5. **기존 오픈소스 앱·프레임워크와의 통합 장벽이 낮다.**
   - CV에는 기존 PyTorch 또는 ONNX Runtime 코드의 최소 수정, LLM에는 OpenAI 호환 API, LangFlow에는 endpoint 교체만 필요하다고 주장한다(원문 22–24행, p.16–17).
   - Python, C++, LangFlow를 지원하고, GUI 도구로 Python/WebUI/FletUI/PyQt, Electron, Qt/MFC, WinForms/WPF 등을 사용할 수 있다고 서술한다(원문 8행 p.6; 원문 51–53행 p.44).

6. **자동화 도구와 모델 변환 절차를 통해 빠른 환경 구축·배포를 지원한다.**
   - QAI Launcher의 자동화 스크립트로 네트워크 환경이 좋을 경우 전체 배포를 통상 2시간 내 완료할 수 있다고 주장한다(원문 39–43행, p.34–35).
   - ONNX/DLC를 NPU에서 직접 실행 가능한 QNN context binary로 변환하는 명령·예시를 제시한다(원문 47–51행, p.39–42).

## 3. 보고된 근거·관찰 (주장과 분리)

- **API·구성도 및 코드 예시가 제공된다.** 문서는 QAI AppBuilder가 Qualcomm AI Runtime SDK와 앱 사이에 위치하고 Python API, C++ API, OpenAI Compatible API(GenieAPIService)를 제공하는 아키텍처를 제시한다(원문 9행, p.7). Llama 3용 `GenieContext(config)` 및 `Query(prompt, response)` 코드, 그리고 OpenAI 클라이언트의 로컬 URL 설정 코드가 실제 텍스트로 포함된다(원문 16–19행, p.11–12).
- **CV 코드 예시는 RealESRGan의 입력 전처리→추론→자원 해제→후처리 순서를 보여 준다.** `QNNConfig.Config`, `RealESRGan("realesrgan.bin")`, `Inference`, `del(realesrgan)` 등이 명시된다(원문 22행, p.15). 이는 구현 인터페이스의 예시이지, 화질·속도·메모리 성능의 측정 근거는 아니다.
- **지원 환경과 배포 산출물의 조건이 일부 명시된다.** Python은 x64 및 ARM64, C++ API를 지원하며, 문서는 x64 Python은 확장 생태계가 더 좋고 ARM64 Python은 성능이 더 좋다고 서술한다(원문 27–29행, p.21). 다만 이 성능 비교에 대한 측정 수치·장비·방법은 없다.
- **재현 경로가 링크와 샘플로 안내된다.** 튜토리얼, 사용자 가이드, Python/C++/WebUI/FletUI/GenieAPIService 샘플의 GitHub 경로가 열거된다(원문 25–26행, p.19; 원문 29–32행, p.23). 해당 외부 저장소의 실제 최신 내용이나 실행 가능성은 이 분석 범위에서 검증하지 않았다.
- **지원 도구의 구체적 설치 흐름이 제시된다.** QAI Launcher에는 AppBuilder 설치, LLM 모델 설치, WebUI·GenieAPIService·LangFlow 실행 및 LangFlow 설치를 포함한 6개 스크립트가 나열된다(원문 41–43행, p.35). Pixi 기반 독립 Python 환경과 화면에 표시된 Python `3.12.8`도 제시된다(원문 44–46행, p.37).
- **모델 변환 명령의 예가 있다.** QAIRT `v2.37.1`, QAI AppBuilder `v2.38`, ARM64 Windows 대상 RealESRGan x4plus ONNX의 FP16 변환 예, 그리고 DLC에서 FP16/Int8 binary를 만드는 명령이 제시된다(원문 50–51행, p.40–42). 추출 텍스트에서 일부 명령은 생략 부호 또는 밀집된 레이아웃으로 나타나므로, 완전한 복사·실행 가능한 명령열로 간주할 수 없다.

## 4. 수치·정의·방법론

### 수치 및 버전

| 항목 | 원문에 제시된 값/조건 | 위치 |
|---|---|---|
| 초기 환경 구성 시간 | 좋은 네트워크 환경에서 “usually … within **two hours**”라는 제공자 주장 | 원문 39행, p.34 |
| Python LLM 예시 규모 | “**10 lines** Python code”로 사용 가능하다는 설명 및 코드 예 | 원문 15–19행, p.11 |
| 로컬 LLM 서비스 endpoint | `http://localhost:**8910**`, OpenAI client용 `/v1` base URL | 원문 19행, p.12 |
| QAIRT/QAI AppBuilder 버전 | QAIRT SDK **v2.37.1**, QAI AppBuilder **v2.38** | 원문 50–51행, p.40–42 |
| Pixi 화면의 Python 버전 | Python **3.12.8** (conda-forge 패키징 화면 표시) | 원문 45행, p.37 |
| 변환 정밀도 예 | RealESRGan ONNX→QNN의 **FP16** 예; DLC→binary의 **FP16** 및 **Int8** 예 | 원문 50–51행, p.40–42 |
| ONNX 입력 예 | `input` 차원 **1,3,512,512** | 원문 50행, p.40 |

### 원문 내 정의와 구현 범위

- **LLM:** 문서는 Qwen·Llama 등을 로컬 NPU에서 호출하는 대상으로 든다(원문 6행, p.5; 원문 10행, p.10). 모델 크기, 양자화 수준, 컨텍스트 길이는 일반 LLM 설명에서 정의하지 않는다.
- **CV/LVM:** CV는 computer vision, LVM은 large vision model로 괄호 정의한다. Stable Diffusion은 text-to-image LVM 예이며 여러 모델의 협업을 수반한다고 설명한다(원문 20–21행, p.14).
- **QNN context binary:** ONNX 또는 DLC 형식 모델을 변환해 NPU에서 직접 실행할 수 있는 형식으로 설명된다(원문 47–49행, p.39).
- **`GenieContext` / `GenieAPIService`:** 전자는 Python API를 통한 LLM 호출 방식, 후자는 로컬 LLM을 OpenAI API 방식으로 접근하게 하는 서비스로 제시된다(원문 9–19행, p.10–12).

### 방법론으로서 확인 가능한 것과 확인 불가능한 것

- 문서는 **성능 평가 실험의 방법론**(장비 SKU, NPU 런타임 설정, 모델 체크포인트·정밀도, 프롬프트/이미지 데이터셋, warm-up, 반복 횟수, 지연시간 정의, 처리량, 메모리·전력 측정)을 제시하지 않는다.
- 따라서 “고성능”, “ultra-low latency”, ARM64의 “better performance”, 2시간 배포 등의 표현은 조건 통제된 벤치마크 결과가 아니라 원문의 제품 설명 또는 경험적 안내로만 읽어야 한다(원문 8행 p.6; 원문 27행 p.21; 원문 39행 p.34).

## 5. 원문 한계 및 확인 필요 항목

1. **독립 성능 검증 부재:** 속도, 지연, 정확도/이미지 품질, 메모리, 전력, 비용을 수치로 비교한 벤치마크가 없다. 제시된 성능·편의성 표현은 Qualcomm의 주장으로 한정된다.
2. **“2시간” 및 “10줄”의 적용 조건 불명확:** 네트워크 품질 외에 모델 다운로드 크기, 하드웨어, OS 상태, 사전 설치 여부, 측정 시작·종료 기준이 없다(원문 15–19, 39–43행). 이 수치를 일반적 온보딩 시간이나 운영 성능으로 일반화할 수 없다.
3. **호환성 범위의 확인 필요:** 문서는 Windows 중심이며 Windows·Android·Linux의 멀티플랫폼 지원을 언급하지만(원문 4행, p.5), 각 OS·아키텍처·모델별 지원 행렬과 기능 동등성은 제시하지 않는다. 특히 본문 환경 설정은 Windows x64/ARM64 Python 및 C++에 초점을 둔다(원문 26–29행).
4. **OpenAI 호환성의 정확한 API 범위 미제시:** endpoint 교체만으로 전환 가능하다고 하지만(원문 11, 19행), 지원되는 endpoint, 스트리밍·도구 호출·인증·오류 처리 및 OpenAI SDK 버전 호환 범위는 명시되지 않는다.
5. **모델 가용성·라이선스·배포 조건 미확정:** “수백 개”의 Model Hub 모델 및 Qwen/Llama/Stable Diffusion 사례가 언급되나(원문 6–7행), 모델 목록, 정확한 버전, 접근 조건, 라이선스, 다운로드 용량은 원문에 없다.
6. **변환 예의 재현성 제한:** SDK 경로·Windows ARM64·RealESRGan·FP16/Int8 예는 있으나(원문 50–51행), 추출본의 일부 긴 명령은 잘려 있고 전체 설정 파일·input list·양자화 파라미터의 내용은 제공되지 않는다. 원문 자체도 세부 단계는 QAIRT 문서를 보라고 안내한다(원문 49, 51행).
7. **데모와 운영 환경의 구분:** Image Repair 및 Chat UI는 “For Demo Purpose Only”로 표기된다(원문 33–34행, p.25–27; 원문 38행, p.32). 따라서 이를 생산 환경 준비도·신뢰성의 근거로 해석할 수 없다.
8. **법률·문서 안정성 주의:** 원문은 자료가 “AS IS”이고 완전성·정확성을 보증하지 않으며 변경될 수 있다고 명시한다(원문 55–60행). 또한 수출 통제 정보 가능성을 표기한다(원문 3행 및 57행). 실제 사용 전 최신 문서, 적용 계약·추가 약관, 수출 통제 의무의 확인이 필요하다.
