import os

from uiucprescon import pygetmarc


def test_get_marc():
    with open(os.path.join(os.path.dirname(__file__), "1099891.marc"), "rU", encoding="utf-8-sig") as marc_file:
        expected_marc_data = marc_file.read()

    marc_record = pygetmarc.request.get_marc(bib_id="1099891")
    assert expected_marc_data == marc_record


def test_get_marc_validated():
    with open(os.path.join(os.path.dirname(__file__), "1099891.marc"), "rU", encoding="utf-8-sig") as marc_file:
        expected_marc_data = marc_file.read()
        expected_marc_data_lines = expected_marc_data.split("\n")
        new_expected_marc_data_lines = []
        for line in expected_marc_data_lines:
            if '<?count 1 ?>' in line:
                new_expected_marc_data_lines.append('<?v true ?>')

            new_expected_marc_data_lines.append(line)

        expected_marc_data = "\n".join(new_expected_marc_data_lines)

    marc_record = pygetmarc.request.get_marc(bib_id="1099891", validate=True)
    assert expected_marc_data == marc_record
