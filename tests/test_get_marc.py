import os
import pytest
from uiucprescon import pygetmarc


def get_sample_record(bib_id):
    with open(os.path.join(os.path.dirname(__file__), f"{bib_id}.marc"), "rU", encoding="utf-8-sig") as marc_file:
        expected_marc_data = marc_file.read()
    return expected_marc_data.strip()


@pytest.mark.parametrize("bib_id,validate", [
    (1099891, False),
    (1099891, True),
])
def test_get_marc(bib_id, validate):
    expected_marc_data = get_sample_record(bib_id)
    marc_record = pygetmarc.get_marc(bib_id, validate)
    assert expected_marc_data == marc_record


def test_get_marc_bad():
    with pytest.raises(ValueError):
        try:
            marc_record = pygetmarc.get_marc(0)
        except ValueError as e:
            print(e)
            raise
    # assert expected_marc_data == marc_record
