"""
A system for assigning and grading notebooks.
"""

from __future__ import absolute_import

from .apps.nbgraderapp import NbGraderApp as _NBAPP

__version__ = _NBAPP.version
