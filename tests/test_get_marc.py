# import uiucprescon.pygetmarc.request
import os

from uiucprescon import pygetmarc

def test_get_marc():
    with open(os.path.join(os.path.dirname(__file__), "1099891.marc"), "rU", encoding="utf8") as marc_file:
        expected_marc_data = marc_file.read()

    marc_record = pygetmarc.request.get_marc(bib_id="1099891").replace("\r\n", "\n")
    assert expected_marc_data == marc_record
