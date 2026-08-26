import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).parents[1]
CATALOG = ROOT / "translations" / "argos_translate_sv.ts"


def test_swedish_catalog_is_complete():
    root = ET.parse(CATALOG).getroot()
    messages = root.findall(".//message")
    assert len(messages) >= 20
    for message in messages:
        source = message.findtext("source") or ""
        translation = message.findtext("translation") or ""
        assert source.strip()
        assert translation.strip(), source
        assert message.find("translation").get("type") != "unfinished"

    translated = sum(
        1
        for message in messages
        if (message.findtext("translation") or "").strip()
        and message.find("translation").get("type") != "unfinished"
    )
    assert translated / len(messages) > 0.20


def test_source_catalogs_do_not_contain_compiled_files():
    assert not list((ROOT / "translations").glob("*.qm"))
