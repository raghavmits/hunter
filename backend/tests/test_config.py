"""config.yaml loads into a validated, cached Config (issue #3)."""

import pytest
from app.config import CONFIG_PATH_ENV_VAR, ConfigError, get_config

VALID_YAML = """
cadence:
  cold_outreach:
    intervals: [5, 10, 20]
daily_quotas:
  cold_outreach_sent: 10
  warm_intro_requests_sent: 6
  cold_applications_submitted: 6
  referral_asks_made: 3
campaign_targets:
  new_connections_made:
    target: 60
    type: input
    deadline: null
role_families: [FDE, SWE, MLE, MTS, OTHER]
contact_sources: [recruiter, linkedin]
ghost_threshold: 3
at_risk_threshold_days: 8
"""


@pytest.fixture
def point_at(tmp_path, monkeypatch):
    def _point_at(text: str) -> None:
        config_file = tmp_path / "config.yaml"
        config_file.write_text(text)
        monkeypatch.setenv(CONFIG_PATH_ENV_VAR, str(config_file))

    return _point_at


def test_valid_load_from_the_real_config_yaml() -> None:
    config = get_config()

    assert config.cadence["cold_outreach"].intervals == [5, 10, 20]
    assert config.cadence["long_term_nurture"].recurring is True
    assert config.daily_quotas.cold_outreach_sent == 10
    assert config.campaign_targets["offers"].target == 3
    assert config.campaign_targets["offers"].deadline is None
    assert "FDE" in config.role_families
    assert "linkedin" in config.contact_sources
    assert config.ghost_threshold == 3
    assert config.at_risk_threshold_days == 8


def test_missing_key_fails_loudly_naming_the_key(point_at) -> None:
    point_at(VALID_YAML.replace("ghost_threshold: 3\n", ""))

    with pytest.raises(ConfigError, match="ghost_threshold"):
        get_config()


def test_malformed_value_fails_loudly_naming_the_field(point_at) -> None:
    point_at(VALID_YAML.replace("cold_outreach_sent: 10", "cold_outreach_sent: not-a-number"))

    with pytest.raises(ConfigError, match="cold_outreach_sent"):
        get_config()


def test_missing_file_raises_clear_error(monkeypatch, tmp_path) -> None:
    missing = tmp_path / "does-not-exist.yaml"
    monkeypatch.setenv(CONFIG_PATH_ENV_VAR, str(missing))

    with pytest.raises(ConfigError, match="not found"):
        get_config()


def test_second_call_is_cached_and_does_not_reread_the_file(point_at, tmp_path) -> None:
    point_at(VALID_YAML)
    first = get_config()

    (tmp_path / "config.yaml").unlink()

    second = get_config()

    assert second is first
