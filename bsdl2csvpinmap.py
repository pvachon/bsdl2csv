#!/usr/bin/env python3
#
# Based on python-bsdl-parser, thanks Forest for the hard work on the ebnf.
#
# Copyright (c) 2020, Phil Vachon <phil@security-embedded.com>
# Copyright (c) 2016, Forest Crossman <cyrozap@gmail.com>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#

import argparse
import csv
import logging

import bsdl

class CSVPinConvertSemantics(object):
    def __init__(self):
        # Collect the pin to port mappings
        self._pin_map = {}

        # Collect the port attributes so we can annotate
        self._port_map = {}

        # Length of port vector
        self._port_vec_length = 0

    def pin_spec(self, ast):
        """
        When a port definition's pin spec is found, grab the port name(s) and populate the
        attributes in the port map
        """
        for identifier in ast['identifier_list']:
            if identifier in self._port_map:
                raise Exception('Name {} already exists in port map.')

            nr_pins = 1
            if type(ast['port_dimension']) != str:
                logging.debug('Vector Pin Spec: {}'.format(ast))
                # Ugly, but it works. Extract the vector size.
                pd = ast['port_dimension']
                bit_vec = pd['bit_vector']
                if bit_vec[1] == 'to':
                    vec_min = int(bit_vec[0])
                    vec_max = int(bit_vec[2]) + 1
                elif bit_vec[1] == 'downto':
                    vec_max = int(bit_vec[0]) + 1
                    vec_min = int(bit_vec[2])
                else:
                    raise Exception('Should have been handled by the grammar: unknown bit vector specification: {}.'.format(bit_vec[1]))
                nr_pins = vec_max - vec_min

            self._port_map[identifier] = {'nr_pins': nr_pins, 'direction': ast['pin_type']}
            self._port_vec_length += nr_pins
        return ast

    def map_string(self, ast):
        """
        When a PIN_MAP is encountered, parse out pins and store them for later conversion
        """
        parser = bsdl.bsdlParser()
        ast = parser.parse(''.join(ast), "port_map")
        for item in ast:
            for pin in item['pin_list']:
                if int(pin) in self._pin_map.keys():
                    raise Exception('Pin {} already in pin list?! BSDL is malformed. (pin name: {})'.format(pin, item['port_name']))

                self._pin_map[int(pin)] = item['port_name']
        return ast

_direction_mapping = {
    'inout' : 'Bidirectional',
    'linkage' : 'Power',
    'in' : 'Input',
    'out' : 'Output',
    'passive' : 'Passive'
}

def main():
    parser = argparse.ArgumentParser(description='Parse a BSDL file and generate a pin map CSV from it for use with Allegro.')
    parser.add_argument('-o', '--output', type=str, required=False, help='File to write to (default: stdout)', default='/dev/stdout')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('filename', type=str, help='BSDL file to parse')
    args = parser.parse_args()

    # Set up logging.
    if args.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logging.basicConfig(format='%(asctime)s - %(name)s:%(levelname)s:%(message)s', datefmt='%m/%d/%Y %H:%M:%S', level=log_level)

    logging.debug('Input file: {}'.format(args.filename))

    # Open the BSDL and turn it into a Python object
    with open(args.filename) as f:
        text = f.read()
        parser = bsdl.bsdlParser()
        semantics = CSVPinConvertSemantics()

        # Walk the AST, and collect a pin map from it.
        ast = parser.parse(text, 'bsdl_description', semantics=semantics, parseinfo=False)

    logging.debug('Finished parsing BSDL. There are {} pins. Port vector length is {}. Generating pinmap.'.format(len(semantics._pin_map.keys()), semantics._port_vec_length))

    output_pin_map = []

    for pin_mapping in sorted(semantics._pin_map.items()):
        port_attrs = semantics._port_map.get(pin_mapping[1], {})
        logging.debug('Pin {} Port {}, attributes: {}'.format(pin_mapping[0], pin_mapping[1], port_attrs))
        port_dir = _direction_mapping.get(port_attrs.get('direction', 'passive'), 'Passive')
        output_pin_map.append({'Number': pin_mapping[0], 'Name': pin_mapping[1], 'Type' : port_dir, 'Shape': 'Short'})

    with open(args.output, 'wt+') as outf:
        writer = csv.DictWriter(outf, fieldnames=['Number', 'Name', 'Type', 'Shape'], dialect='excel')

        writer.writeheader()
        for mapping in output_pin_map:
            writer.writerow(mapping)

if __name__ == '__main__':
    main()

