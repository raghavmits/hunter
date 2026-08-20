"""Pydantic schema for GET /api/quotas (issue #20)."""

from pydantic import BaseModel


class QuotaProgress(BaseModel):
    count: int
    target: int
    remaining: int


class QuotaSummary(BaseModel):
    cold_outreach_sent: QuotaProgress
    warm_intro_requests_sent: QuotaProgress
    cold_applications_submitted: QuotaProgress
    referral_asks_made: QuotaProgress
