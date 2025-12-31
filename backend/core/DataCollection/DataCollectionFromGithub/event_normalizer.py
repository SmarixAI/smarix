"""Event normalizer

Provides a small utility to normalize GitHub and Teams events into a
consistent shape used by the repository processor.
"""
import hashlib
from datetime import datetime
from typing import Dict, Any, List


class EventNormalizer:
    """Normalize different event payloads (commits, issues, PRs, Teams messages)

    This lightweight normalizer provides consistent fields for downstream
    processing: id, source, type, text, tags, timestamp.
    """

    def __init__(self):
        self.keywords = {
            "onboarding": ["onboard", "welcome", "new hire", "setup", "getting started"],
            "offboarding": ["handoff", "resign", "leave", "offboard", "transition", "retire"],
            "knowledge": ["lesson", "why", "decision", "gotcha", "fix", "note", "explain"]
        }

    def _hash(self, text: str) -> str:
        return hashlib.sha1(text.encode("utf-8")).hexdigest()

    def normalize_github_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        e_type = event.get("type") or event.get("event_type") or "unknown"
        payload = event.get("payload", {}) or {}
        text = ""

        if e_type in ("commit", "Commit", "push"):
            commit = payload.get("commit") or payload.get("commit_data") or {}
            text = commit.get("message", "")
        elif e_type in ("issue", "Issue"):
            text = (payload.get("title", "") + " " + (payload.get("body", "") or ""))
        elif e_type in ("pr", "pull_request", "PullRequestEvent"):
            text = (payload.get("title", "") + " " + (payload.get("body", "") or ""))
        else:
            # Fallback: attempt to stringify common fields
            text = " ".join([str(payload.get(k, "")) for k in ("title", "message", "body") if payload.get(k)])

        tags = self._detect_tags(text)
        timestamp = payload.get("timestamp") or payload.get("created_at") or payload.get("date") or datetime.utcnow().isoformat()

        return {
            "id": self._hash(str(payload)[:300] + str(timestamp)),
            "source": "github",
            "type": e_type,
            "text": text,
            "tags": tags,
            "timestamp": timestamp
        }

    def normalize_teams_message(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        text = msg.get("content") or msg.get("text") or ""
        tags = self._detect_tags(text)
        timestamp = msg.get("timestamp") or msg.get("created_at") or datetime.utcnow().isoformat()
        return {
            "id": self._hash(str(msg)[:300] + str(timestamp)),
            "source": "teams",
            "type": "message",
            "text": text,
            "tags": tags,
            "timestamp": timestamp
        }

    def _detect_tags(self, text: str) -> List[str]:
        tags: List[str] = []
        t = (text or "").lower()
        for label, kws in self.keywords.items():
            for k in kws:
                if k in t:
                    tags.append(label)
                    break
        # remove duplicates while preserving order
        return list(dict.fromkeys(tags))
