import difflib
import os
import pytest
from uiucprescon import pygetmarc
from xml.dom import minidom


def get_sample_record(bib_id):
    with open(os.path.join(os.path.dirname(__file__), f"{bib_id}.marc"), "rU",
              encoding="utf-8-sig") as marc_file:

        expected_marc_data = marc_file.read()
    return expected_marc_data.strip()


@pytest.mark.integration
@pytest.mark.parametrize("bib_id,validate", [
    (1099891, False),
    (1099891, True),
])
def test_get_marc(bib_id, validate):
    marc_record = pygetmarc.get_marc(bib_id, validate)
    dom = minidom.parseString(marc_record)
    for control_element in dom.getElementsByTagName("controlfield"):
        if not control_element.attributes['tag'].value == "001":
            continue
        assert control_element.firstChild.data == str(bib_id)


@pytest.mark.integration
def test_get_marc_bad():
    with pytest.raises(ValueError):
        marc_record = pygetmarc.get_marc(0)


def test_clean_data():
    """Remove any Processing Instruction"""
    data = '<record xmlns="http://www.loc.gov/MARC21/slim" ' \
           'xsi:schemaLocation="http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd" ' \
           'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' \
           '\n  <leader>03183cam a2200505I  4500</leader>' \
           '\n  <controlfield tag="001">1099891</controlfield>' \
           '\n  <controlfield tag="005">20171111225037.0</controlfield>' \
           '\n  <controlfield tag="008">720602s1926    nyuab    b    000 0 eng  </controlfield>' \
           '\n</record>' \
           '\n<?query @attr 1=12 "1099891" ?>' \
           '\n<?count 1 ?>'

    cleaned_up_data = pygetmarc.request.clean_up(data)

    assert cleaned_up_data == \
               '<record xmlns="http://www.loc.gov/MARC21/slim" ' \
               'xsi:schemaLocation="http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd" ' \
               'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' \
               '\n  <leader>03183cam a2200505I  4500</leader>' \
               '\n  <controlfield tag="001">1099891</controlfield>' \
               '\n  <controlfield tag="005">20171111225037.0</controlfield>' \
               '\n  <controlfield tag="008">720602s1926    nyuab    b    000 0 eng  </controlfield>' \
               '\n</record>'
