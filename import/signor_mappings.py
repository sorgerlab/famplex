"""Propose mappings between FamPlex and Signor families based on members."""

import csv
from collections import defaultdict

from common import get_child_map, jaccard_index


def get_signor_pf_map(pf_filename):
    signor_pf = {}
    with open(pf_filename, 'rt') as f:
        csvreader = csv.reader(f, delimiter=';')
        next(csvreader)  # Skip header row
        for row in csvreader:
            pf_id, pf_name, pf_member_list = row
            up_ids = [s.strip() for s in pf_member_list.split(',')]
            signor_pf[pf_id] = (pf_name, up_ids)
    return signor_pf


def get_mappings(fplx_child_map, signor_pf_map, jaccard_cutoff=1.):
    mappings = defaultdict(list)
    for signor_id, signor_info in signor_pf_map.items():
        signor_name = signor_info[0]
        signor_set = set(signor_info[1])
        # Skip empty sets
        if not signor_set:
            continue
        for fplx_id, fplx_children in fplx_child_map.items():
            # Skip empty sets
            fplx_set = set(fplx_children)
            if not fplx_set:
                continue
            jacc = jaccard_index(fplx_set, signor_set)
            if jacc >= jaccard_cutoff:
                mappings[signor_id].append({
                    'signorId': signor_id,
                    'signorName': signor_name,
                    'signorMembers': list(signor_set),
                    'fplxId': fplx_id,
                    'fplxMembers': list(fplx_set),
                    'eqEntry': 'SIGNOR,%s,%s' % (signor_id, fplx_id),
                    'jaccardIndex': jacc,
                })

        if signor_id in mappings:
            mappings[signor_id].sort(key=lambda d: d['jaccardIndex'], reverse=True)

    return dict(mappings)


def main():
    fplx_child_map = get_child_map()
    signor_pf_map = get_signor_pf_map('SIGNOR_PF.csv')
    mappings = get_mappings(fplx_child_map, signor_pf_map, jaccard_cutoff=1.)
    for k, v in mappings.items():
        print(v[0]['eqEntry'])


if __name__ == '__main__':
    main()
