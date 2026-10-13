"""Optional advisory layer. No auto-execution; local rule-based fallback.
Provider calls deliberately abstracted behind a supplied callable.
"""
from __future__ import annotations
import json
from dataclasses import dataclass
from typing import Callable
from .guardian import Finding

@dataclass(frozen=True)
class Advice:
    summary: str
    recommendation: str
    risk: str
    requires_human_review: bool

class Advisor:
    def __init__(self, provider:Callable[[str],str]|None=None):
        self.provider=provider
    def assess(self, findings:list[Finding]) -> Advice:
        count=len(findings)
        risky=[f for f in findings if f.severity in {"high","medium"}]
        risk="high" if any(f.severity=="high" for f in findings) else ("medium" if risky else "low")
        summary=f"{count} event(s) observed; {len(risky)} need attention"
        fallback=Advice(summary,"Review audit log and verify unexpected changes before authorizing a corrective operation.",risk,bool(risky))
        if self.provider is None:return fallback
        payload=json.dumps({"events":[{"severity":f.severity,"code":f.code,"subject":f.subject} for f in findings[:30]]},ensure_ascii=False)
        try:
            data=json.loads(self.provider(payload))
            recommendation=str(data.get("recommendation",fallback.recommendation))[:1000]
            # Provider cannot downgrade risk or remove required human review.
            return Advice(summary,recommendation,risk,bool(risky))
        except (ValueError,TypeError,KeyError):
            return fallback
