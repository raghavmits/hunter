"""Typed, cached loader for config.yaml (issue #3)."""

import os
from enum import StrEnum
from functools import cache
from pathlib import Path

from pydantic import BaseModel, ValidationError
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

CONFIG_PATH_ENV_VAR = "HUNTER_CONFIG_PATH"
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config.yaml"

_yaml = YAML(typ="safe")


class ConfigError(Exception):
    """Raised when config.yaml is missing, malformed, or fails validation."""


class TargetType(StrEnum):
    INPUT = "input"
    OUTCOME = "outcome"


class CadenceEntry(BaseModel):
    intervals: list[int]
    recurring: bool = False


class DailyQuotas(BaseModel):
    cold_outreach_sent: int
    warm_intro_requests_sent: int
    cold_applications_submitted: int
    referral_asks_made: int


class CampaignTarget(BaseModel):
    target: int
    type: TargetType
    deadline: str | None = None


class Config(BaseModel):
    cadence: dict[str, CadenceEntry]
    daily_quotas: DailyQuotas
    campaign_targets: dict[str, CampaignTarget]
    role_families: list[str]
    contact_sources: list[str]
    ghost_threshold: int
    at_risk_threshold_days: int


def _config_path() -> Path:
    override = os.environ.get(CONFIG_PATH_ENV_VAR)
    return Path(override) if override else DEFAULT_CONFIG_PATH


@cache
def _load_config(path_str: str) -> Config:
    path = Path(path_str)
    if not path.is_file():
        raise ConfigError(f"config file not found at {path}")

    try:
        with path.open("r") as f:
            raw = _yaml.load(f)
    except YAMLError as exc:
        raise ConfigError(f"config file at {path} is not valid YAML: {exc}") from exc

    try:
        return Config.model_validate(raw)
    except ValidationError as exc:
        raise ConfigError(f"config file at {path} failed validation:\n{exc}") from exc


def get_config() -> Config:
    """Return the validated config, parsed once per distinct file path and cached."""
    return _load_config(str(_config_path()))
