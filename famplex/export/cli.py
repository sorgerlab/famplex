# -*- coding: utf-8 -*-

"""A command line interface for FamPlex exporters."""

import famplex.export.export_belns
import famplex.export.export_obo
import famplex.export.export_relations_graph

__all__ = [
    'main',
]


def main() -> None:
    """Export FamPlex to all file types."""
    famplex.export.export_belns.main()
    famplex.export.export_obo.main()
    famplex.export.export_relations_graph.main()


if __name__ == '__main__':
    main()
