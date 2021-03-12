# -*- coding: utf-8 -*-

"""Import descriptions."""

import csv
from collections import defaultdict

import bioregistry
import click
from more_click import verbose_option

import pyobo
from famplex.load import load_descriptions, load_entities, load_equivalences


@click.command()
@verbose_option
def main():
    description_rows = list(load_descriptions())
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
    entities_sans_descrption = set(entities) - set(descriptions)
    print(f'{len(descriptions)} have descriptions')
    print(f'{len(entities_sans_descrption)} missing descriptions')

    print('loading interpro definitions')
    ip_definition = pyobo.get_id_definition_mapping('interpro')
    print('loading mesh definitions')
    mesh_definition = pyobo.get_id_definition_mapping('mesh')
    print('loaded')

    for fplx_id in entities_sans_descrption:
        entity_xrefs = xrefs.get(fplx_id)
        if not entity_xrefs:
            continue

        definition = None
        if definition is None and (mesh_id := entity_xrefs.get('mesh')):
            if definition := mesh_definition.get(mesh_id):
                description_rows.append((fplx_id, f'mesh:{mesh_id}', definition))
        if definition is None and (interpro_id := entity_xrefs.get('interpro')):
            if definition := ip_definition.get(interpro_id):
                description_rows.append((fplx_id, f'interpro:{interpro_id}', definition))

    with open('/Users/cthoyt/dev/famplex/descriptions.csv', 'w') as file:
        writer = csv.writer(
            file, delimiter=',', lineterminator='\r\n',
            quoting=csv.QUOTE_MINIMAL,
            quotechar='"',
        )
        writer.writerows(description_rows)


if __name__ == '__main__':
    main()
