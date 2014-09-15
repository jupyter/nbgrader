from nbgrader.preprocessors import TableOfContents

from .base import TestBase


class TestTableOfContents(TestBase):

    def setup(self):
        super(TestTableOfContents, self).setup()
        self.preprocessor = TableOfContents()

    def test_get_toc_no_heading_cells(self):
        """Is the ToC empty if there are no heading cells?"""
        self.nb.worksheets[0].cells = []
        nb, resources = self.preprocessor.preprocess(self.nb, {})
        assert resources['toc'] == ""

    def test_get_toc(self):
        """Is the ToC correctly formatted?"""
        correct_toc = """* <a href="#foo-bar">foo bar</a>
\t* <a href="#bar">bar</a>
\t\t* <a href="#baz">baz</a>
\t\t* <a href="#quux">quux</a>
\t* <a href="#foo2">foo2</a>"""
        nb, resources = self.preprocessor.preprocess(self.nb, {})
        assert resources['toc'] == correct_toc
