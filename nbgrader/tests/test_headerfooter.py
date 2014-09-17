import os
from nbgrader.preprocessors import IncludeHeaderFooter

from .base import TestBase


class TestIncludeHeaderFooter(TestBase):

    def setup(self):
        super(TestIncludeHeaderFooter, self).setup()
        self.preprocessor = IncludeHeaderFooter()

    def test_concatenate_nothing(self):
        """Are the cells the same if there is no header/footer?"""
        nb, resources = self.preprocessor.preprocess(self.nb, {})
        assert nb == self.nb

    def test_concatenate_header(self):
        """Is the header prepended correctly?"""
        self.preprocessor.header = os.path.join(self.pth, "files/test.ipynb")
        cells = self.nb.worksheets[0].cells
        self.nb.worksheets[0].cells = cells[:-1]
        nb, resources = self.preprocessor.preprocess(self.nb, {})
        assert nb.worksheets[0].cells == (cells + cells[:-1])

    def test_concatenate_footer(self):
        """Is the footer appended correctly?"""
        self.preprocessor.footer = os.path.join(self.pth, "files/test.ipynb")
        cells = self.nb.worksheets[0].cells
        self.nb.worksheets[0].cells = cells[:-1]
        nb, resources = self.preprocessor.preprocess(self.nb, {})
        assert nb.worksheets[0].cells == (cells[:-1] + cells)

    def test_concatenate_header_and_footer(self):
        """Is the header and footer concatenated correctly?"""
        self.preprocessor.header = os.path.join(self.pth, "files/test.ipynb")
        self.preprocessor.footer = os.path.join(self.pth, "files/test.ipynb")
        cells = self.nb.worksheets[0].cells
        self.nb.worksheets[0].cells = cells[:-1]
        nb, resources = self.preprocessor.preprocess(self.nb, {})
        assert nb.worksheets[0].cells == (cells + cells[:-1] + cells)
