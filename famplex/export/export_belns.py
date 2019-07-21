# -*- coding: utf-8 -*-

"""Output FamPlex as a BEL namespace using the :mod:`bel_resources` package."""

import os

from bel_resources import write_namespace
from bel_resources.constants import NAMESPACE_DOMAIN_GENE

from famplex.constants import ENTITIES_TSV_PATH, EXPORT_DIR

DEFAULT_BELNS_PATH = os.path.join(EXPORT_DIR, 'famplex.belns')


def _get_entities():
    with open(ENTITIES_TSV_PATH) as fh:
        return {
            l.strip().split('\t')[1]: 'GRPC'
            for l in fh.readlines()
        }


def _write_namespace(values, output_file):
    with open(output_file, 'w') as file:
        write_namespace(
            namespace_name='FamPlex',
            namespace_keyword='FPLX',
            namespace_domain=NAMESPACE_DOMAIN_GENE,
            author_name='John Bachman and Ben Gyori',
            citation_name='FamPlex',
            values=values,
            namespace_description='FamPlex is a collection of resources for grounding biological entities from text '
                                  'and describing their hierarchical relationships.',
            namespace_query_url='http://identifiers.org/fplx/',
            author_copyright='CC0 1.0 Universal',
            citation_url='https://github.com/sorgerlab/famplex',
            case_sensitive=True,
            cacheable=True,
            file=file,
        )


def main(output_file=DEFAULT_BELNS_PATH):
    entities = _get_entities()
    _write_namespace(entities, output_file)


if __name__ == '__main__':
    main()
