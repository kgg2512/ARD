#!/usr/bin/env python3
"""
Universal Git Sync — 원격(클라우드 클로드)·로컬(노트북 클로드) 단절 방지.

문제: 원격은 세션 브랜치에 push, 로컬은 master에 있어 서로 못 봄. GitHub이 유일한 다리인데
      양쪽이 다른 브랜치를 보면 다리가 끊긴다.
해법: 모든 레포에서 'trunk(origin 기본 브랜치, 보통 master)'를 단일 진실로 삼고,
      세션 시작 시 자동 fetch+동기화, 종료 시 미푸시 경고. 모든 레포에 글로벌 훅으로 적용.

안전 원칙(절대): force 금지 · 더티 트리 자동 머지 금지 · 블라인드 auto-push 금지.
  → 읽기 위주(fetch) + 클린 트리에서 ff-only pull만. 위험하면 손대지 않고 '알림'만.

훅 등록:
  SessionStart →  python git_sync.py --mode start   (최신으로 당겨오기)
  Stop         →  python git_sync.py --mode stop    (미푸시 경고)
"""
import json
import os
import subprocess
import sys


def git(args, cwd=None):
    try:
        r = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True, timeout=30)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except Exception as e:
        return 1, "", str(e)


def repo_root():
    code, out, _ = git(["rev-parse", "--show-toplevel"])
    return out if code == 0 else None


def trunk(root):
    code, out, _ = git(["symbolic-ref", "--short", "refs/remotes/origin/HEAD"], root)
    if code == 0 and out:
        return out.split("/")[-1]
    for b in ("master", "main"):
        code, _, _ = git(["rev-parse", "--verify", f"origin/{b}"], root)
        if code == 0:
            return b
    return "master"


def clean_tree(root):
    code, out, _ = git(["status", "--porcelain"], root)
    return code == 0 and out == ""


def cur_branch(root):
    code, out, _ = git(["rev-parse", "--abbrev-ref", "HEAD"], root)
    return out if code == 0 else "?"


def count(root, rng):
    code, out, _ = git(["rev-list", "--count", rng], root)
    return int(out) if code == 0 and out.isdigit() else 0


def emit_session(msg):
    print(json.dumps(
        {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": msg}},
        ensure_ascii=False))


def mode_start():
    root = repo_root()
    if not root:
        return
    git(["fetch", "origin", "--quiet"], root)
    t = trunk(root)
    cb = cur_branch(root)
    notes = []

    if cb == t:
        behind = count(root, f"HEAD..origin/{t}")
        if behind == 0:
            return  # 이미 최신 → 조용히
        if clean_tree(root):
            code, out, err = git(["pull", "--ff-only", "origin", t], root)
            if code == 0:
                notes.append(f"⬇️ {t}를 origin 최신으로 {behind}커밋 당겨옴(동기화 완료).")
            else:
                head = (err.splitlines() or [""])[0]
                notes.append(f"⚠️ {t} ff-pull 실패(분기 가능). 수동 확인: {head}")
        else:
            notes.append(f"⚠️ {t}가 origin보다 {behind}커밋 뒤짐인데 작업트리에 변경 있음 "
                         f"→ 커밋/스태시 후 'git pull --ff-only origin {t}'.")
    else:
        behind = count(root, f"HEAD..origin/{t}")
        notes.append(f"ℹ️ 현재 브랜치 '{cb}' ≠ trunk '{t}'. 단일 브랜치 원칙: 작업을 {t}로 수렴시켜라 "
                     f"(예: git checkout {t} && git merge origin/{cb}). {t} 대비 {behind}커밋 뒤짐.")

    if notes:
        emit_session(f"[Git Sync] {os.path.basename(root)}: " + " ".join(notes))


def mode_stop():
    root = repo_root()
    if not root:
        return
    cb = cur_branch(root)
    # 업스트림 대비 미푸시 커밋(@{u})
    code, out, _ = git(["log", "--oneline", "@{u}.."], root)
    if code == 0 and out:
        n = len(out.splitlines())
        print(f"[Git Sync] {os.path.basename(root)}: 미푸시 커밋 {n}개({cb}). "
              f"`git push` 후 종료 권장 — 안 하면 다른 기기(노트북/폰)에서 못 봄.")
    elif code != 0:
        # 업스트림 미설정 브랜치
        code2, out2, _ = git(["log", "--oneline", "-1"], root)
        if out2:
            print(f"[Git Sync] {os.path.basename(root)}: 브랜치 '{cb}' 업스트림 미설정. "
                  f"`git push -u origin {cb}` (또는 trunk로 수렴) 후 종료 권장.")


def main():
    mode = "start"
    if "--mode" in sys.argv:
        try:
            mode = sys.argv[sys.argv.index("--mode") + 1]
        except IndexError:
            pass
    try:
        sys.stdin.read()
    except Exception:
        pass
    if mode == "stop":
        mode_stop()
    else:
        mode_start()
    return 0


if __name__ == "__main__":
    sys.exit(main())
