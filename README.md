# BSDL2CSVPINMAP - Convert a BSDL to a CSV

Given a BSDL for a micro or other IC with a pin map, generate a CSV file
containing a list of pins and attributes. Useful when creating symbols in
Allegro.

Based on `python-bsdl-parser` from Forest Crossman. `python-bsdl-parser` is a
[Grako][Grako]-based parser for IEEE 1149.1 Boundary-Scan Description Language
(BSDL) files.

## Requirements

* Python 3
* [Grako 3.99.9][Grako]

## Usage

Install the requirements with `pip`. Invoke `make` to generate the python code
to parse BSDLs.

After generating the parser module, you can invoke the `bsdl2cvspinmap.py`
script for details on how to use it.

[Grako]: https://pypi.python.org/pypi/grako
