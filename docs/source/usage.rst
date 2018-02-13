.. _usage:

Usage
=====

The following code with retrieve the marc xml record for bib id, 1099891.

.. testcode::

    from uiucprescon import pygetmarc
    marc_record = pygetmarc.get_marc(bib_id=1099891)
    print(marc_record)

When printed to the screen, this results in the following output

.. testoutput::

    <record xmlns="http://www.loc.gov/MARC21/slim" xsi:schemaLocation="http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
      <leader>03183cam a2200505I  4500</leader>
      <controlfield tag="001">1099891</controlfield>
      <controlfield tag="005">20171111225037.0</controlfield>
      <controlfield tag="008">720602s1926    nyuab    b    000 0 eng  </controlfield>
      <datafield tag="010" ind1=" " ind2=" ">
        <subfield code="a">   26016324 </subfield>
      </datafield>
      <datafield tag="035" ind1=" " ind2=" ">
        <subfield code="a">(OCoLC)ocm00323295</subfield>
      </datafield>
    ...

