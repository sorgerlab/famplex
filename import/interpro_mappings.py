import json
import os
from collections import defaultdict

from common import get_child_map, jaccard_index, read_csv
from indra.databases import uniprot_client


def get_ip_families_for_be(be_up_ids, cache_file=None):
    if cache_file is not None and os.path.exists(cache_file):
        with open(cache_file, 'rt') as f:
            ipfs = [line.strip() for line in f.readlines()]
        return ipfs

    # If not cached, read from file
    ip_families_for_be = set()
    with open('protein2ipr.dat', 'rt') as f:
        counter = 0
        while True:
            if counter % 1000000 == 0:
                print("At line %d" % counter)
            line = f.readline()
            if not line:
                continue
            entries = line.strip().split('\t')
            up_id, ip_id = entries[0:2]
            if up_id in be_up_ids:
                print(entries)
                ip_families_for_be.add(ip_id)
            counter += 1

    return ip_families_for_be


def get_ip_family_members(
        ip_families_for_be,
        ip_datafile='protein2ipr.dat',
        cache_file=None,
):
    # Check if Interpro info is cached
    if cache_file is not None:
        with open(cache_file, 'rt') as f:
            ip_family_members = json.load(f)
        return ip_family_members
    # If not cached, load from file
    ip_family_members = {}
    with open(ip_datafile, 'rt') as f:
        counter = 0
        for line in f:
            if counter % 100000 == 0:
                print("At line %d" % counter)
            if line == '' or line.strip() == '':
                continue
            entries = line.strip().split('\t')
            up_id, ip_id, ip_name = entries[0:3]
            if ip_id in ip_families_for_be and uniprot_client.is_human(up_id):
                ip_fam_info = ip_family_members.get(ip_id)
                if ip_fam_info is None:
                    ip_family_members[ip_id] = {
                        'name': ip_name,
                        'members': [up_id]
                    }
                else:
                    ip_fam_info['members'].append(up_id)
            counter += 1
    with open('ip_family_members.json', 'wt') as f:
        json.dump(ip_family_members, f, indent=2)
    return ip_family_members


def load_uniprot(filename):
    with open(filename, 'rt') as f:
        entries = read_csv(f, delimiter='\t', quotechar='"')
    up_ids = [row[0] for row in entries[1:]]
    return up_ids


def get_mappings(be_child_map, ip_family_members, uniprot_ids,
                 jaccard_cutoff=1.):
    mappings = defaultdict(list)
    up_set = set(uniprot_ids)
    for be_id, be_children in be_child_map.items():
        print("Mapping %s" % be_id)
        # Skip empty sets
        be_set = set(be_children)
        if not be_set:
            continue
        for ip_id, ip_info in ip_family_members.items():
            ip_name = ip_info['name']
            members = ip_info['members']
            ip_set = set(members).intersection(up_set)
            # Skip empty sets
            if not ip_set:
                continue
            jacc = jaccard_index(be_set, ip_set)
            if jacc >= jaccard_cutoff:
                mapping = {
                    'id': ip_id, 'name': ip_name,
                    'members': list(ip_set), 'jaccardIndex': jacc,
                    'equivalence': 'IP,%s,%s' % (ip_id, be_id)
                }
                mappings[be_id].append(mapping)
        if be_id in mappings:
            mappings[be_id].sort(key=lambda d: d['jaccardIndex'], reverse=True)
    return mappings


def main():
    be_child_map = get_child_map()
    be_up_ids = [up_id for child_list in be_child_map.values()
                 for up_id in child_list]

    ip_families_for_be = get_ip_families_for_be(
        be_up_ids,
        cache_file='ip_families_for_be.txt',
    )
    ip_family_members = get_ip_family_members(
        ip_families_for_be,
        cache_file='ip_family_members.json',
    )
    up_ids = load_uniprot('uniprot_reviewed_human.tsv')
    mappings = get_mappings(
        be_child_map,
        ip_family_members,
        up_ids,
        jaccard_cutoff=1,
    )
    for be_id, map_list in mappings.items():
        for map_info in map_list:
            ip_id = map_info['id']
            print("IP,%s,%s" % (ip_id, be_id))


if __name__ == '__main__':
    main()
