"""Scripts for ensuring a canonical ordering of the famplex resource files."""

import csv
import os

from famplex.load import _load_csv

HERE = os.path.dirname(os.path.abspath(__file__))
RESOURCES_PATH = os.path.join(HERE, 'famplex', 'resources')


def _write_csv(filename, rows):
    with open(filename, 'w') as file:
        writer = csv.writer(
            file,
            delimiter=str(u','),
            lineterminator='\r\n',
            quoting=csv.QUOTE_MINIMAL,
            quotechar=str(u'"'),
        )
        writer.writerows(rows)


def _lint_csv(path, has_header: bool = False):
    rows = _load_csv(path)
    if has_header:
        first, *rest = rows
        new_rows = [first, *sorted(rest)]
    else:
        new_rows = sorted(rows)
    _write_csv(path, new_rows)


def main():
    for resource, has_header in [
        ('entities.csv', False),
        ('relations.csv', False),
        ('equivalences.csv', False),
        ('grounding_map.csv', False),
        ('gene_prefixes.csv', True),
        ('descriptions.csv', False),
    ]:
        path = os.path.join(HERE, resource)
        _lint_csv(path, has_header=has_header)


if __name__ == '__main__':
    main()
