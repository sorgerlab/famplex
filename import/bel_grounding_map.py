from common import load_entity_list, load_equivalences, load_grounding_map


def main():
    equivalences = load_equivalences('../equivalences.csv')
    has_bel_mapping = set()
    for source_db, source_id, be_id in equivalences:
        if source_db == 'BEL':
            has_bel_mapping.add(be_id)

    gm = load_grounding_map('../grounding_map.csv')
    has_grounding = set()
    for text, refs in gm.items():
        be_id = refs.get('FPLX')
        if be_id:
            has_grounding.add(be_id)

    entities = load_entity_list('../entities.csv')

    no_grounding = sorted(list(set(entities) - set(has_grounding)))
    bel_no_grounding = sorted(list(set(has_bel_mapping) & set(no_grounding)))

    print('# entities: %d' % len(entities))
    print('# has grounding: %d' % len(has_grounding))
    print('# no grounding: %d' % len(no_grounding))
    print('# no grounding but has BEL mapping: %d' % len(bel_no_grounding))

    bel_no_grounding_mapped = set()
    for source_db, source_id, be_id in equivalences:
        if be_id in bel_no_grounding:
            if source_db == 'BEL':
                bel_no_grounding_mapped.add(source_id)

    with open('../../indra/data/large_corpus.bel', 'r') as fh:
        large_corpus = fh.read()

    bel_counts = {}
    for bel_fam in bel_no_grounding_mapped:
        search = 'H:"%s"' % bel_fam
        bel_counts[bel_fam] = large_corpus.count(search)

    bel_to_lookup = sorted(bel_counts.items(), key=lambda x: x[1], reverse=True)
    bel_to_lookup = [b for b in bel_to_lookup if b[1] > 0]


if __name__ == '__main__':
    main()
