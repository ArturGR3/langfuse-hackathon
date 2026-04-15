from services.scrubber import scrub_pii


def test_replaces_single_pii():
    assert scrub_pii("Hello Max Mustermann", ["Max Mustermann"]) == "Hello [REDACTED]"


def test_replaces_multiple_pii():
    result = scrub_pii(
        "Name: Anna Schmidt, IBAN: DE89370400440532013000",
        ["Anna Schmidt", "DE89370400440532013000"],
    )
    assert result == "Name: [REDACTED], IBAN: [REDACTED]"


def test_case_insensitive():
    assert scrub_pii("Hello max mustermann", ["Max Mustermann"]) == "Hello [REDACTED]"


def test_empty_pii_list():
    assert scrub_pii("Hello world", []) == "Hello world"


def test_multiple_occurrences():
    assert scrub_pii("Max called. Max left.", ["Max"]) == "[REDACTED] called. [REDACTED] left."
