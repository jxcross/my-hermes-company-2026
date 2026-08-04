#!/usr/bin/env python3
"""code-docs 3게이트를 '일부러 깨뜨린 픽스처'로 검증한다 (docs/13 §5).
특히 원본 api_coverage 가 100% PASS 를 준 케이스를 우리 게이트가 FAIL 하는지 본다."""
import json, os, shutil, subprocess, sys
import yaml

ROOT = "/work/company"
FIX = "/tmp/df"
CODE = "/tmp/df/src"
GATES = os.path.join(ROOT, "scripts", "gates")

DOC_BODY = ("이 함수는 주어진 경로의 파일을 읽어 심볼 목록을 반환한다. "
            "실패 시 빈 목록을 돌려주며 예외를 던지지 않는다. 예제는 아래를 보라.")


def build():
    shutil.rmtree(FIX, ignore_errors=True)
    os.makedirs(os.path.join(FIX, "docs"))
    os.makedirs(CODE)

    tpl = yaml.safe_load(open(os.path.join(ROOT, "templates", "code-docs.yaml"), encoding="utf-8"))
    json.dump({"policy": tpl["policy"]}, open(os.path.join(FIX, "pipeline.json"), "w"), ensure_ascii=False)

    w = lambda p, s: open(os.path.join(FIX, p), "w", encoding="utf-8").write(s)
    w("SCOPE.md", "---\ncodebase: src\nlanguages: [python]\ndoc_types: [api-ref, architecture]\n---\n")

    # 실제 코드 — AST 가 여기서 진실을 읽는다
    w("src/core.py", '''"""핵심 모듈."""


def parse_tree(node, depth=0):
    return []


def get_config(path):
    return {}


def _private_helper(x):
    return x


class Engine:
    def run(self, task):
        return task

    def _secret(self):
        pass
''')

    w("symbols.md", """# 심볼

```functions
- name: parse_tree
  signature: parse_tree(node, depth=0)
  module: core.py
- name: get_config
  signature: get_config(path)
  module: core.py
```

```classes
- name: Engine
  signature: Engine()
- name: Engine.run
  signature: Engine.run(task)
```
""")
    w("docs/api-ref.md", f"""# API Reference

### parse_tree(node, depth=0)
{DOC_BODY}

### get_config(path)
설정 파일을 읽어 딕셔너리로 돌려준다. 파일이 없으면 빈 딕셔너리를 반환하며 예외는 없다.

### Engine
실행 엔진 클래스다. 태스크를 받아 순서대로 처리하며 상태를 내부에 보관하지 않는다.

### Engine.run(task)
태스크 하나를 실행하고 결과를 반환한다. 자세한 흐름은 [아키텍처](architecture.md#구조-개요)를 보라.
""")
    w("docs/architecture.md", """# 아키텍처

## 구조 개요
core 모듈이 전부다. 자세한 API 는 [레퍼런스](api-ref.md#parse_treenode-depth0)를 보라.

## 의존성
외부 의존성은 없다. [엔진](api-ref.md#engine)이 진입점이다.

## 결정
설계 결정은 [구조 개요](#구조-개요)에 정리했다.
""")


def run(gate, draft):
    r = subprocess.run(["python3", os.path.join(GATES, f"{gate}.py"),
                        "--policy", os.path.join(FIX, "pipeline.json"),
                        "--sources", os.path.join(FIX, "raw", "sources.yaml"),
                        "--draft", os.path.join(FIX, draft)],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


DRAFTS = {"symbol_truth": "symbols.md", "api_coverage": "docs", "doc_links": "docs"}


def expect(label, gate, want, show=False):
    rc, out = run(gate, DRAFTS[gate])
    print(f"{'OK ' if rc == want else '‼️ '}{label:52s} exit={rc} (기대 {want})")
    if rc != want or show:
        print("      " + "\n      ".join(out.splitlines()[-7:]))
    return rc == want


def patch(path, old, new):
    p = os.path.join(FIX, path)
    t = open(p, encoding="utf-8").read()
    assert old in t, f"픽스처 치환 실패: {old!r} not in {path}"
    open(p, "w", encoding="utf-8").write(t.replace(old, new))


results = []
print("── ① 정상 픽스처: 3게이트 모두 PASS ──")
build()
results.append(expect("정상 · symbol_truth", "symbol_truth", 0, show=True))
results.append(expect("정상 · api_coverage", "api_coverage", 0, show=True))
results.append(expect("정상 · doc_links", "doc_links", 0, show=True))

print("\n── ② symbol_truth 를 깨뜨린다 ──")
build(); patch("symbols.md", "- name: get_config\n  signature: get_config(path)",
               "- name: load_settings\n  signature: load_settings(path)")
results.append(expect("코드에 없는 심볼 선언(환각)", "symbol_truth", 1))

build(); patch("symbols.md", "signature: parse_tree(node, depth=0)",
               "signature: parse_tree(node, depth=0, strict=True)")
results.append(expect("시그니처 불일치", "symbol_truth", 1))

build(); patch("symbols.md", """- name: get_config
  signature: get_config(path)
  module: core.py
""", "")
patch("symbols.md", "- name: Engine.run\n  signature: Engine.run(task)\n", "")
results.append(expect("과소 선언(2/4=50% < 80%) — 원본에 없던 검사", "symbol_truth", 1))

build(); patch("symbols.md", "- name: parse_tree", "- name: _private_helper")
results.append(expect("비공개 심볼 선언 + 공개 누락", "symbol_truth", 1))

print("\n── ③ api_coverage 를 깨뜨린다 ──")
build(); patch("docs/api-ref.md", f"### parse_tree(node, depth=0)\n{DOC_BODY}\n\n", "")
patch("docs/architecture.md", "[레퍼런스](api-ref.md#parse_treenode-depth0)", "[레퍼런스](api-ref.md)")
results.append(expect("심볼 1개 미문서화(3/4=75% < 90%)", "api_coverage", 1))

build(); patch("docs/api-ref.md", DOC_BODY, "TODO")
patch("docs/architecture.md", "[레퍼런스](api-ref.md#parse_treenode-depth0)", "[레퍼런스](api-ref.md)")
results.append(expect("제목만 있고 본문 없음(TODO)", "api_coverage", 1))

print("\n── ④ doc_links 를 깨뜨린다 ──")
build(); patch("docs/architecture.md", "[레퍼런스](api-ref.md#parse_treenode-depth0)",
               "[레퍼런스](api-ref.md#없는앵커)")
results.append(expect("존재하지 않는 앵커", "doc_links", 1))

build(); patch("docs/api-ref.md", "[아키텍처](architecture.md#구조-개요)",
               "[아키텍처](../없는곳/architecture.md#구조-개요)")
results.append(expect("존재하지 않는 파일 경로 — 원본은 basename 만 봐서 통과", "doc_links", 1))

build(); patch("docs/architecture.md", "[레퍼런스](api-ref.md#parse_treenode-depth0)를 보라", "")
patch("docs/architecture.md", "[엔진](api-ref.md#engine)이 진입점이다", "엔진이 진입점이다")
patch("docs/api-ref.md", "자세한 흐름은 [아키텍처](architecture.md#구조-개요)를 보라.", "")
results.append(expect("상호 링크 0개 < 3개", "doc_links", 1))

print("\n── ⑤ 원본 결함의 회귀 방어 ──")
build()
# 원본이 100% PASS 를 준 시나리오: 부분 문자열만 스치는 문서
patch("docs/api-ref.md", f"### parse_tree(node, depth=0)\n{DOC_BODY}",
      "### 개요\n현재 parse_tree_node 를 running 상태에서 get_configuration 과 함께 쓴다. "
      "자세한 것은 추후 작성 예정이며 지금은 초안이다.")
patch("docs/architecture.md", "[레퍼런스](api-ref.md#parse_treenode-depth0)", "[레퍼런스](api-ref.md)")
results.append(expect("부분 문자열 스침을 문서화로 세지 않는다", "api_coverage", 1))

build()
with open(os.path.join(FIX, "docs/architecture.md"), "a", encoding="utf-8") as f:
    f.write("\n![다이어그램](graph.png)\n\n예제:\n```md\n[깨진링크](없는파일.md)\n```\n")
results.append(expect("이미지·코드블록 안 링크는 대상이 아니다", "doc_links", 0))

print(f"\n{sum(results)}/{len(results)} 통과")
sys.exit(0 if all(results) else 1)
