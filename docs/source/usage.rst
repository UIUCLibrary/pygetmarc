.. _usage:

Usage
=====

Getting Marc Data
-----------------

The following code with retrieve the marc xml record for bib id, 1099891.

.. testcode::

    from uiucprescon import pygetmarc
    marc_record = pygetmarc.get_marc(bib_id=1099891)



Enrich Record
-------------

To modify the xml record. Use the one of the :ref:`modifiers <modifiers>`.

.. testcode::

    from uiucprescon import pygetmarc

    # Get the marc xml record
    marc_record = pygetmarc.get_marc(bib_id=1099891)

    # Get a modifier that adds the 955 field
    field_adder = pygetmarc.modifiers.Add955()

    # Configure the properties of the modifier
    field_adder.bib_id = "6852844"

    # Transform the original record
    transformed = field_adder.enrich(src=marc_record)