"""Deterministic demo/test data (issue #39).

Pure builder: takes every time-dependent value as an explicit parameter
(same reasoning as app/cadence.py, app/digest.py) and never commits — the
caller (scripts/seed_demo_data.py, or a pytest fixture) decides when to
commit. Flushes only, via the repository layer, per AGENTS.md's
"repositories flush, callers commit" convention.

The four target conditions (overdue, due-today, at-risk, ghost-suggested)
have their next_follow_up_date/nudge_number/stage_entered_at set directly
rather than derived by running compute_cadence and hoping the interval
math lands where needed — compute_cadence already has its own tests
(#10), and re-deriving through it here would make this fixture fragile to
config.yaml retuning for no benefit. Real Touch rows are still logged for
history/realism; they just aren't what determines the final state.

Thresholds are overshot generously rather than parameterized to
config.yaml's exact current values (ghost_threshold=3, at_risk_threshold_
days=8) — nudge_number=4 and a 15-day-old stage_entered_at both clear
either threshold comfortably regardless of future tuning.
"""

from datetime import date, datetime, timedelta

from app.models import (
    Motion,
    RoleFamily,
    Stage,
    StageOrTerminal,
    ThreadStatus,
    TouchChannel,
    TouchDirection,
    TouchKind,
)
from app.repositories import (
    CompanyRepository,
    ContactRepository,
    StageEventRepository,
    ThreadRepository,
    TouchRepository,
)


def _advance_stage(
    thread_repo: ThreadRepository,
    stage_event_repo: StageEventRepository,
    thread_id: int,
    from_stage: StageOrTerminal | None,
    to_stage: StageOrTerminal,
    occurred_at: datetime,
) -> None:
    """Mirrors what POST /threads/{id}/stage does — a stage_event plus the
    matching thread column updates — since this seeds directly through the
    repository layer, not the API."""
    stage_event_repo.create(
        thread_id=thread_id, from_stage=from_stage, to_stage=to_stage, occurred_at=occurred_at
    )
    if to_stage.value in {s.value for s in Stage}:
        thread_repo.update(
            thread_id,
            stage=Stage(to_stage.value),
            status=ThreadStatus.OPEN,
            stage_entered_at=occurred_at,
        )
    else:
        thread_repo.update(thread_id, status=ThreadStatus(to_stage.value), closed_at=occurred_at)


def seed_demo_data(session, today: date, now_utc: datetime) -> dict[str, int]:
    """`session` is intentionally untyped — only app/db.py and app/repositories/
    are allowed to import sqlalchemy.orm.Session (test_db.py's structural
    test), and this module lives outside that boundary on purpose, going
    through the repository layer like everything else does."""
    company_repo = CompanyRepository(session)
    contact_repo = ContactRepository(session)
    thread_repo = ThreadRepository(session)
    touch_repo = TouchRepository(session)
    stage_event_repo = StageEventRepository(session)

    ids: dict[str, int] = {}

    # 1. Acme Corp — overdue
    acme = company_repo.create(name="Acme Corp")
    alex = contact_repo.create(
        full_name="Alex Recruiter", company_id=acme.id, title="Technical Recruiter"
    )
    acme_thread = thread_repo.create(
        company_id=acme.id,
        contact_id=alex.id,
        role_title="Backend Engineer",
        role_family=RoleFamily.SWE,
        motion=Motion.COLD_OUTREACH,
    )
    touch_repo.create(
        thread_id=acme_thread.id,
        kind=TouchKind.COLD_OUTREACH,
        direction=TouchDirection.OUTBOUND,
        channel=TouchChannel.EMAIL,
        occurred_at=today - timedelta(days=8),
    )
    thread_repo.update(
        acme_thread.id,
        next_follow_up_date=today - timedelta(days=3),
        nudge_number=1,
        stage_entered_at=now_utc,
    )
    ids["acme_thread_id"] = acme_thread.id

    # 2. Beta Inc — due today, cold application, no contact
    beta = company_repo.create(name="Beta Inc")
    beta_thread = thread_repo.create(
        company_id=beta.id,
        role_title="ML Engineer",
        role_family=RoleFamily.MLE,
        motion=Motion.COLD_APPLICATION,
    )
    touch_repo.create(
        thread_id=beta_thread.id,
        kind=TouchKind.APPLICATION_SUBMITTED,
        direction=TouchDirection.OUTBOUND,
        channel=TouchChannel.PORTAL,
        occurred_at=today - timedelta(days=7),
    )
    thread_repo.update(
        beta_thread.id, next_follow_up_date=today, nudge_number=1, stage_entered_at=now_utc
    )
    ids["beta_thread_id"] = beta_thread.id

    # 3. Gamma LLC — at-risk (stuck in "replied" for 15 days)
    gamma = company_repo.create(name="Gamma LLC")
    jamie = contact_repo.create(full_name="Jamie Contact", company_id=gamma.id)
    gamma_thread = thread_repo.create(
        company_id=gamma.id,
        contact_id=jamie.id,
        role_title="Staff Engineer",
        role_family=RoleFamily.SWE,
        motion=Motion.WARM_OUTREACH,
    )
    touch_repo.create(
        thread_id=gamma_thread.id,
        kind=TouchKind.WARM_INTRO_REQUEST,
        direction=TouchDirection.OUTBOUND,
        channel=TouchChannel.LINKEDIN,
        occurred_at=today - timedelta(days=16),
    )
    _advance_stage(
        thread_repo,
        stage_event_repo,
        gamma_thread.id,
        StageOrTerminal.OUTREACH,
        StageOrTerminal.REPLIED,
        now_utc - timedelta(days=15),
    )
    thread_repo.update(
        gamma_thread.id, next_follow_up_date=today + timedelta(days=3), follow_up_pinned=True
    )
    ids["gamma_thread_id"] = gamma_thread.id

    # 4. Delta Co — ghost-suggested, cold application, no contact
    delta = company_repo.create(name="Delta Co")
    delta_thread = thread_repo.create(
        company_id=delta.id,
        role_title="Platform Engineer",
        role_family=RoleFamily.SWE,
        motion=Motion.COLD_OUTREACH,
    )
    for days_ago in (20, 15, 10, 5):
        touch_repo.create(
            thread_id=delta_thread.id,
            kind=TouchKind.COLD_OUTREACH,
            direction=TouchDirection.OUTBOUND,
            channel=TouchChannel.EMAIL,
            occurred_at=today - timedelta(days=days_ago),
        )
    thread_repo.update(
        delta_thread.id,
        nudge_number=4,
        next_follow_up_date=today - timedelta(days=1),
        stage_entered_at=now_utc,
    )
    ids["delta_thread_id"] = delta_thread.id

    # 5. Epsilon Corp — healthy, at screen
    epsilon = company_repo.create(name="Epsilon Corp")
    epsilon_contact = contact_repo.create(full_name="Morgan Contact", company_id=epsilon.id)
    epsilon_thread = thread_repo.create(
        company_id=epsilon.id,
        contact_id=epsilon_contact.id,
        role_title="Senior Software Engineer",
        role_family=RoleFamily.SWE,
        motion=Motion.WARM_OUTREACH,
    )
    touch_repo.create(
        thread_id=epsilon_thread.id,
        kind=TouchKind.POST_RECRUITER_CALL,
        direction=TouchDirection.OUTBOUND,
        channel=TouchChannel.EMAIL,
        occurred_at=today - timedelta(days=2),
    )
    _advance_stage(
        thread_repo,
        stage_event_repo,
        epsilon_thread.id,
        StageOrTerminal.OUTREACH,
        StageOrTerminal.REPLIED,
        now_utc - timedelta(days=4),
    )
    _advance_stage(
        thread_repo,
        stage_event_repo,
        epsilon_thread.id,
        StageOrTerminal.REPLIED,
        StageOrTerminal.SCREEN,
        now_utc - timedelta(days=2),
    )
    thread_repo.update(epsilon_thread.id, next_follow_up_date=today + timedelta(days=4))
    ids["epsilon_thread_id"] = epsilon_thread.id

    # 6. Zeta Inc — healthy, at interview
    zeta = company_repo.create(name="Zeta Inc")
    zeta_contact = contact_repo.create(full_name="Taylor Contact", company_id=zeta.id)
    zeta_thread = thread_repo.create(
        company_id=zeta.id,
        contact_id=zeta_contact.id,
        role_title="Founding Engineer",
        role_family=RoleFamily.FDE,
        motion=Motion.WARM_OUTREACH,
    )
    touch_repo.create(
        thread_id=zeta_thread.id,
        kind=TouchKind.POST_INTERVIEW,
        direction=TouchDirection.OUTBOUND,
        channel=TouchChannel.EMAIL,
        occurred_at=today - timedelta(days=1),
    )
    for from_s, to_s, days_ago in (
        (StageOrTerminal.OUTREACH, StageOrTerminal.REPLIED, 7),
        (StageOrTerminal.REPLIED, StageOrTerminal.SCREEN, 5),
        (StageOrTerminal.SCREEN, StageOrTerminal.INTERVIEW, 1),
    ):
        _advance_stage(
            thread_repo,
            stage_event_repo,
            zeta_thread.id,
            from_s,
            to_s,
            now_utc - timedelta(days=days_ago),
        )
    thread_repo.update(zeta_thread.id, next_follow_up_date=today + timedelta(days=7))
    ids["zeta_thread_id"] = zeta_thread.id

    # 7. Eta Corp — healthy, at offer
    eta = company_repo.create(name="Eta Corp")
    eta_contact = contact_repo.create(full_name="Casey Contact", company_id=eta.id)
    eta_thread = thread_repo.create(
        company_id=eta.id,
        contact_id=eta_contact.id,
        role_title="Machine Learning Engineer",
        role_family=RoleFamily.MLE,
        motion=Motion.WARM_OUTREACH,
    )
    touch_repo.create(
        thread_id=eta_thread.id,
        kind=TouchKind.POST_INTERVIEW,
        direction=TouchDirection.OUTBOUND,
        channel=TouchChannel.EMAIL,
        occurred_at=today,
    )
    for from_s, to_s, days_ago in (
        (StageOrTerminal.OUTREACH, StageOrTerminal.REPLIED, 12),
        (StageOrTerminal.REPLIED, StageOrTerminal.SCREEN, 9),
        (StageOrTerminal.SCREEN, StageOrTerminal.INTERVIEW, 5),
        (StageOrTerminal.INTERVIEW, StageOrTerminal.OFFER, 0),
    ):
        _advance_stage(
            thread_repo,
            stage_event_repo,
            eta_thread.id,
            from_s,
            to_s,
            now_utc - timedelta(days=days_ago),
        )
    thread_repo.update(eta_thread.id, next_follow_up_date=today + timedelta(days=2))
    ids["eta_thread_id"] = eta_thread.id

    # 8. Theta LLC — closed (rejected at screen)
    theta = company_repo.create(name="Theta LLC")
    theta_contact = contact_repo.create(full_name="Riley Contact", company_id=theta.id)
    theta_thread = thread_repo.create(
        company_id=theta.id,
        contact_id=theta_contact.id,
        role_title="Infrastructure Engineer",
        role_family=RoleFamily.SWE,
        motion=Motion.COLD_OUTREACH,
    )
    touch_repo.create(
        thread_id=theta_thread.id,
        kind=TouchKind.COLD_OUTREACH,
        direction=TouchDirection.OUTBOUND,
        channel=TouchChannel.EMAIL,
        occurred_at=today - timedelta(days=14),
    )
    _advance_stage(
        thread_repo,
        stage_event_repo,
        theta_thread.id,
        StageOrTerminal.OUTREACH,
        StageOrTerminal.REPLIED,
        now_utc - timedelta(days=10),
    )
    _advance_stage(
        thread_repo,
        stage_event_repo,
        theta_thread.id,
        StageOrTerminal.REPLIED,
        StageOrTerminal.SCREEN,
        now_utc - timedelta(days=6),
    )
    _advance_stage(
        thread_repo,
        stage_event_repo,
        theta_thread.id,
        StageOrTerminal.SCREEN,
        StageOrTerminal.REJECTED,
        now_utc - timedelta(days=1),
    )
    ids["theta_thread_id"] = theta_thread.id

    return ids
