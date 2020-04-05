from __future__ import print_function, unicode_literals
import csv
import sys
from collections import Counter


def read_csv(fh, delimiter, quotechar):
    if sys.version_info.major < 3:
        csvreader = csv.reader(fh, delimiter=bytes(delimiter),
                               quotechar=bytes(quotechar))
        rows = [[cell.decode('utf-8') for cell in row] for row in csvreader]
    else:
        csvreader = csv.reader(fh, delimiter=delimiter, quotechar=quotechar)
        rows = [row for row in csvreader]
    return rows


def load_csv(filename):
    with open(filename) as f:
        rows = read_csv(f, ',', '"')
    return rows


def load_grounding_map(filename):
    gm_rows = load_csv(filename)
    gm_tuples = []
    check_rows(gm_rows, 7, filename)
    g_map = {}
    for row in gm_rows:
        gm_tuples.append(tuple(row))
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
    return g_map, tuple(gm_tuples)


def check_file_rows(filename, row_length):
    with open(filename) as f:
        rows = read_csv(f, ',', '"')
    check_rows(rows, row_length, filename)


def check_rows(rows, row_length, filename):
    for ix, row in enumerate(rows):
        if len(row) != row_length:
            print("ERROR: Line %d in file %s has %d columns, should be %d" %
                  ((ix + 1), filename, len(row), row_length))


def load_entity_list(filename):
    with open(filename) as f:
        rows = read_csv(f, ',', '"')
    check_rows(rows, 1, filename)
    entities = [row[0] for row in rows]
    return entities


def load_relationships(filename):
    relationships = []
    with open(filename) as f:
        rows = read_csv(f, ',', '"')
    check_rows(rows, 5, filename)
    for row in rows:
        relationships.append(((row[0], row[1]), row[2], (row[3], row[4])))
    return relationships


def load_equivalences(filename):
    equivalences = []
    with open(filename) as f:
        rows = read_csv(f, ',', '"')
    check_rows(rows, 3, filename)
    for row in rows:
        equivalences.append((row[0], row[1], row[2]))
    return equivalences


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


if __name__ == '__main__':
    signal_error = False
    entities = load_entity_list('entities.csv')
    relationships = load_relationships('relations.csv')
    equivalences = load_equivalences('equivalences.csv')
    gm, gm_tuples = load_grounding_map('grounding_map.csv')
    check_file_rows('gene_prefixes.csv', 3)

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
        if db_refs is not None:
            for db_key, db_id in db_refs.items():
                if db_key == 'FPLX' and db_id not in entities:
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
                print("WARNING: %s has PUBCHEM ID (%s) but no CHEBI ID."
                      % (text, db_refs['PUBCHEM']))
            if p_and_c == 'pubchem_missing':
                pubchem_id_missing.append(db_refs['CHEBI'])
                print("WARNING: %s has CHEBI ID (%s) but no PUBCHEM ID." %
                      (text, db_refs['CHEBI']))

    print()
    print("-- Checking for undeclared FamPlex IDs in relationships file --")
    # Load the relationships
    # Check the relationships for consistency with entities
    entities_missing_rel = []
    for subj, rel, obj in relationships:
        for term in (subj, obj):
            term_ns = term[0]
            term_id = term[1]
            if term_ns == 'FPLX' and term_id not in entities:
                entities_missing_rel.append(term_id)
                print("ERROR: ID %s referenced in relations "
                      "is not in entities list." % term_id)
                signal_error = True
    print()
    print("-- Checking for valid namespaces in relations --")
    for ix, (subj, rel, obj) in enumerate(relationships):
        for term in (subj, obj):
            term_ns = term[0]
            if term_ns not in ('FPLX', 'HGNC', 'UP'):
                print("ERROR: row %d: Invalid namespace in relations.csv: %s" %
                      (ix+1, term_ns))
                signal_error = True

    # This check requires the indra package
    try:
        from indra.databases import hgnc_client
        print()
        print("-- Checking for invalid HGNC Symbols in relationships file --")
        for subj, rel, obj in relationships:
            for term in (subj, obj):
                term_ns = term[0]
                term_id = term[1]
                if term_ns == 'HGNC':
                    hgnc_id = hgnc_client.get_hgnc_id(term_id)
                    if not hgnc_id:
                        print("ERROR: Symbol %s referenced in relations is "
                              "not a valid HGNC Symbol." % term_id)
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
        print("-- Checking for invalid HGNC Symbols in grounding map --")
        for text, db_refs in gm.items():
            if db_refs is not None:
                for db_key, db_id in db_refs.items():
                    if db_key == 'HGNC':
                        hgnc_id = hgnc_client.get_hgnc_id(db_id)
                        if not hgnc_id:
                            print("ERROR: Symbol %s in grounding map is "
                                   "not a valid HGNC Symbol." % db_id)
                            signal_error = True
    except ImportError as e:
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
    for ent in entities:
        found = False
        for subj, rel, obj in relationships:
            subj_ns = subj[0]
            subj_id = subj[1]
            obj_ns = obj[0]
            obj_id = obj[1]
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
    for eq_ns, eq_id, be_id in equivalences:
        if be_id not in entities:
            signal_error = True
            entities_missing_eq.append(be_id)
            print("ERROR: ID %s referenced in equivalences "
                  "is not in entities list." % be_id)
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
        logging.getLogger('requests').setLevel(logging.CRITICAL)
        logging.getLogger('urllib3').setLevel(logging.CRITICAL)
        print()
        print("-- Checking for invalid PUBCHEM CIDs in grounding map --")
        pubchem_url = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/' + \
                      'cid/%s/description/XML'
        for text, db_refs in gm.items():
            if db_refs is not None:
                for db_key, db_id in db_refs.items():
                    if db_key == 'PUBCHEM':
                        res = requests.get(pubchem_url % db_id)
                        if res.status_code != 200:
                            print("ERROR: ID %s in grounding map is "
                                  "not a valid PUBCHEM ID." % db_id)
    except ImportError:
        pass

    if signal_error:
        sys.exit(1)
    sys.exit(0)
