import collections
import csv
import datetime
import os

from famplex.constants import (
    ENTITIES_TSV_PATH, EQUIVALENCES_TSV_PATH, EXPORT_DIR, GROUNDING_MAP_TSV_PATH, RELATIONS_TSV_PATH,
)

DEFAULT_OBO_PATH = os.path.join(EXPORT_DIR, 'famplex.obo')

Synonym = collections.namedtuple('Synonym', ['name', 'status'])


class Reference:
    def __init__(self, db, identifier, name=None):
        self.db = db
        self.id = identifier
        self.name = name


ROOT_REFERENCE = Reference('FPLX', '000000', 'famplex')


class OboTerm:
    def __init__(
            self,
            *,
            term_id,
            description=None,
            references=None,
            rels=None,
            synonyms=None,
            xrefs=None,
    ):
        self.term_id = term_id
        self.description = description
        self.references = references
        self.rels = rels or {}
        self.synonyms = synonyms or []
        self.xrefs = xrefs or []

    def to_obo(self):
        obo_str = '[Term]\n'
        obo_str += 'id: %s:%s\n' % (self.term_id.db, self.term_id.id)
        obo_str += 'name: %s\n' % self.term_id.name
        if self.description is not None:
            obo_str += 'def: "%s" [%s]\n' % (self.description, ','.join(self.references))

        for synonym in self.synonyms:
            obo_str += 'synonym: "%s" %s []\n' % (synonym.name, synonym.status)

        for xref in self.xrefs:
            if xref.db == 'BEL':
                entry = 'BEL:"%s"' % xref.id
            elif xref.db == 'NXP':
                entry = 'NEXTPROT-FAMILY:%s' % xref.id[3:]
            elif xref.db == 'PF':
                entry = 'XFAM:%s' % xref.id
            elif xref.db == 'GO':
                entry = xref.id
            else:
                entry = '%s:%s' % (xref.db, xref.id)

            if xref.name is not None:
                entry += f' ! {xref.name}'

            obo_str += 'xref: %s\n' % entry

        for rel_type, rel_entries in self.rels.items():
            for ref in rel_entries:
                if rel_type == 'is_a':
                    obo_str += '%s: %s:%s' % (rel_type, ref.db, ref.id)
                else:
                    obo_str += 'relationship: %s %s:%s' % (rel_type, ref.db, ref.id)
                if ref.name is not None:
                    obo_str += f' ! {ref.name}'
                obo_str += '\n'

        return obo_str

    def __str__(self):
        return self.to_obo()


ROOT_OBO_TERM = OboTerm(term_id=ROOT_REFERENCE)


def get_obo_terms():
    obo_terms = [ROOT_OBO_TERM]

    with open(ENTITIES_TSV_PATH) as fh:
        reader = csv.reader(
            fh,
            delimiter='\t',
            lineterminator='\r\n',
            quoting=csv.QUOTE_MINIMAL,
        )
        entities = {
            fplx_id: (
                fplx_name,
                None if description == '.' else description,
                None if references == '.' else [r.strip() for r in references.split(',')],
            )
            for fplx_id, fplx_name, description, references in reader
        }

    with open(EQUIVALENCES_TSV_PATH, 'r') as fh:
        reader = csv.reader(
            fh,
            delimiter='\t',
            lineterminator='\r\n',
            quoting=csv.QUOTE_MINIMAL,
        )
        equivalences = collections.defaultdict(list)
        for xref_db, xref_id, fplx_id, _ in reader:
            equivalences[fplx_id].append((xref_db, xref_id))

    with open(GROUNDING_MAP_TSV_PATH) as fh:
        reader = csv.reader(
            fh,
            delimiter='\t',
            lineterminator='\r\n',
            quoting=csv.QUOTE_MINIMAL,
        )
        textrefs = collections.defaultdict(list)
        for textref, db, db_id, _ in reader:
            if db == 'FPLX':
                textrefs[db_id].append(textref)

    with open(RELATIONS_TSV_PATH) as fh:
        rels = {
            entity: collections.OrderedDict(
                is_a=[],
                part_of=[],
                inverse_is_a=[],
                has_part=[],
            )
            for entity in entities
        }
        reader = csv.reader(
            fh,
            delimiter='\t',
            lineterminator='\r\n',
            quoting=csv.QUOTE_MINIMAL,
        )
        for sub_db, sub_id, sub_name, rel, obj_db, obj_id, obj_name in reader:
            if sub_db == 'FPLX':
                if rel == 'isa':
                    rels[sub_id]['is_a'].append(Reference(obj_db, obj_id, obj_name))
                elif rel == 'partof':
                    rels[sub_id]['part_of'].append(Reference(obj_db, obj_id, obj_name))
            if obj_db == 'FPLX':
                if rel == 'isa':
                    rels[obj_id]['inverse_is_a'].append(Reference(sub_db, sub_id, sub_name))
                elif rel == 'partof':
                    rels[obj_id]['has_part'].append(Reference(sub_db, sub_id, sub_name))

    # For each entity in famplex
    for fplx_id, (fplx_name, description, references) in entities.items():
        name = fplx_name.replace('_', '-')

        term_id = Reference('FPLX', fplx_id, name)

        synonyms = [  # Get synonyms
            Synonym(textref, 'EXACT')
            for textref in textrefs.get(fplx_id, [])
        ]

        xrefs = [  # Get xrefs
            Reference(xref_db, xref_id)
            for xref_db, xref_id in equivalences.get(fplx_id, [])
        ]
        # If the entity has no isa relations, connect it to the root
        if not rels[fplx_id]['is_a'] and not rels[fplx_id]['part_of']:
            rels[fplx_id]['is_a'].append(ROOT_REFERENCE)

        obo_term = OboTerm(
            term_id=term_id,
            description=description,
            references=references,
            rels=rels[fplx_id],
            synonyms=synonyms,
            xrefs=xrefs,
        )
        obo_terms.append(obo_term)

    return obo_terms


def save_obo_terms(obo_terms, output_file):
    date = datetime.datetime.today()
    date_str = date.strftime('%d:%m:%Y %H:%M')
    with open(output_file, 'w') as fh:
        fh.write('format-version: 1.2\n')
        fh.write('date: %s\n' % date_str)
        fh.write(""" 
[Typedef]
id: part_of
name: part of
namespace: external
xref: BFO:0000050
is_transitive: true

[Typedef]
id: inverse_is_a
name: inverse is_a

[Typedef]
id: has_part
name: has part

""")

        for term in obo_terms:
            obo_str = term.to_obo()
            fh.write(obo_str)
            fh.write('\n')


def main():
    obo_terms = get_obo_terms()
    save_obo_terms(obo_terms, DEFAULT_OBO_PATH)


if __name__ == '__main__':
    main()
