"""Several files in this resource use HGNC gene symbols to identify individual
genes. However, the symbols assigned to HGNC IDs can change over time, and
therefore previously curated symbols can become invalid. This script
generates a mapping of current (i.e. at the time of running the script)
mappings of HGNC IDs to symbols so that the assumptions about the identity
of the genes in the various tables can be traced."""

import csv
import os

from famplex.constants import EXPORT_DIR, GROUNDING_MAP_TSV_PATH, RELATIONS_TSV_PATH
from indra.databases import hgnc_client

HERE = os.path.dirname(os.path.abspath(__file__))
HGNC_SYMBOL_MAP_PATH = os.path.join(EXPORT_DIR, 'hgnc_symbol_map.csv')


def main():
    hgnc_symbols = set()
    # Gather all HGNC symbols from relations.csv
    with open(RELATIONS_TSV_PATH) as f:
        for ns1, id1, n1, rel, ns2, id2, n2 in csv.reader(f, delimiter='\t'):
            if ns1 == 'HGNC':
                hgnc_symbols.add(n1)
            if ns2 == 'HGNC':
                hgnc_symbols.add(n2)

    # Gather all HGNC symbols from grounding_map.csv
    with open(GROUNDING_MAP_TSV_PATH) as f:
        for text, db, db_id, db_name in csv.reader(f, delimiter='\t'):
            if db == 'HGNC':
                hgnc_symbols.add(db_name)

    # Create output file
    with open(HGNC_SYMBOL_MAP_PATH, 'w') as fh:
        for hgnc_symbol in sorted(list(hgnc_symbols)):
            hgnc_id = hgnc_client.get_hgnc_id(hgnc_symbol)
            fh.write('%s,%s\r\n' % (hgnc_symbol, hgnc_id))


if __name__ == '__main__':
    main()
