"""Shared helper so SQLAlchemy's Enum columns store the enum's value, not its name."""

from enum import StrEnum


def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [member.value for member in enum_cls]
