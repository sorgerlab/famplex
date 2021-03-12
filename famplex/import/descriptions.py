# -*- coding: utf-8 -*-

"""Import descriptions."""

import csv
import os
from collections import defaultdict

import bioregistry
import click
from more_click import verbose_option
from tqdm import tqdm

import pyobo
from famplex.load import load_descriptions, load_entities, load_equivalences

HERE = os.path.abspath(os.path.dirname(__file__))
PATH = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir, 'descriptions.csv'))

PRIORITY_LIST = [
    'interpro',
    'mesh',
    'go',
    'eccode',
    'HGNC_GROUP',
    'PF',
]
PRIORITY_LIST = [bioregistry.normalize_prefix(prefix) for prefix in PRIORITY_LIST]


@click.command()
@verbose_option
@click.option('--force', is_flag=True)
def main(force: bool):
    if force:
        for prefix in tqdm(PRIORITY_LIST, desc='reloading resources'):
            tqdm.write(f'reloading {prefix}')
            pyobo.get_id_definition_mapping(prefix, force=True)
    
    description_rows = [tuple(row) for row in load_descriptions()]
    descriptions = {e: d for e, _source, d in description_rows}
    xrefs = defaultdict(dict)

    unnorm = set()
    for xref_ns, xref_id, fplx_id in load_equivalences():
        norm_xref_ns = bioregistry.normalize_prefix(xref_ns)
        if norm_xref_ns is None and xref_ns not in unnorm:
            print('unnormalized ns', xref_ns)
            unnorm.add(xref_ns)
        xrefs[fplx_id][norm_xref_ns] = xref_id

    entities = load_entities()
    missing_description = set(entities) - set(descriptions)
    print(f'{len(descriptions)} have descriptions')
    print(f'{len(missing_description)} missing descriptions')

    for fplx_id in missing_description:
        entity_xrefs = xrefs.get(fplx_id)
        if not entity_xrefs:
            continue
        for prefix in PRIORITY_LIST:
            identifier = entity_xrefs.get(prefix)
            if not identifier:
                continue
            definition = pyobo.get_definition(prefix, identifier)
            if definition:
                description_rows.append((fplx_id, f'{prefix}:{identifier}', definition))
                break

    with open(PATH, 'w') as file:
        writer = csv.writer(
            file, delimiter=',', lineterminator='\r\n',
            quoting=csv.QUOTE_MINIMAL,
            quotechar='"',
        )
        writer.writerows(sorted(description_rows))


if __name__ == '__main__':
    main()
