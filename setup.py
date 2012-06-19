VERSION = '0.6.2'

long_description = """
A tool for recoloring css style sheets with automatic grouping of similar colors.

Comes with a gui version and headless version for automation.
"""

from setuptools import setup, find_packages

setup(
      name = 'colortater',
      version = VERSION,
      author = 'Timo Paulssen',
      description = '',
      long_description = long_description,
      keywords = '',
      url = 'http://wakelift.de/posts/colortater/',
      packages = find_packages(),
      entry_points="""
          [console_scripts]
          colortater = colortater.main.main
      """,
    )

