# -*- coding: utf-8 -*-

"""Constants for the FamPlex Python package."""

import os

HERE = os.path.abspath(os.path.dirname(__file__))

RESOURCES = os.path.join(HERE, 'resources')
ENTITIES_TSV_PATH = os.path.join(RESOURCES, 'entities.tsv')
EQUIVALENCES_TSV_PATH = os.path.join(RESOURCES, 'equivalences.tsv')
GROUNDING_MAP_TSV_PATH = os.path.join(RESOURCES, 'grounding_map.tsv')
RELATIONS_TSV_PATH = os.path.join(RESOURCES, 'relations.tsv')
METADATA_PATH = os.path.join(RESOURCES, 'metadata.json')

EXPORT_DIR = os.path.abspath(os.path.join(HERE, os.pardir, 'export'))
