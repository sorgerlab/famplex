import csv
import json
import os
import requests
from functools import lru_cache
from collections import defaultdict

import common


@lru_cache(10000)
def rx_id_from_up_id(up_id):
    """Get the Reactome Stable ID for a given Uniprot ID."""
    react_search_url = 'http://www.reactome.org/ContentService/search/query'
    params = {'query': up_id, 'cluster': 'true', 'species':'Homo sapiens'}
    headers = {'Accept': 'application/json'}
    res = requests.get(react_search_url, headers=headers, params=params)
    if not res.status_code == 200:
        return None
    json = res.json()
    results = json.get('results')
    if not results:
        print('No results for %s' % up_id)
        return None
    stable_ids = []
    for result in results:
        entries = result.get('entries')
        for entry in entries:
            stable_id = entry.get('stId')
            if not stable_id:
                continue
            name = entry.get('name')
            stable_ids.append(stable_id)
    return stable_ids


@lru_cache(100000)
def up_id_from_rx_id(reactome_id):
    """Get the Uniprot ID (referenceEntity) for a given Reactome Stable ID."""
    react_url = 'http://www.reactome.org/ContentService/data/query/' \
                + reactome_id + '/referenceEntity'
    res = requests.get(react_url)
    if not res.status_code == 200:
        return None
    _, entry, entry_type = res.text.split('\t')
    if entry_type != 'ReferenceGeneProduct':
        return None
    id_entry = entry.split(' ')[0]
    db_ns, db_id = id_entry.split(':')
    if db_ns != 'UniProt':
        return None
    return db_id


@lru_cache(10000)
def get_participants(reactome_id):
    """Get Uniprot IDs of members of a Reactome DefinedSet or CandidateSet."""
    react_url = 'http://www.reactome.org/ContentService/data/event/' \
                + reactome_id + '/participatingReferenceEntities'
    headers = {'Accept': 'application/json'}
    res = requests.get(react_url, headers=headers)
    if not res.status_code == 200:
        return []
    json = res.json()
    up_ids = []
    for res in json:
        if not res.get('databaseName') == 'UniProt':
            continue
        up_id = res.get('identifier')
        if up_id is not None:
            up_ids.append(up_id)
    return up_ids


@lru_cache(10000)
def get_subunits(complex_id):
    """Get Uniprot IDs of subunits of a Reactome Complex."""
    react_url = 'http://www.reactome.org/ContentService/data/complex/' \
                + complex_id + '/subunits'
    headers = {'Accept': 'application/json'}
    res = requests.get(react_url, headers=headers)
    if not res.status_code == 200:
        return []
    json = res.json()
    up_ids = []
    for subunit in json:
        subunit_rx_id = subunit.get('stId')
        if not subunit_rx_id:
            continue
        up_id = up_id_from_rx_id(subunit_rx_id)
        if up_id:
            up_ids.append(up_id)
    return up_ids


@lru_cache(10000)
def _get_parents(stable_id):
    """Recursively get all parents of a Reactome ID."""
    react_data_url = 'http://www.reactome.org/ContentService/data/entity/' + \
                     stable_id + '/componentOf'
    headers = {'Accept': 'application/json'}
    res = requests.get(react_data_url, headers=headers)
    if not res.status_code == 200:
        return []
    json = res.json()
    names = []
    stable_ids = []
    schema_classes = []
    for parent_group in json:
        if not parent_group.get('type') in \
                            ['hasComponent', 'hasMember', 'hasCandidate']:
            continue
        names += parent_group.get('names')
        stable_ids += parent_group.get('stIds')
        schema_classes += parent_group.get('schemaClasses')
    parents_at_this_level = list(zip(names, stable_ids, schema_classes))
    parents_at_next_level_up = []
    for p_name, p_id, sc in parents_at_this_level:
        parents_at_next_level_up += _get_parents(p_id)
    return parents_at_this_level + parents_at_next_level_up


@lru_cache(10000)
def get_all_parents(up_id):
    """Get all parents for all Reactome IDs linked to a Uniprot ID."""
    linked_stable_ids = rx_id_from_up_id(up_id)
    if linked_stable_ids is None:
        return ([], [])
    parents = []
    for ls_id in linked_stable_ids:
        parents += _get_parents(ls_id)
    sets = [tup for tup in parents if tup[2] != 'Complex']
    complexes = [tup for tup in parents if tup[2] == 'Complex']
    return sets, complexes


def get_rx_family_members(up_ids, cache_file=None):
    """Get dictionary mapping Reactome sets/complexes to member Uniprot IDs."""
    # Check to see if we're loading from a cache
    if cache_file is not None and os.path.exists(cache_file):
        with open(cache_file, 'rt') as f:
            rx_family_members = json.load(f)
        return rx_family_members

    # Not cached, get members from the Reactome web service
    rx_family_members = {}
    for be_id, children_up_ids in be_child_map.items():
        print("Getting family info for %s" % be_id)
        # For every child, get all parents in Reactome
        rx_sets = set([])
        rx_complexes = set([])
        for up_id in children_up_ids:
            sets, complexes = get_all_parents(up_id)
            rx_sets = rx_sets.union(sets)
            rx_complexes = rx_complexes.union(complexes)
        # Next, for all of the sets, get their membership
        for rx_set in rx_sets.union(rx_complexes):
            name, rx_id, rx_type = rx_set
            # If we've already gotten info for this Reactome Set/Complex,
            # we can skip it
            if rx_id in rx_family_members:
                continue
            # Otherwise, get members
            if rx_type == 'DefinedSet' or rx_type == 'CandidateSet':
                rx_members = set(get_participants(rx_id))
            elif rx_type == 'Complex':
                rx_members = set(get_subunits(rx_id))
            else:
                print("Unrecognized type %s for %s, %s" %
                      (rx_type, name, rx_id))
                continue
            # Save info in dict
            rx_family_members[rx_id] = {'name': name, 'type': rx_type,
                                        'members': list(rx_members)}
    # Save to JSON
    with open('rx_family_members.json', 'wt') as f:
        json.dump(rx_family_members, f, indent=2)
    # Return
    return rx_family_members


def get_mappings(be_child_map, rx_family_members, jaccard_cutoff=1.):
    """Find matches between FPLX and Reactome families/complexes."""
    mappings = defaultdict(list)
    for be_id, be_children in be_child_map.items():
        # Skip empty sets
        be_set = set(be_children)
        if not be_set:
            continue
        for rx_id, rx_info in rx_family_members.items():
            rx_name = rx_info['name']
            rx_type = rx_info['type']
            rx_set = set(rx_info['members'])
            # Skip empty sets
            if not rx_set:
                continue
            jacc = common.jaccard_index(be_set, rx_set)
            if jacc >= jaccard_cutoff:
                mapping = {'reactomeId': rx_id, 'reactomeType': rx_type,
                           'reactomeName': rx_name,
                           'reactomeMembers': list(rx_set),
                           'jaccardIndex': jacc}
                mappings[be_id].append(mapping)
        if be_id in mappings:
            mappings[be_id].sort(key=lambda d: d['jaccardIndex'], reverse=True)
    return mappings


if __name__ == '__main__':
    be_child_map = common.get_child_map()
    be_up_ids = [up_id for child_list in be_child_map.values()
                       for up_id in child_list]
    rx_family_members = get_rx_family_members(be_up_ids,
                                          cache_file='rx_family_members.json')
    mappings = get_mappings(be_child_map, rx_family_members, jaccard_cutoff=1.)
    with open('reactome_mappings.json', 'wt') as f:
        json.dump(mappings, f, indent=2)
