from nbgrader.preprocessors import IncludeHeaderFooter
from nose.tools import assert_equal

from .base import TestBase


class TestIncludeHeaderFooter(TestBase):

    def setup(self):
        super(TestIncludeHeaderFooter, self).setup()
        self.preprocessor = IncludeHeaderFooter()

    def _test_concatenate_nothing(self, name):
        """Are the cells the same if there is no header/footer?"""
        orig_nb = self.nbs[name]
        nb = self.preprocessor.preprocess(orig_nb, {})[0]
        assert_equal(nb, orig_nb, name)

    def test_concatenate_nothing(self):
        for name in self.files:
            yield self._test_concatenate_nothing, name

    def _test_concatenate_header(self, name, header):
        """Is the header prepended correctly?"""
        self.preprocessor.header = self.files[header]
        cells = self.nbs[header].cells[:]
        orig_nb = self.nbs[name]
        orig_cells = orig_nb.cells[:]
        nb = self.preprocessor.preprocess(orig_nb, {})[0]
        assert_equal(nb.cells, (cells + orig_cells), name)

    def test_concatenate_header(self):
        for header in self.files:
            for name in self.files:
                yield self._test_concatenate_header, name, header

    def _test_concatenate_footer(self, name, footer):
        """Is the footer appended correctly?"""
        self.preprocessor.footer = self.files[footer]
        cells = self.nbs[footer].cells[:]
        orig_nb = self.nbs[name]
        orig_cells = orig_nb.cells[:]
        nb = self.preprocessor.preprocess(orig_nb, {})[0]
        assert_equal(nb.cells, (orig_cells + cells), name)

    def test_concatenate_footer(self):
        for footer in self.files:
            for name in self.files:
                yield self._test_concatenate_footer, name, footer

    def _test_concatenate_header_and_footer(self, name, header, footer):
        """Are the header and footer appended correctly?"""
        self.preprocessor.header = self.files[header]
        self.preprocessor.footer = self.files[footer]
        header_cells = self.nbs[header].cells[:]
        footer_cells = self.nbs[footer].cells[:]
        orig_nb = self.nbs[name]
        orig_cells = orig_nb.cells[:]
        nb = self.preprocessor.preprocess(orig_nb, {})[0]
        assert_equal(nb.cells, (header_cells + orig_cells + footer_cells), name)

    def test_concatenate_header_and_footer(self):
        for header in self.files:
            for name in self.files:
                yield self._test_concatenate_header_and_footer, name, header, header
