from __future__ import annotations

from pathlib import Path
import re
import xml.etree.ElementTree as ET

import yaml


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_DIR = ROOT / "contracts" / "paper_to_spec"
GUIDE_DIR = CONTRACT_DIR / "field_guides"

GUIDE_MAP = {
    "paper_data_spec_contract.yaml": {
        "guide": "paper_data_spec.fields.xml",
        "artifact": "paper_data_spec.yaml",
        "core_container": "core_data_requirements",
    },
    "paper_signal_spec_contract.yaml": {
        "guide": "paper_signal_spec.fields.xml",
        "artifact": "paper_signal_spec.yaml",
        "core_container": "core_signal_requirements",
    },
    "paper_train_freeze_spec_contract.yaml": {
        "guide": "paper_train_freeze_spec.fields.xml",
        "artifact": "paper_train_freeze_spec.yaml",
        "core_container": "core_train_freeze_requirements",
    },
    "paper_test_evidence_spec_contract.yaml": {
        "guide": "paper_test_evidence_spec.fields.xml",
        "artifact": "paper_test_evidence_spec.yaml",
        "core_container": "core_test_evidence_requirements",
    },
    "paper_backtest_spec_contract.yaml": {
        "guide": "paper_backtest_spec.fields.xml",
        "artifact": "paper_backtest_spec.yaml",
        "core_container": "core_backtest_requirements",
    },
    "paper_backtest_implementation_spec_contract.yaml": {
        "guide": "paper_backtest_implementation_spec.fields.xml",
        "artifact": "paper_backtest_implementation_spec.yaml",
        "core_container": "core_implementation_requirements",
    },
    "paper_auto_implementation_handoff_contract.yaml": {
        "guide": "paper_auto_implementation_handoff.fields.xml",
        "artifact": "paper_auto_implementation_handoff.yaml",
        "core_container": "",
    },
}

REQUIRED_EXPLANATION_TAGS = [
    "zhName",
    "meaning",
    "whyItMatters",
    "fillRule",
    "examples",
    "commonMistakes",
]

CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def _load_contract(filename: str) -> dict:
    path = CONTRACT_DIR / filename
    assert path.exists(), f"missing contract: {path}"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict), f"{path} must be a mapping"
    return payload


def _load_guide(filename: str) -> ET.Element:
    path = GUIDE_DIR / filename
    assert path.exists(), f"missing XML field guide: {path}"
    return ET.fromstring(path.read_text(encoding="utf-8"))


def _attr(guide_filename: str, element: ET.Element, attr_name: str) -> str:
    value = element.attrib.get(attr_name)
    assert value is not None, (
        f"{guide_filename} <{element.tag}> missing required attribute {attr_name!r}"
    )
    return value


def _text_for(element: ET.Element, tag: str) -> str:
    child = element.find(tag)
    assert child is not None, f"{element.tag} {element.attrib} missing <{tag}>"
    text = "".join(child.itertext()).strip()
    assert text, f"{element.tag} {element.attrib} has empty <{tag}>"
    return text


def _assert_explanation_complete(element: ET.Element) -> None:
    combined = []
    for tag in REQUIRED_EXPLANATION_TAGS:
        combined.append(_text_for(element, tag))
    assert CJK_RE.search(" ".join(combined)), (
        f"{element.tag} {element.attrib} must include Chinese explanation text"
    )


def _index_entries_by_attr(
    guide_filename: str,
    root: ET.Element,
    tag: str,
    attr_name: str,
) -> dict[str, ET.Element]:
    entries = {}
    for element in root.findall(tag):
        value = _attr(guide_filename, element, attr_name)
        assert value not in entries, (
            f"{guide_filename} has duplicate <{tag}> {attr_name}={value!r}"
        )
        _assert_explanation_complete(element)
        entries[value] = element
    return entries


def test_paper_to_spec_xml_field_guides_exist_and_reference_contracts() -> None:
    for contract_filename, expected in GUIDE_MAP.items():
        root = _load_guide(expected["guide"])
        assert root.tag == "paperSpecFieldGuide"
        assert _attr(expected["guide"], root, "artifact") == expected["artifact"]
        assert _attr(expected["guide"], root, "contract") == contract_filename


def test_paper_to_spec_xml_field_guides_cover_required_fields() -> None:
    for contract_filename, expected in GUIDE_MAP.items():
        contract = _load_contract(contract_filename)
        root = _load_guide(expected["guide"])
        fields = _index_entries_by_attr(expected["guide"], root, "field", "path")

        for field_name in contract.get("required_top_level_fields", []):
            assert field_name in fields, (
                f"{expected['guide']} missing top-level field guide for {field_name}"
            )

        core_container = expected["core_container"]
        for field_name in contract.get("core_required_fields", []):
            path = f"{core_container}.{field_name}"
            assert path in fields, f"{expected['guide']} missing core field guide for {path}"


def test_paper_to_spec_xml_field_guides_cover_optional_blocks_and_blocking_groups() -> None:
    for contract_filename, expected in GUIDE_MAP.items():
        contract = _load_contract(contract_filename)
        root = _load_guide(expected["guide"])
        blocks = _index_entries_by_attr(expected["guide"], root, "block", "name")
        blocking_groups = _index_entries_by_attr(
            expected["guide"], root, "blockingGroup", "name"
        )

        for block_name in contract.get("optional_blocks", []):
            assert block_name in blocks, (
                f"{expected['guide']} missing optional block guide for {block_name}"
            )

        for group_name in contract.get("blocking_question_groups", {}):
            assert group_name in blocking_groups, (
                f"{expected['guide']} missing blocking group guide for {group_name}"
            )
