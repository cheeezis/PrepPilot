from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from preppilot_api.models import FoodConcept, FoodSourceIdentifier


class FoodConceptNotFoundError(LookupError):
    pass


class FoodSourceIdentifierNotFoundError(LookupError):
    pass


class FoodSourceIdentifierConflictError(ValueError):
    pass


@dataclass(frozen=True)
class ObserveFoodSourceIdentifierCommand:
    source_name: str
    external_id: str
    source_label: str | None = None
    source_url: str | None = None


def observe_food_source_identifier(
    session: Session,
    command: ObserveFoodSourceIdentifierCommand,
) -> tuple[FoodSourceIdentifier, bool]:
    source_name = _required(command.source_name, "source name")
    external_id = _required(command.external_id, "external ID")
    identifier = session.scalar(
        select(FoodSourceIdentifier).where(
            FoodSourceIdentifier.source_name == source_name,
            FoodSourceIdentifier.external_id == external_id,
        )
    )
    if identifier is not None:
        if identifier.source_label is None:
            identifier.source_label = _optional(command.source_label)
        if identifier.source_url is None:
            identifier.source_url = _optional(command.source_url)
        return identifier, False

    identifier = FoodSourceIdentifier(
        concept_id=None,
        source_name=source_name,
        external_id=external_id,
        source_label=_optional(command.source_label),
        source_url=_optional(command.source_url),
    )
    session.add(identifier)
    session.flush()
    return identifier, True


def resolve_food_source_identifier(
    session: Session,
    *,
    identifier_id: int,
    concept_key: str,
) -> tuple[FoodSourceIdentifier, bool]:
    concept_key = _required(concept_key, "concept key")
    concept = session.scalar(
        select(FoodConcept).where(FoodConcept.key == concept_key)
    )
    if concept is None:
        raise FoodConceptNotFoundError(concept_key)

    identifier = session.get(FoodSourceIdentifier, identifier_id)
    if identifier is None:
        raise FoodSourceIdentifierNotFoundError(identifier_id)
    if identifier.concept_id is not None:
        if identifier.concept_id != concept.id:
            raise FoodSourceIdentifierConflictError(
                "source identifier already belongs to another food concept"
            )
        return identifier, False

    identifier.concept_id = concept.id
    session.flush()
    return identifier, True


def list_unresolved_food_source_identifiers(
    session: Session,
) -> tuple[FoodSourceIdentifier, ...]:
    return tuple(
        session.scalars(
            select(FoodSourceIdentifier)
            .where(FoodSourceIdentifier.concept_id.is_(None))
            .order_by(FoodSourceIdentifier.id)
        )
    )


def find_food_concept_by_source_identifier(
    session: Session,
    *,
    source_name: str,
    external_id: str,
) -> FoodConcept | None:
    return session.scalar(
        select(FoodConcept)
        .join(
            FoodSourceIdentifier,
            FoodSourceIdentifier.concept_id == FoodConcept.id,
        )
        .where(
            FoodSourceIdentifier.source_name == source_name.strip(),
            FoodSourceIdentifier.external_id == external_id.strip(),
        )
    )


def _required(value: str, field_name: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{field_name} must not be blank")
    return stripped


def _optional(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip() or None
