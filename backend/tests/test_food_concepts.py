import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from preppilot_api.catalog_data import load_catalog
from preppilot_api.catalog_seed import replace_catalog
from preppilot_api.food_concepts import (
    FoodSourceIdentifierConflictError,
    ObserveFoodSourceIdentifierCommand,
    find_food_concept_by_source_identifier,
    list_unresolved_food_source_identifiers,
    observe_food_source_identifier,
    resolve_food_source_identifier,
)
from preppilot_api.models import Base, FoodConcept, FoodSourceIdentifier


def test_observes_one_reusable_unresolved_source_identifier() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session, session.begin():
        replace_catalog(session, load_catalog())
        command = ObserveFoodSourceIdentifierCommand(
            source_name="wikibooks",
            external_id="12345",
            source_label="Cookbook:Tomato",
            source_url="https://en.wikibooks.org/wiki/Cookbook:Tomato",
        )
        first, created = observe_food_source_identifier(session, command)
        second, repeated_created = observe_food_source_identifier(session, command)

        assert created
        assert not repeated_created
        assert second.id == first.id
        assert first.concept_id is None
        assert (
            session.scalar(select(func.count()).select_from(FoodSourceIdentifier))
            == 1
        )
        assert list_unresolved_food_source_identifiers(session) == (first,)
        assert find_food_concept_by_source_identifier(
            session,
            source_name="wikibooks",
            external_id="12345",
        ) is None


def test_resolves_source_identifier_once_and_rejects_reassignment() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session, session.begin():
        replace_catalog(session, load_catalog())
        command = ObserveFoodSourceIdentifierCommand(
            source_name="wikibooks",
            external_id="12345",
            source_label="Cookbook:Tomato",
        )
        identifier, _ = observe_food_source_identifier(session, command)
        resolved, changed = resolve_food_source_identifier(
            session,
            identifier_id=identifier.id,
            concept_key="tomato",
        )
        repeated, repeated_changed = resolve_food_source_identifier(
            session,
            identifier_id=identifier.id,
            concept_key="tomato",
        )

        assert changed
        assert not repeated_changed
        assert repeated.id == resolved.id
        assert list_unresolved_food_source_identifiers(session) == ()

        with pytest.raises(FoodSourceIdentifierConflictError):
            resolve_food_source_identifier(
                session,
                identifier_id=identifier.id,
                concept_key="banana",
            )

        concept = session.scalar(
            select(FoodConcept)
            .join(
                FoodSourceIdentifier,
                FoodSourceIdentifier.concept_id == FoodConcept.id,
            )
            .where(FoodSourceIdentifier.external_id == "12345")
        )
        assert concept is not None
        assert concept.key == "tomato"
