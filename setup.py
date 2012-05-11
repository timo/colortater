VERSION = '0.5.0'

long_description = """
A tool for recoloring css style sheets with automatic grouping of similar colors.

Comes with a gui version and headless version for automation.
"""

from setuptools import setup, find_packages

setup(
      name = 'colortate',
      version = VERSION,
      author = 'Timo Paulssen',
      description = '',
      long_description = long_description,
      keywords = '',
      url = '',
      packages = find_packages(),
      entry_points="""
          [console_scripts]
          colortate = colortate.main.main
      """,
    )

