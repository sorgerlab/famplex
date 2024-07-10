import os
import sys
from setuptools import setup, find_packages
from distutils.sysconfig import get_python_lib

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

relative_site_packages = get_python_lib().\
    split(os.path.realpath(sys.prefix) + os.sep)[1]

package_relative_path = os.path.join(relative_site_packages,
                                     'famplex')
setup(name='famplex',
      version='0.0.5',
      description="Resources for grounding protein complexes and families"
      " from text and describing their hierarchical relationships.",
      long_description=long_description,
      long_description_content_type='text/markdown',
      url='https://github.com/sorgerlab/famplex',
      author='Famplex Developers, Harvard Medical School',
      classifiers=[
          'Development Status :: 4 - Beta',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8'],
      packages=find_packages(),
      extras_require={
          'test': ['pytest'],
          'html': ['requests', 'tqdm', 'pandas', 'click', 'jinja2',
                   'numpy<2'],
      },
      package_data={'': ['entities.csv', 'equivalences.csv',
                         'grounding_map.csv', 'relations.csv',
                         'gene_prefixes.csv', 'descriptions.csv',
                         'famplex.belns',
                         'famplex_groundings.tsv',
                         'famplex.obo',
                         'hgnc_symbol_map.csv']},
      data_files=[(os.path.join(package_relative_path, 'resources'),
                   ['entities.csv', 'equivalences.csv', 'grounding_map.csv',
                    'relations.csv', 'gene_prefixes.csv',
                    'descriptions.csv']),
                  (os.path.join(package_relative_path, 'exports'),
                   ['export/famplex.belns', 'export/famplex_groundings.tsv',
                    'export/famplex.obo', 'export/hgnc_symbol_map.csv'])],
      include_package_data=True)
