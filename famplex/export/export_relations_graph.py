import csv
import os

import pygraphviz as pgv

from famplex.constants import EXPORT_DIR, RELATIONS_TSV_PATH

DEFAULT_RELATIONS_GRAPH_PATH = os.path.join(EXPORT_DIR, 'relations_graph.pdf')

HGNC_STYLE = {
    'color': 'lightgray',
    'style': 'filled',
    'fontname': 'arial',
}
FAMPLEX_STYLE = {
    'color': 'pink',
    'style': 'filled',
    'fontname': 'arial',
}
EDGE_STYLE = {
    'fontname': 'arial',
}


def node_label(db, db_id, name):
    return '%s:%s ! %s' % (db, db_id, name)


def main(output_file=DEFAULT_RELATIONS_GRAPH_PATH):
    graph = pgv.AGraph(name='relations', directed=True, rankdir='LR')

    with open(RELATIONS_TSV_PATH) as f:
        for ns1, id1, name1, rel, ns2, id2, name2 in csv.reader(f, delimiter='\t'):
            sub, obj = node_label(ns1, id1, name1), node_label(ns2, id2, name2)

            for db, label in ((ns1, sub), (ns2, obj)):
                if db == 'HGNC':
                    graph.add_node(label, **HGNC_STYLE)
                elif db == 'FPLX':
                    graph.add_node(label, **FAMPLEX_STYLE)

            graph.add_edge(sub, obj, label=rel, **EDGE_STYLE)

    graph.draw(output_file, prog='dot')


if __name__ == '__main__':
    main()
