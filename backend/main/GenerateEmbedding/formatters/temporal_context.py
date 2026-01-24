from datetime import datetime

def format_temporal_context(temporal):
    if not temporal:
        return ""

    parts = []
    def fmt(ts):
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%B %d, %Y")
        except:
            return ts

    if temporal.get("created_at"):
        parts.append(f"created {fmt(temporal['created_at'])}")
    if temporal.get("updated_at"):
        parts.append(f"updated {fmt(temporal['updated_at'])}")
    if temporal.get("merged_at"):
        parts.append("merged")
    elif temporal.get("closed_at"):
        parts.append("closed")

    return ", ".join(parts)

