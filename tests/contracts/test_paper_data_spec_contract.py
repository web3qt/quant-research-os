from pathlib import Path

import yaml


CONTRACT_PATH = Path("contracts/paper_to_spec/paper_data_spec_contract.yaml")


def _load_contract() -> dict:
    assert CONTRACT_PATH.exists(), f"missing contract: {CONTRACT_PATH}"
    payload = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_paper_data_spec_contract_declares_required_shape() -> None:
    contract = _load_contract()

    assert contract["schema_id"] == "qros-paper-data-spec-contract-v1"
    assert contract["spec_version"] == "v1"
    assert contract["required_top_level_fields"] == [
        "spec_version",
        "source",
        "reading_coverage",
        "target_market",
        "core_data_requirements",
        "triggered_optional_blocks",
        "ambiguities",
        "implementation_handoff",
    ]


def test_paper_data_spec_contract_locks_core_blocking_fields() -> None:
    contract = _load_contract()
    expected_core_fields = [
        "universe",
        "price_bars",
        "price_type",
        "funding",
        "fees_and_slippage",
        "label_or_return_target",
        "timestamp_alignment",
        "data_availability",
    ]

    assert contract["core_required_fields"] == expected_core_fields
    assert contract["strict_blocking_fields"] == expected_core_fields


def test_paper_data_spec_contract_declares_requirement_enums() -> None:
    contract = _load_contract()

    assert contract["allowed_requirement_statuses"] == [
        "required",
        "optional",
        "not_needed",
        "unknown",
    ]
    assert contract["allowed_requirement_sources"] == [
        "paper_stated",
        "agent_inferred",
        "researcher_required",
        "exchange_profile_default",
    ]
    assert contract["allowed_exchange_profiles"] == [
        "generic_crypto_perp",
        "binance_usdt_perp",
        "okx_perp",
        "bybit_perp",
    ]


def test_paper_data_spec_contract_declares_field_library_and_profiles() -> None:
    contract = _load_contract()

    assert set(contract["field_library"]["core"]) == set(contract["core_required_fields"])
    assert set(contract["field_library"]["optional_blocks"]) == {
        "derivatives_positioning",
        "liquidity_microstructure",
        "cross_exchange",
        "external_or_onchain",
        "sentiment_or_news",
    }
    assert contract["exchange_profiles"]["binance_usdt_perp"]["quote_currency"] == "USDT"
    assert contract["exchange_profiles"]["binance_usdt_perp"]["contract_settlement"] == "linear"
    assert contract["exchange_profiles"]["generic_crypto_perp"]["timezone"] == "UTC"


def test_paper_data_spec_contract_declares_blocking_question_groups() -> None:
    contract = _load_contract()

    assert contract["blocking_question_groups"] == {
        "market_scope": ["universe", "data_availability"],
        "bar_and_price": ["price_bars", "price_type", "timestamp_alignment"],
        "return_accounting": ["funding", "fees_and_slippage", "label_or_return_target"],
        "source_coverage": ["reading_coverage"],
    }


def test_paper_data_spec_contract_declares_runtime_validated_nested_shapes() -> None:
    contract = _load_contract()

    assert contract["required_optional_block_fields"] == [
        "block_name",
        "reason",
        "requirements",
    ]
    assert contract["required_ambiguity_fields"] == [
        "field",
        "question",
        "blocking",
    ]
    assert contract["required_implementation_handoff_fields"] == [
        "raw_inputs",
        "derived_inputs",
        "validation_checks",
    ]
