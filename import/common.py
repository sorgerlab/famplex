import csv
import sys

from indra.databases import hgnc_client
from indra.preassembler.hierarchy_manager import hierarchies
from indra.statements import Agent
from indra.tools.expand_families import Expander


def read_csv(fh, delimiter, quotechar):
    if sys.version_info.major < 3:
        csvreader = csv.reader(fh, delimiter=bytes(delimiter),
                               quotechar=bytes(quotechar))
    else:
        csvreader = csv.reader(fh, delimiter=delimiter, quotechar=quotechar)
    rows = [row for row in csvreader]
    return rows


def load_csv(filename):
    with open(filename) as f:
        rows = read_csv(f, ',', '"')
    return rows


def load_equivalences(filename):
    equivalences = []
    with open(filename) as f:
        rows = read_csv(f, ',', '"')
        for row in rows:
            equivalences.append((row[0], row[1], row[2]))
    return equivalences


def load_grounding_map(filename):
    gm_rows = load_csv(filename)
    g_map = {}
    for row in gm_rows:
        key = row[0]
        db_refs = {'TEXT': key}
        keys = [entry for entry in row[1::2] if entry != '']
        values = [entry for entry in row[2::2] if entry != '']
        if len(keys) != len(values):
            print('ERROR: Mismatched keys and values in row %s' % str(row))
            continue
        else:
            db_refs.update(dict(zip(keys, values)))
            if len(db_refs.keys()) > 1:
                g_map[key] = db_refs
            else:
                g_map[key] = None
    return g_map


def load_entity_list(filename):
    with open(filename) as f:
        rows = read_csv(f, ',', '"')
    entities = [row[0] for row in rows]
    return entities


def get_child_map():
    """Get dictionary mapping FPLX IDs to Uniprot IDs of all children."""
    entities = load_entity_list('../entities.csv')

    be_agents = [Agent(be_id, db_refs={'FPLX': be_id})
                 for be_id in entities]
    ex = Expander(hierarchies)
    child_map = {}
    for be_agent in be_agents:
        children = ex.get_children(be_agent)
        children_up_ids = []
        for child_ns, child_id in children:
            if child_ns == 'HGNC':
                hgnc_id = hgnc_client.get_hgnc_id(child_id)
                up_id = hgnc_client.get_uniprot_id(hgnc_id)
                children_up_ids.append(up_id)
            else:
                print("Unhandled NS: %s %s" % (child_ns, child_id))
                continue
        child_map[be_agent.name] = list(set(children_up_ids))
    return child_map


def jaccard_index(a, b):
    int_size = len(a.intersection(b))
    union_size = len(a.union(b))
    return int_size / float(union_size)
