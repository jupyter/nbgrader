from nbgrader.preprocessors import IncludeHeaderFooter
from nose.tools import assert_equal

from .base import TestBase


class TestIncludeHeaderFooter(TestBase):

    def setup(self):
        super(TestIncludeHeaderFooter, self).setup()
        self.preprocessor = IncludeHeaderFooter()

    def test_concatenate_nothing(self):
        """Are the cells the same if there is no header/footer?"""
        orig_nb = self.nbs["test.ipynb"]
        nb = self.preprocessor.preprocess(orig_nb, {})[0]
        assert_equal(nb, orig_nb)

    def test_concatenate_header(self):
        """Is the header prepended correctly?"""
        self.preprocessor.header = self.files["header.ipynb"]
        cells = self.nbs["header.ipynb"].cells[:]
        orig_nb = self.nbs["test.ipynb"]
        orig_cells = orig_nb.cells[:]
        nb = self.preprocessor.preprocess(orig_nb, {})[0]
        assert_equal(nb.cells, (cells + orig_cells))

    def test_concatenate_footer(self):
        """Is the footer appended correctly?"""
        self.preprocessor.footer = self.files["header.ipynb"]
        cells = self.nbs["header.ipynb"].cells[:]
        orig_nb = self.nbs["test.ipynb"]
        orig_cells = orig_nb.cells[:]
        nb = self.preprocessor.preprocess(orig_nb, {})[0]
        assert_equal(nb.cells, (orig_cells + cells))

    def test_concatenate_header_and_footer(self):
        """Are the header and footer appended correctly?"""
        self.preprocessor.header = self.files["header.ipynb"]
        self.preprocessor.footer = self.files["header.ipynb"]
        header_cells = self.nbs["header.ipynb"].cells[:]
        footer_cells = self.nbs["header.ipynb"].cells[:]
        orig_nb = self.nbs["test.ipynb"]
        orig_cells = orig_nb.cells[:]
        nb = self.preprocessor.preprocess(orig_nb, {})[0]
        assert_equal(nb.cells, (header_cells + orig_cells + footer_cells))
