"""
Daily Outreach Tracker
Tracks volume, responses, and pipeline for the $0 revenue engine.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class OutreachLog:
    date: str
    messages_sent: int = 0
    replies_received: int = 0
    calls_booked: int = 0
    notes: List[str] = field(default_factory=list)


class OutreachTracker:
    def __init__(self):
        self.logs: List[OutreachLog] = []
        self.current_streak = 0

    def log_day(self, sent: int, replies: int, booked: int, note: str = ""):
        today = datetime.now().strftime("%Y-%m-%d")
        log = OutreachLog(
            date=today,
            messages_sent=sent,
            replies_received=replies,
            calls_booked=booked,
            notes=[note] if note else []
        )
        self.logs.append(log)
        return f"Logged {sent} sent, {replies} replies, {booked} booked."

    def get_summary(self) -> str:
        if not self.logs:
            return "No outreach logged yet. Start today."

        total_sent = sum(l.messages_sent for l in self.logs)
        total_replies = sum(l.replies_received for l in self.logs)
        total_booked = sum(l.calls_booked for l in self.logs)
        days = len(self.logs)

        return (
            f"📊 **OUTREACH SUMMARY**\n\n"
            f"Days tracked: {days}\n"
            f"Total sent: {total_sent}\n"
            f"Total replies: {total_replies}\n"
            f"Total booked: {total_booked}\n"
            f"Reply rate: {total_replies/total_sent*100:.1f}%" if total_sent > 0 else "No data"
        )

    def today_target(self) -> str:
        return "Target today: 50+ messages. No excuses."


tracker = OutreachTracker()