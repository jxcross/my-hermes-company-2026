#!/usr/bin/env python3
"""outreach-content(아키타입 S) 게이트를 '일부러 깨뜨린 픽스처'로 검증한다 (docs/13 §5).

원본 outreachforge 에서 실측으로 확인한 결함에 **회귀 방어**를 건다:
  · 지어낸 "8배" 가 원자료의 `0.873` 안의 `8` 로 통과(숫자를 문자열로 찾는다)      → ②-1
  · 최상급 주장이 **단어 하나만 겹치면** 통과("first ever to beat human experts")  → ②-2
  · 채널이 하나도 없으면 PASS(공집합 통과 열 번째)                                 → ②-3
  · 과장 5건까지 허용 — 한 문장에 다섯 개를 넣어도 PASS(`HYPE_WARN` 은 죽은 상수)  → ④-1
  · 채널 목록이 하드코딩 — X 만 만드는 미션이 반려된다                             → ③-1(정상)
  · Medium 분량이 영문 word 기준 — 정상 국문 글이 '미달'로 반려                    → ③-2(정상)
"""
import json, os, shutil, subprocess, sys
import yaml

ROOT = "/work/company"
FIX = "/tmp/ofg"
GATES = os.path.join(ROOT, "scripts", "gates")

LAUNCH = "2026-09-01"
KO = "이 연구는 국내 산업 데이터를 대상으로 제안 기법의 실효성을 정량 지표로 검증했다. "


def w(rel, s):
    p = os.path.join(FIX, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(s)


def twitter(n=5, hype="", extra=""):
    posts = [f"## {i}/{n}\n" for i in range(1, n + 1)]
    posts[0] += f"국내 산업 데이터에서 정확도 0.873 을 얻었다 [e1]. {hype}\n"
    posts[1] += "재현 절차를 공개해 누구나 따라 돌릴 수 있게 했다 [e2].\n"
    posts[2] += f"기존 대비 3.2배 빠르다 [e3]. {extra}\n"
    for i in range(3, n - 1):
        posts[i] += "설계와 한계를 블로그에 자세히 적었다.\n"
    posts[n - 1] += "자세한 내용은 https://arxiv.org/abs/2601.01234 #MLSys\n"
    return "---\nstage: channel\n---\n" + "\n".join(posts)


def medium(n_para=4, sent=22):
    body = "\n\n".join(f"## 절 {i}\n\n" + KO * sent for i in range(1, n_para + 1))
    return ("---\nstage: channel\n---\n# 국내 산업 데이터 검증 이야기\n\n"
            "> Hero image hint: 정확도 비교 막대그림\n\n"
            "정확도 0.873 을 얻었다 [e1]. 재현 절차도 공개했다 [e2].\n\n" + body)


README = """---
stage: channel
---
# README 갱신 (PR diff)

+ ## Validation on domestic industrial data
+ 국내 산업 데이터에서 정확도 0.873 을 달성했습니다 [e1].
+ We release the full reproduction procedure [e2].
+ 재현 절차: `make reproduce`
+ See the paper for details.

```bibtex
@article{kim2026val, title={Validation on industrial data}, year={2026}}
```
"""

CHECKLIST = f"""# 발신 체크리스트

- T-0 ({LAUNCH}): GitHub 릴리스 태그 확정
- T+0: X 스레드 게시
- T+1일: 블로그 발행
- T+2일: README PR

⚠️ 이 파이프라인은 게시하지 않는다. 사람이 최종 확인 후 직접 올린다.
정정 절차: 오류 발견 시 해당 채널에 정정 글을 올리고 원 글에 링크한다.
"""


def build(channels=("twitter", "medium", "readme"), basis="arxiv", ref="2601.01234",
          patent="none", embargo="", mode="local_only", launch=LAUNCH):
    shutil.rmtree(FIX, ignore_errors=True)
    os.makedirs(FIX)
    tpl = yaml.safe_load(open(os.path.join(ROOT, "templates", "outreach-content.yaml"),
                              encoding="utf-8"))
    pol = tpl["policy"]
    pol["publication_policy"]["mode"] = mode
    json.dump({"policy": pol}, open(os.path.join(FIX, "pipeline.json"), "w"),
              ensure_ascii=False)

    w("SCOPE.md", f"""---
channels: [{", ".join(channels)}]
release_basis: {basis}
release_ref: {ref}
patent_status: {patent}
launch_date: {launch}
embargo_until: {embargo}
---
# 발신 스펙
""")
    # 원자료 — claim 의 값이 여기에 실재해야 한다
    w("_private/source/results.md",
      "# 결과\n정확도 0.873 (baseline 0.812).\n처리 속도는 baseline 대비 3.2배 빨랐다.\n"
      "재현 절차는 reproduce.sh 로 제공한다.\n")
    w("_private/source.md", """# 발신 주장

```evidence
- id: e1
  grade: verified
  value: 0.873
  locator: _private/source/results.md
  statement: 국내 산업 데이터에서 정확도 0.873 을 얻었다
- id: e2
  grade: verified
  locator: _private/source/results.md
  statement: 재현 절차를 공개했다
- id: e3
  grade: verified
  value: 3.2
  locator: _private/source/results.md
  statement: 기존 대비 3.2배 빠르다
```
""")
    w("_private/hook.md", "# 후킹\n한 줄 요약: 국내 데이터에서 검증하고 재현 절차를 공개했다.\n")
    gen = {"twitter": twitter(), "medium": medium(), "readme": README}
    for ch in channels:
        w(f"_private/channels/{ch}.md", gen[ch])
    w("_private/visuals.md", """# 그림 브리프

```visuals
- id: v1
  channel: twitter
  description: 정확도 비교 막대그림
  source: _private/source/figures/fig2.png
  license: own
```
""")
    w("_private/cite-pack.md", "# 인용팩\nc1 → twitter 1/5 · medium 도입부\nc3 → twitter 3/5\n")
    w("_private/launch-checklist.md", CHECKLIST)
    w("report/summary.md", "# 발신 요약\n채널 3종을 만들었고 게시는 사람이 한다.\n")


def run(gate, draft="."):
    r = subprocess.run([sys.executable, os.path.join(GATES, f"{gate}.py"),
                        "--policy", os.path.join(FIX, "pipeline.json"),
                        "--sources", os.path.join(FIX, "raw", "sources.yaml"),
                        "--draft", os.path.join(FIX, draft)],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


DRAFTS = {"claim_provenance": ".", "channel_format": ".", "release_readiness": ".",
          "outreach_tone": ".", "evidence_grade": "_private/channels",
          "secret_redaction": "_private/channels"}


def expect(label, gate, want, show=False, draft=None):
    rc, out = run(gate, draft or DRAFTS[gate])
    print(f"{'OK ' if rc == want else '‼️ '}{label:62s} exit={rc} (기대 {want})")
    if rc != want or show:
        print("      " + "\n      ".join(out.splitlines()[-8:]))
    return rc == want


def patch(path, old, new, count=1):
    p = os.path.join(FIX, path)
    t = open(p, encoding="utf-8").read()
    assert old in t, f"픽스처 치환 실패: {old!r} not in {path}"
    open(p, "w", encoding="utf-8").write(t.replace(old, new, count))


results = []
print("── ① 정상 픽스처: 6게이트 모두 PASS ──")
build()
results.append(expect("정상 · claim_provenance(full)", "claim_provenance", 0, show=True))
results.append(expect("정상 · channel_format", "channel_format", 0, show=True))
results.append(expect("정상 · outreach_tone", "outreach_tone", 0))
results.append(expect("정상 · release_readiness", "release_readiness", 0, show=True))
results.append(expect("정상 · evidence_grade(G 재사용)", "evidence_grade", 0))
results.append(expect("정상 · secret_redaction(L 재사용)", "secret_redaction", 0))

print("\n── ② claim_provenance: 숫자를 문자열로 찾던 하드게이트 ──")
build(); patch("_private/channels/twitter.md", "기존 대비 3.2배 빠르다 [e3]",
               "기존 대비 8배 빠르다 [e3]")
results.append(expect("**원본 회귀: 지어낸 '8배'(원자료의 0.873 안의 8)**",
                      "claim_provenance", 1, show=True))

build(); patch("_private/channels/twitter.md",
               "재현 절차를 공개해 누구나 따라 돌릴 수 있게 했다 [e2].",
               "This is the first ever method to beat human experts.")
results.append(expect("**원본 회귀: 근거 없는 최상급('first ever')**",
                      "claim_provenance", 1, show=True))

build(); shutil.rmtree(os.path.join(FIX, "_private/channels"))
os.makedirs(os.path.join(FIX, "_private/channels"))
results.append(expect("**원본 회귀: 채널이 하나도 없다**", "claim_provenance", 1, show=True))

build(); patch("_private/channels/medium.md", "정확도 0.873 을 얻었다 [e1]",
               "정확도 0.941 을 얻었다 [e1]")
results.append(expect("인용한 claim 의 값과 채널의 수치가 다르다", "claim_provenance", 1, show=True))

build(); patch("_private/channels/twitter.md", "정확도 0.873 을 얻었다 [e1]",
               "정확도 0.873 을 얻었다")
results.append(expect("수치에 claim 인용이 없다", "claim_provenance", 1))

build(); patch("_private/channels/twitter.md", "[e1]", "[e9]")
results.append(expect("존재하지 않는 claim 인용(환각)", "claim_provenance", 1))

build(); patch("_private/source.md", "  value: 0.873\n", "  value: 0.999\n")
results.append(expect("claim 의 값이 원자료에 없다(지어낸 수치)", "claim_provenance", 1, show=True))

build(); patch("_private/source.md", "  locator: _private/source/results.md\n", "", 1)
results.append(expect("claim 에 locator 가 없다", "claim_provenance", 1))

build(); patch("_private/source.md", "locator: _private/source/results.md",
               "locator: _private/source/nope.md", 1)
results.append(expect("locator 가 실재하지 않는다", "claim_provenance", 1))

build(); shutil.rmtree(os.path.join(FIX, "_private/channels"))
results.append(expect("설계 방어: source 모드(채널이 아직 없다)", "claim_provenance", 0, show=True))

print("\n── ③ channel_format: 하드코딩된 채널 목록과 영문 분량 기준 ──")
build(channels=("twitter",))
results.append(expect("**원본 회귀(정상): X 스레드만 만드는 미션**", "channel_format", 0, show=True))

build(); w("_private/channels/medium.md", medium(n_para=4, sent=20))
results.append(expect("**원본 회귀(정상): 국문 1천 어절대 글**(원본은 1500 미만이라 반려했다)",
                      "channel_format", 0, show=True))

build(); os.remove(os.path.join(FIX, "_private/channels/medium.md"))
results.append(expect("선언한 채널의 산출물이 없다", "channel_format", 1))

build(); w("_private/channels/linkedin.md", "# 선언하지 않은 채널\n")
results.append(expect("선언하지 않은 채널을 만들었다(승인 범위 밖)", "channel_format", 1, show=True))

build(); w("_private/channels/twitter.md", twitter(n=3))
results.append(expect("트윗 개수가 규격 밖", "channel_format", 1))

build(); patch("_private/channels/twitter.md", "## 3/5", "## 4/5")
results.append(expect("트윗 번호가 어긋난다", "channel_format", 1))

build(); patch("_private/channels/twitter.md",
               "자세한 내용은 https://arxiv.org/abs/2601.01234 #MLSys", "끝.")
results.append(expect("마지막 트윗에 CTA 가 없다", "channel_format", 1))

build(); patch("_private/channels/twitter.md", "국내 산업 데이터에서 정확도 0.873 을 얻었다 [e1].",
               "국내 산업 데이터에서 정확도 0.873 을 얻었다 [e1]. " + KO * 12)
results.append(expect("트윗이 280자를 넘는다", "channel_format", 1, show=True))

build(); w("_private/channels/medium.md", medium(n_para=8, sent=40))
results.append(expect("블로그 분량 초과 + 소제목 초과", "channel_format", 1))

build(); patch("_private/channels/medium.md", "> Hero image hint: 정확도 비교 막대그림", "")
results.append(expect("블로그에 대표 이미지 힌트가 없다", "channel_format", 1))

build(); patch("_private/channels/readme.md", "```bibtex\n@article{kim2026val, title={Validation on industrial data}, year={2026}}\n```", "")
results.append(expect("README 에 BibTeX 가 없다", "channel_format", 1))

build(); patch("SCOPE.md", "channels: [twitter, medium, readme]\n", "")
results.append(expect("설계 방어: SCOPE 선언이 없으면 정책 기본값을 쓴다", "channel_format", 0))

build(); patch("SCOPE.md", "channels: [twitter, medium, readme]\n", "")
pol = json.load(open(os.path.join(FIX, "pipeline.json")))
pol["policy"]["channel_policy"].pop("channels")
json.dump(pol, open(os.path.join(FIX, "pipeline.json"), "w"), ensure_ascii=False)
results.append(expect("채널 선언이 어디에도 없다 → fail-closed", "channel_format", 2))

print("\n── ④ outreach_tone: 과장 5건까지 허용하던 임계 ──")
build(); w("_private/channels/twitter.md",
           twitter(hype="획기적이고 혁명적인 놀라운 breakthrough 이며 전례없는 성과다."))
results.append(expect("**원본 회귀: 한 문장에 과장 5건**", "outreach_tone", 1, show=True))

build(); w("_private/channels/twitter.md", twitter(hype="놀라운 결과다."))
results.append(expect("설계 방어: 과장 1건은 통과(게이트가 목적과 싸우지 않는다)",
                      "outreach_tone", 0, show=True))

build(); w("_private/channels/twitter.md", twitter(hype="놀라운 획기적 결과다."))
results.append(expect("과장 2건 > 임계 1", "outreach_tone", 1))

build(); patch("_private/channels/medium.md", "정확도 0.873 을 얻었다 [e1].",
               "기존 연구는 쓸모없다는 것을 보였다 [e1].")
results.append(expect("경쟁 비하 표현", "outreach_tone", 1, show=True))

build(); patch("_private/channels/twitter.md", "## 1/5\n", "## 1/5\n🎉🎊🚀🔥 ")
results.append(expect("이모지 상한 초과", "outreach_tone", 1))

build(); patch("_private/channels/twitter.md",
               "자세한 내용은 https://arxiv.org/abs/2601.01234 #MLSys",
               "자세한 내용은 https://arxiv.org/abs/2601.01234 #MLSys #AI #ML #DL #NLP")
results.append(expect("해시태그 상한 초과", "outreach_tone", 1))

build(); patch("_private/channels/readme.md", "See the paper for details.",
               "AMAZING RESULTS INDEED HERE")
results.append(expect("전부 대문자 낱말 남용", "outreach_tone", 1))

print("\n── ⑤ evidence_grade 재사용(G): 예비 결과를 확정처럼 말하는 것 ──")
build(); patch("_private/source.md", "- id: e1\n  grade: verified", "- id: e1\n  grade: preliminary")
results.append(expect("**예비 등급 claim 인용에 유보 표현이 없다**", "evidence_grade", 1, show=True))

build()
patch("_private/source.md", "- id: e1\n  grade: verified", "- id: e1\n  grade: preliminary")
patch("_private/channels/twitter.md", "정확도 0.873 을 얻었다 [e1].",
      "정확도 0.873 을 얻었다 [e1]. 다만 예비 결과이며 추가 검증이 필요하다.")
patch("_private/channels/medium.md", "정확도 0.873 을 얻었다 [e1].",
      "정확도 0.873 을 얻었다 [e1]. 이는 예비 결과로 추가 검증이 필요하다.")
patch("_private/channels/readme.md", "국내 산업 데이터에서 정확도 0.873 을 달성했습니다 [e1].",
      "국내 산업 데이터에서 정확도 0.873 을 달성했습니다 [e1]. (예비 결과 · 추가 검증 예정)")
results.append(expect("설계 방어: 유보 표현을 붙이면 통과", "evidence_grade", 0, show=True))

print("\n── ⑥ release_readiness: 원본에 이 질문이 없다 ──")
build(basis="")
results.append(expect("**공개 근거 선언이 없다**(원본은 묻지 않는다)", "release_readiness", 1, show=True))

build(patent="planned")
results.append(expect("**출원 예정 발명 — 공개하면 신규성을 잃는다**",
                      "release_readiness", 1, show=True))

build(embargo="2026-10-01")
results.append(expect("엠바고 해제일이 발신일보다 늦다", "release_readiness", 1, show=True))

build(basis="owner_approval", ref="sam-2026-08", mode="repo_commit")
results.append(expect("미공개 자료인데 커밋 범위가 repo_commit", "release_readiness", 1, show=True))

build(mode="repo_commit")
results.append(expect("설계 방어: arXiv 공개 자료면 repo_commit 허용", "release_readiness", 0))

build(ref="")
results.append(expect("공개 근거의 실체(release_ref)가 없다", "release_readiness", 1))

build(patent="")
results.append(expect("특허 상태 선언이 없다", "release_readiness", 1))

build(launch="")
results.append(expect("발신일 선언이 없다", "release_readiness", 1))

build(); patch("_private/channels/twitter.md", "https://arxiv.org/abs/2601.01234",
               "https://example.com/TBD")
results.append(expect("플레이스홀더가 남았다(그대로 게시되면 사고)", "release_readiness", 1, show=True))

build(); patch("_private/launch-checklist.md",
               "⚠️ 이 파이프라인은 게시하지 않는다. 사람이 최종 확인 후 직접 올린다.", "")
results.append(expect("체크리스트에 '우리는 게시하지 않는다' 고지가 없다",
                      "release_readiness", 1))

build(); patch("_private/launch-checklist.md", f"T-0 ({LAUNCH})", "T-0 (미정일)")
results.append(expect("체크리스트에 발신일이 없다", "release_readiness", 1))

build(); patch("_private/visuals.md", "  license: own\n", "")
results.append(expect("그림에 라이선스 표기가 없다(남의 그림 무단 사용)",
                      "release_readiness", 1, show=True))

build(); patch("_private/visuals.md", "```visuals", "```figures")
results.append(expect("그림 브리프 블록이 없다", "release_readiness", 1))

build(); os.remove(os.path.join(FIX, "_private/launch-checklist.md"))
results.append(expect("발신 체크리스트가 없다", "release_readiness", 1))

print("\n── ⑦ secret_redaction 재사용(L) ──")
build(); patch("_private/channels/readme.md", "+ 재현 절차: `make reproduce`",
               "+ 재현 절차: `export API_KEY=sk-proj-Ab3dEf5GhIj7KlMn9OpQrStUvWxYz012345678` && make reproduce")
results.append(expect("발신물 예제 코드에 API 키가 박혔다", "secret_redaction", 1, show=True))

n_ok = sum(1 for r in results if r)
print(f"\n{n_ok}/{len(results)} 통과")
sys.exit(0 if n_ok == len(results) else 1)
