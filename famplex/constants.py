# -*- coding: utf-8 -*-

"""Constants for the FamPlex Python package."""

import os

HERE = os.path.abspath(os.path.dirname(__file__))

RESOURCES = os.path.join(HERE, 'resources')
ENTITIES_TSV_PATH = os.path.join(RESOURCES, 'entities.csv')
EQUIVALENCES_TSV_PATH = os.path.join(RESOURCES, 'equivalences.csv')
GROUNDING_MAP_TSV_PATH = os.path.join(RESOURCES, 'grounding_map.csv')
RELATIONS_TSV_PATH = os.path.join(RESOURCES, 'relations.csv')
METADATA_PATH = os.path.join(RESOURCES, 'metadata.json')

EXPORT_DIR = os.path.abspath(os.path.join(HERE, os.pardir, 'export'))
