#!/usr/bin/env python3
"""
Influencer Monitor — Claude Code 스킬/MCP 자동 탐지 & 설치
대상 YouTube 채널의 신규 영상을 분석해서 관련 스킬/MCP를 자동 설치한다.
SessionStart 시 하루 1회 실행.
"""

import json
import os
import re
import subprocess
import sys
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path

CLAUDE_DIR = Path.home() / ".claude"
DATA_DIR = CLAUDE_DIR / "data"
STATE_FILE = DATA_DIR / "influencer_monitor_state.json"
CHANNELS_FILE = DATA_DIR / "influencer_channels.json"
LOG_FILE = DATA_DIR / "influencer_monitor_log.jsonl"
CHECK_INTERVAL_HOURS = 24

# 스킬/MCP 감지 패턴
SKILL_INSTALL_PATTERNS = [
    r'npx skills add\s+([\w@/.-]+)',
    r'skills\.sh/([\w@/.-]+/[\w@/.-]+)',
]

MCP_NPM_PATTERNS = [
    r'npx\s+-y\s+([@\w/.-]+-mcp[@\w/.-]*)',
    r'npm\s+install\s+-?g?\s+([@\w/.-]+-mcp[@\w/.-]*)',
    r'"([@\w/.-]+-mcp(?:@[\w.-]+)?)"',
    r"'([@\w/.-]+-mcp(?:@[\w.-]+)?)'",
]

# 이미 알려진 MCP 서버명 → npm 패키지 매핑
KNOWN_MCPS = {
    "context7": "@upstash/context7-mcp",
    "playwright": "@playwright/mcp",
    "supabase": "@supabase/mcp-server-supabase",
    "github": "@modelcontextprotocol/server-github",
    "filesystem": "@modelcontextprotocol/server-filesystem",
    "firecrawl": "firecrawl-mcp",
    "vercel": "vercel-mcp-server",
    "stripe": "@stripe/mcp",
}

CLAUDE_CODE_KEYWORDS = [
    "claude code", "mcp server", "model context protocol",
    "skills.sh", "npx skills", "claude mcp", "@anthropic",
    "mcp tool", "claude agent"
]


def load_state():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"last_check": None, "checked_videos": [], "installed": []}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def load_channels():
    if CHANNELS_FILE.exists():
        try:
            return json.loads(CHANNELS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def should_run(state):
    if not state.get("last_check"):
        return True
    last = datetime.fromisoformat(state["last_check"])
    return datetime.now() - last > timedelta(hours=CHECK_INTERVAL_HOURS)


def fetch_rss(channel_id):
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception:
        return None


def parse_rss(xml_text):
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "yt": "http://www.youtube.com/xml/schemas/2015",
        "media": "http://search.yahoo.com/mrss/",
    }
    try:
        root = ET.fromstring(xml_text)
        videos = []
        for entry in root.findall("atom:entry", ns):
            vid_id = entry.find("yt:videoId", ns)
            title = entry.find("atom:title", ns)
            published = entry.find("atom:published", ns)
            desc = entry.find(".//media:description", ns)
            if vid_id is not None:
                videos.append({
                    "id": vid_id.text or "",
                    "title": (title.text or "") if title is not None else "",
                    "published": (published.text or "") if published is not None else "",
                    "description": (desc.text or "") if desc is not None else "",
                    "url": f"https://www.youtube.com/watch?v={vid_id.text}",
                })
        return videos
    except Exception:
        return []


def is_relevant(video):
    text = f"{video['title']} {video['description']}".lower()
    return any(kw in text for kw in CLAUDE_CODE_KEYWORDS)


def extract_skills(text):
    found = []
    for pat in SKILL_INSTALL_PATTERNS:
        found.extend(re.findall(pat, text, re.IGNORECASE))
    return list(set(found))


def extract_mcps(text):
    found = []
    for pat in MCP_NPM_PATTERNS:
        found.extend(re.findall(pat, text, re.IGNORECASE))
    # 알려진 MCP 이름도 감지
    text_lower = text.lower()
    for keyword, pkg in KNOWN_MCPS.items():
        if keyword in text_lower:
            found.append(pkg)
    return list(set(found))


def already_installed_mcp(pkg_name, settings_path):
    try:
        settings = json.loads(Path(settings_path).read_text(encoding="utf-8"))
        mcp_servers = settings.get("mcpServers", {})
        pkg_short = pkg_name.split("/")[-1].replace("-mcp", "").replace("mcp-server-", "")
        return any(pkg_short in key.lower() for key in mcp_servers)
    except Exception:
        return False


def add_mcp_to_settings(pkg_name, settings_path):
    try:
        settings = json.loads(Path(settings_path).read_text(encoding="utf-8"))
        server_key = pkg_name.split("/")[-1].replace("@", "").replace("-mcp", "").replace("mcp-server-", "")
        if server_key not in settings.get("mcpServers", {}):
            if "mcpServers" not in settings:
                settings["mcpServers"] = {}
            settings["mcpServers"][server_key] = {
                "command": "npx",
                "args": ["-y", pkg_name],
                "_auto_added": True,
                "_source": "influencer_monitor",
                "_added_date": datetime.now().strftime("%Y-%m-%d")
            }
            Path(settings_path).write_text(
                json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            return True
    except Exception:
        pass
    return False


def install_skill(pkg):
    try:
        result = subprocess.run(
            ["npx", "skills", "add", pkg, "-g", "-y"],
            capture_output=True, text=True, timeout=60
        )
        return result.returncode == 0
    except Exception:
        return False


def log_entry(data):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
    except Exception:
        pass


def main():
    state = load_state()

    if not should_run(state):
        return 0

    channels = load_channels()
    active = [c for c in channels if c.get("active", True) and c.get("platform") == "youtube"]
    if not active:
        return 0

    settings_path = str(CLAUDE_DIR / "settings.json")
    checked = set(state.get("checked_videos", []))
    installed_skills = []
    added_mcps = []
    relevant_videos = []

    for ch in active:
        cid = ch.get("channel_id", "")
        if not cid:
            continue

        xml = fetch_rss(cid)
        if not xml:
            continue

        videos = parse_rss(xml)

        for video in videos[:5]:
            if video["id"] in checked:
                continue

            checked.add(video["id"])

            if not is_relevant(video):
                continue

            relevant_videos.append({"channel": ch["name"], "title": video["title"], "url": video["url"]})
            text = f"{video['title']} {video['description']}"

            # 스킬 감지 & 설치
            for skill_pkg in extract_skills(text):
                if skill_pkg not in [i["pkg"] for i in state.get("installed", [])]:
                    if install_skill(skill_pkg):
                        installed_skills.append({"pkg": skill_pkg, "source": video["url"]})

            # MCP 감지 & settings.json 추가
            for mcp_pkg in extract_mcps(text):
                if not already_installed_mcp(mcp_pkg, settings_path):
                    if add_mcp_to_settings(mcp_pkg, settings_path):
                        added_mcps.append({"pkg": mcp_pkg, "source": video["url"]})

    # 상태 저장
    state["last_check"] = datetime.now().isoformat()
    state["checked_videos"] = list(checked)[-1000:]
    state["installed"] = state.get("installed", []) + installed_skills + added_mcps
    save_state(state)

    # 보고
    if installed_skills or added_mcps:
        print("\n[인플루언서 모니터] 자동 업데이트 완료:")
        for item in installed_skills:
            print(f"  ✓ 스킬 설치: {item['pkg']}")
            print(f"    출처: {item['source']}")
        for item in added_mcps:
            print(f"  ✓ MCP 추가: {item['pkg']} (Claude Code 재시작 시 활성화)")
            print(f"    출처: {item['source']}")
        log_entry({
            "timestamp": datetime.now().isoformat(),
            "relevant_videos": relevant_videos,
            "installed_skills": installed_skills,
            "added_mcps": added_mcps,
        })
    elif relevant_videos:
        print(f"\n[인플루언서 모니터] 관련 영상 {len(relevant_videos)}개 감지, 설치 항목 없음")

    return 0


if __name__ == "__main__":
    sys.exit(main())
