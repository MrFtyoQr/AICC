"""HU-16: tabla de transiciones explícita y diccionario de estados (sin base de datos)."""

import itertools
import re

import pytest

from app.core.config import REPO_ROOT
from app.domain.tasks.state_machine import (
    LABELS,
    TERMINAL,
    TRANSITIONS,
    Command,
    InvalidTransition,
    TaskStatus,
    allowed_commands,
    next_status,
)

S, C = TaskStatus, Command

# Copia independiente del diagrama de orquestacion.md §3. Si alguien cambia la tabla del dominio
# sin cambiar el diseño (o al revés), esta prueba lo detecta.
EXPECTED = {
    (S.DRAFT, C.PLAN): S.PLANNING,
    (S.PLANNING, C.PLAN_READY): S.AWAITING_APPROVAL,
    (S.PLANNING, C.PLAN_FAILED): S.PLANNING_FAILED,
    (S.PLANNING, C.POLICY_REJECT): S.REJECTED_BY_POLICY,
    (S.PLANNING_FAILED, C.EDIT): S.DRAFT,
    (S.REJECTED_BY_POLICY, C.EDIT): S.DRAFT,
    (S.AWAITING_APPROVAL, C.APPROVE): S.APPROVED,
    (S.AWAITING_APPROVAL, C.REJECT): S.REJECTED,
    (S.AWAITING_APPROVAL, C.REQUEST_CHANGES): S.PLANNING,
    (S.APPROVED, C.ENQUEUE): S.RUNNING,
    (S.RUNNING, C.PAUSE): S.PAUSED,
    (S.PAUSED, C.RESUME): S.RUNNING,
    (S.RUNNING, C.SUCCEED): S.DONE,
    (S.RUNNING, C.FAIL): S.FAILED,
    **{
        (s, C.CANCEL): S.CANCELLED
        for s in S
        if s not in {S.DONE, S.FAILED, S.CANCELLED, S.REJECTED}
    },
}


def test_transition_table_matches_design():
    assert TRANSITIONS == EXPECTED


@pytest.mark.parametrize(("source", "command"), sorted(EXPECTED))
def test_every_valid_transition(source, command):
    assert next_status(source, command) == EXPECTED[(source, command)]


INVALID = sorted(set(itertools.product(S, C)) - set(EXPECTED))


@pytest.mark.parametrize(("source", "command"), INVALID)
def test_every_invalid_transition_is_rejected(source, command):
    with pytest.raises(InvalidTransition):
        next_status(source, command)


@pytest.mark.parametrize("status", sorted(TERMINAL))
def test_terminal_states_allow_nothing(status):
    assert allowed_commands(status) == []


def test_cancel_is_allowed_from_every_non_terminal_state():
    for status in set(S) - TERMINAL:
        assert C.CANCEL in allowed_commands(status)


def test_labels_match_ux_dictionary():
    text = (REPO_ROOT / "docs" / "ux" / "principios-ux.md").read_text(encoding="utf-8")
    section = text.split("## 6. Diccionario de estados")[1].split("\n## ")[0]
    documented = dict(re.findall(r"^\| `([A-Z_]+)` \| ([^|]+?) \|", section, re.M))

    assert documented == {status.value: label for status, label in LABELS.items()}
