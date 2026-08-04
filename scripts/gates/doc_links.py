#!/usr/bin/env python3
"""
객관 게이트: 문서 간 링크·앵커 무결성
=======================================
문서 묶음 안의 상호 링크가 실제 파일과 제목을 가리키는지 LLM 없이 검사한다.
출처: other_projects/harness-templates/.../docforge/scripts/doc_link_validator.py
      (원본은 Stage 6 보조 도구였지만 exit code 로 판정하므로 **게이트다** — docs/13 §2④)

이식하며 고친 것 (docs/13 §5)
  · **이미지가 깨진 링크로 잡혔다** — `![alt](img.png)` 도 링크 정규식에 걸려 `.md` 가
    아니라는 이유로 broken 이 됐다. 이미지·비마크다운 대상은 건너뛴다.
  · **앵커 slug 가 GitHub 규칙과 달랐다** — 원본 `[^\\w-]+ → '-'` 는 `parse(x)` 를
    `parse-x-` 로 만든다(GitHub 은 `parsex`). 정상 앵커가 깨진 것으로 나온다.
    → 구두점은 **삭제**하고 공백만 하이픈으로 바꾸는 GitHub 규칙으로 교체.
  · **디렉터리를 무시했다** — `Path(file_part).name` 만 봐서 `../없는곳/api-ref.md` 도
    통과했다. 실제 경로로 확인한다.
  · **링크가 하나도 없어도 PASS** — 상호 링크가 목적인 단계에서 0건은 실패다.
    `min_cross_links` 로 하한을 둔다.

입력 (gate_keeper 규약)
  --policy  <path>  : pipeline.json (policy.link_policy)
  --sources <path>  : 미사용(규약상 전달됨)
  --draft   <path>  : docs/ 디렉터리

정책 필드(link_policy)
  min_cross_links (기본 0) · check_anchors (기본 true) · allow_external (기본 true)

exit: 0 PASS · 1 FAIL · 2 usage/입력없음(fail-closed)
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML 필요", file=sys.stderr); sys.exit(2)

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
# ⚠️ 앞의 `!` 를 배제한다 — 이미지는 문서 간 링크가 아니다(원본은 이걸 깨진 링크로 셌다)
LINK_RE = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)
CODE_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)


def load_policy(path: str) -> dict:
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        d = json.loads(text)
        pol = d.get("policy", d)
        return pol.get("link_policy", {}) or {}
    m = FRONTMATTER_RE.match(text)
    d = yaml.safe_load(m.group(1)) if m else yaml.safe_load(text)
    return (d or {}).get("link_policy", {}) or {}


def slug(s: str) -> str:
    """GitHub 앵커 규칙: 소문자 → 구두점 **삭제** → 공백을 하이픈으로.
    원본처럼 구두점을 하이픈으로 바꾸면 `parse(x)` 가 `parse-x-` 가 돼 정상 앵커가 깨진다."""
    s = re.sub(r"`|<[^>]+>", "", s).strip().lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    return re.sub(r"\s+", "-", s).strip("-")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--sources", default=None, help="미사용(gate_keeper 규약상 전달됨)")
    ap.add_argument("--draft", default=None, help="docs/ 디렉터리")
    args = ap.parse_args()

    if not args.draft or not os.path.isdir(args.draft):
        print(f"FAIL(usage): --draft(docs/ 디렉터리) 필요 — fail-closed", file=sys.stderr); return 2
    try:
        policy = load_policy(args.policy)
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"FAIL(usage): {e} — fail-closed", file=sys.stderr); return 2

    docs = {f: os.path.join(args.draft, f)
            for f in sorted(os.listdir(args.draft)) if f.endswith(".md")}
    if not docs:
        print(f"FAIL(usage): 문서가 없다({args.draft}) — fail-closed", file=sys.stderr); return 2

    min_links = int(policy.get("min_cross_links", 0))
    check_anchors = bool(policy.get("check_anchors", True))
    allow_external = bool(policy.get("allow_external", True))

    texts, anchors = {}, {}
    for name, path in docs.items():
        t = open(path, encoding="utf-8").read()
        texts[name] = t
        anchors[name] = {slug(m.group(1)) for m in HEADING_RE.finditer(t)}

    broken, n_links, n_cross = [], 0, 0
    for name, text in texts.items():
        body = CODE_FENCE_RE.sub(" ", text)          # 코드 예제 안의 링크는 검사 대상이 아니다
        for m in LINK_RE.finditer(body):
            url = m.group(2)
            if url.startswith(("http://", "https://", "mailto:")):
                n_links += 1
                if not allow_external:
                    broken.append((name, url, "외부 링크 금지 정책"))
                continue
            file_part, _, anchor = url.partition("#")
            n_links += 1
            if file_part:
                if not file_part.endswith(".md"):
                    continue                          # 이미지·코드 파일 링크는 대상이 아니다
                target = os.path.normpath(os.path.join(os.path.dirname(docs[name]), file_part))
                tname = os.path.basename(target)
                if not os.path.isfile(target):
                    broken.append((name, url, f"파일 없음: {file_part}"))
                    continue
                if tname in docs and tname != name:
                    n_cross += 1
                if anchor and check_anchors:
                    if tname not in anchors:
                        continue                      # 묶음 밖 파일의 앵커는 확인 불가
                    if slug(anchor) not in anchors[tname]:
                        broken.append((name, url, f"앵커 없음: #{anchor}"))
            elif anchor and check_anchors:
                if slug(anchor) not in anchors[name]:
                    broken.append((name, url, f"같은 문서 앵커 없음: #{anchor}"))

    print(f"문서 {len(docs)}건 · 링크 {n_links}개 · 문서 간 상호 링크 {n_cross}개 "
          f"(하한 {min_links})")

    fail = False
    if broken:
        print(f"FAIL: 깨진 링크 {len(broken)}건")
        for name, url, why in broken[:8]:
            print(f"       · {name}: {url} — {why}")
        fail = True
    if n_cross < min_links:
        print(f"FAIL: 문서 간 상호 링크 {n_cross}개 < {min_links}개 — 상호 참조가 없는 "
              f"문서 묶음은 조각난 문서다")
        fail = True
    if not fail:
        print("  ✓ 링크·앵커 정상")
    print("VERDICT:", "FAIL" if fail else "PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
