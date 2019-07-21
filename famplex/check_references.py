# -*- coding: utf-8 -*-

"""Check the validity and integrity of the FamPlex resources."""

import csv
import sys
from collections import Counter, defaultdict

from famplex.constants import ENTITIES_TSV_PATH, EQUIVALENCES_TSV_PATH, GROUNDING_MAP_TSV_PATH, RELATIONS_TSV_PATH


def load_csv(path):
    """Load the rows of a TSV file."""
    with open(path) as fh:
        reader = csv.reader(
            fh,
            delimiter=',',
            lineterminator='\r\n',
            quoting=csv.QUOTE_MINIMAL,
            quotechar='"',
        )
        return tuple(tuple(row) for row in reader)


def load_grounding_map(filename):
    gm_rows = load_csv(filename)
    check_rows(gm_rows, 4, filename)
    g_map = defaultdict(dict)
    for text, db, db_id, _ in gm_rows:
        g_map[text][db] = db_id
    return g_map, gm_rows


def check_file_rows(filename, row_length):
    rows = load_csv(filename)
    check_rows(rows, row_length, filename)


def check_rows(rows, row_length, filename):
    for ix, row in enumerate(rows, start=1):
        if len(row) != row_length:
            print("ERROR: Line %d in file %s has %d columns, should be %d" %
                  (ix, filename, len(row), row_length))


def load_entity_list(filename):
    rows = load_csv(filename)
    check_rows(rows, 4, filename)
    return rows


def load_relationships(filename):
    rows = load_csv(filename)
    check_rows(rows, 7, filename)
    return [
        ((sns, sid, sname), rel, (ons, oid, oname))
        for sns, sid, sname, rel, ons, oid, oname in rows
    ]


def load_equivalences(filename):
    rows = load_csv(filename)
    check_rows(rows, 4, filename)
    return rows


def update_id_prefixes(filename):
    gm_rows = load_csv(filename)
    updated_rows = []
    for row in gm_rows:
        key = row[0]
        keys = [entry for entry in row[1::2]]
        values = [entry for entry in row[2::2]]
        if 'GO' in keys:
            go_ix = keys.index('GO')
            values[go_ix] = 'GO:%s' % values[go_ix]
        if 'CHEBI' in keys:
            chebi_ix = keys.index('CHEBI')
            values[chebi_ix] = 'CHEBI:%s' % values[chebi_ix]
        if 'CHEMBL' in keys:
            chembl_ix = keys.index('CHEMBL')
            values[chembl_ix] = 'CHEMBL%s' % values[chembl_ix]
        updated_row = [key]
        for pair in zip(keys, values):
            updated_row += pair
        updated_rows.append(updated_row)
    return updated_rows


def pubchem_and_chebi(db_refs):
    pubchem_id = db_refs.get('PUBCHEM')
    chebi_id = db_refs.get('CHEBI')
    if pubchem_id and not chebi_id:
        return 'chebi_missing'
    if chebi_id and not pubchem_id:
        return 'pubchem_missing'
    return None


def check_duplicates(entries, entry_label):
    ent_counter = Counter(entries)
    print("-- Checking for duplicate %s --" % entry_label)
    found_duplicates = False
    for ent, freq in ent_counter.items():
        if freq > 1:
            print("ERROR: Duplicate %s in %s." % (str(ent), entry_label))
            found_duplicates = True
    print()
    return found_duplicates


def main():
    signal_error = False
    entities = load_entity_list(ENTITIES_TSV_PATH)
    relationships = load_relationships(RELATIONS_TSV_PATH)
    equivalences = load_equivalences(EQUIVALENCES_TSV_PATH)
    gm, gm_tuples = load_grounding_map(GROUNDING_MAP_TSV_PATH)

    em = {
        eid: ename
        for eid, ename, *_ in entities
    }

    for entries, entry_label in ((entities, 'entities'),
                                 (relationships, 'relationships'),
                                 (equivalences, 'equivalences'),
                                 (gm_tuples, 'groundings')):
        if check_duplicates(entries, entry_label):
            signal_error = True

    print("-- Checking for undeclared FamPlex IDs in grounding map --")
    # Look through grounding map and find all instances with an FPLX db key
    entities_missing_gm = []
    for text, db_refs in gm.items():
        for db_key, db_id in db_refs.items():
            if db_key == 'FPLX' and db_id not in em:
                entities_missing_gm.append(db_id)
                print("ERROR: ID %s referenced in grounding map "
                      "is not in entities list." % db_id)
                signal_error = True

    print()
    print("-- Checking for CHEBI/PUBCHEM IDs--")
    chebi_id_missing = []
    pubchem_id_missing = []
    for text, db_refs in gm.items():
        if db_refs is not None:
            p_and_c = pubchem_and_chebi(db_refs)
            if p_and_c == 'chebi_missing':
                chebi_id_missing.append(db_refs['PUBCHEM'])
                print("WARNING: %s has PubChem ID (pubchem.compound:%s) but no CHEBI ID."
                      % (text, db_refs['PUBCHEM']))
            if p_and_c == 'pubchem_missing':
                pubchem_id_missing.append(db_refs['CHEBI'])
                print("WARNING: %s has ChEBI ID (%s) but no PUBCHEM ID." %
                      (text, db_refs['CHEBI']))

    print()
    print("-- Checking for undeclared FamPlex IDs in relationships file --")
    # Load the relationships
    # Check the relationships for consistency with entities
    entities_missing_rel = []
    for subj, rel, obj in relationships:
        for term_ns, term_id, term_name in (subj, obj):
            if term_ns == 'FPLX' and term_id not in em:
                entities_missing_rel.append(term_id)
                print("ERROR: ID %s referenced in relations "
                      "is not in entities list." % term_id)
                signal_error = True
    print()
    print("-- Checking for valid namespaces in relations --")
    for ix, (subj, rel, obj) in enumerate(relationships, start=1):
        for term_ns, term_id, term_name in (subj, obj):
            if term_ns not in ('FPLX', 'HGNC', 'UP'):
                print("ERROR: row %d: Invalid namespace in relations.csv: %s" %
                      (ix, term_ns))
                signal_error = True

    # This check requires the indra package
    try:
        from indra.databases import hgnc_client

        print()
        print("-- Checking for invalid HGNC IDs in relationships file --")
        for subj, rel, obj in relationships:
            for term_ns, term_id, term_name in (subj, obj):
                if term_ns == 'HGNC':
                    lu_term_name = hgnc_client.get_hgnc_name(term_id)
                    if not lu_term_name:
                        print("ERROR: ID %s referenced in relations is "
                              "not a valid HGNC ID." % term_id)
                        signal_error = True
                    if term_name != lu_term_name:
                        print("ERROR: HGNC %s symbol out of sync."
                              "%s should be %s" % term_id, term_name, lu_term_name)
                        signal_error = True
    except ImportError as e:
        print('HGNC check could not be performed because of import error')
        print(e)
        signal_error = True
        pass

    # This check requires the indra package
    try:
        from indra.databases import hgnc_client

        print()
        print("-- Checking for invalid HGNC IDs in grounding map --")
        for text, db_refs in gm.items():
            if db_refs is not None:
                for db_key, db_id in db_refs.items():
                    if db_key == 'HGNC':
                        lu_term_name = hgnc_client.get_hgnc_name(db_id)
                        if not lu_term_name:
                            print("ERROR: ID %s in grounding map is "
                                  "not a valid HGNC ID." % db_id)
                            signal_error = True
    except ImportError:
        print('HGNC check could not be performed because of import error')
        print(e)
        signal_error = True
        pass

    # This check requires a ChEBI resource file to be available. You
    # can obtain it from here: ftp://ftp.ebi.ac.uk/pub/databases/
    #                          chebi/Flat_file_tab_delimited/compounds.tsv.gz
    try:
        with open('chebi_compounds.tsv', 'rt') as fh:
            chebi_ids = [lin.split('\t')[2] for lin in fh.readlines()]
        print()
        print("-- Checking for invalid ChEBI IDs in grounding map --")
        for text, db_refs in gm.items():
            if db_refs is not None:
                for db_key, db_id in db_refs.items():
                    if db_key == 'CHEBI':
                        if db_id not in chebi_ids:
                            print("ERROR: ID %s in grounding map is "
                                  "not a valid CHEBI ID." % db_id)
    except IOError:
        pass

    print()
    print("-- Checking for FamPlexes whose relationships are undefined  --")
    # Check the relationships for consistency with entities
    rel_missing_entities = []
    for ent in em:
        found = False
        for (subj_ns, subj_id, _), rel, (obj_ns, obj_id, _) in relationships:
            if subj_ns == 'FPLX' and subj_id == ent:
                found = True
                break
            if obj_ns == 'FPLX' and obj_id == ent:
                found = True
                break
        if not found:
            rel_missing_entities.append(ent)
            print("WARNING: ID %s has no known relations." % ent)

    print()
    print("-- Checking for non-existent FamPlexes in equivalences  --")
    entities_missing_eq = []
    for eq_ns, eq_id, fplx_id, _ in equivalences:
        if fplx_id not in em:
            signal_error = True
            entities_missing_eq.append(fplx_id)
            print("ERROR: ID %s referenced in equivalences "
                  "is not in entities list." % fplx_id)
    print()
    print("-- Checking for duplicate equivalences --")
    equiv_counter = Counter(equivalences)
    duplicate_eq = [item for item, count in equiv_counter.items()
                    if count > 1]
    if duplicate_eq:
        print("ERROR: Duplicate equivalences found:")
        for dup in duplicate_eq:
            print(dup)

    # This check requires the requests package to be installed
    try:
        import requests
        import logging
        from tqdm import tqdm
    except ImportError:
        pass
    else:
        logging.getLogger('requests').setLevel(logging.CRITICAL)
        logging.getLogger('urllib3').setLevel(logging.CRITICAL)
        print()
        print("-- Checking for invalid PUBCHEM CIDs in grounding map --")
        pubchem_url = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/' + \
                      'cid/%s/description/XML'

        pubchem_ids = {
            db_id
            for text, db_refs in gm.items()
            for db_key, db_id in db_refs.items()
            if db_key == 'PUBCHEM'
        }
        for db_id in tqdm(pubchem_ids):
            res = requests.get(pubchem_url % db_id)
            if res.status_code != 200:
                print("ERROR: ID %s in grounding map is "
                      "not a valid PUBCHEM ID." % db_id)

    if signal_error:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
