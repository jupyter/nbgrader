from nbgrader.preprocessors import ComputeChecksums
from .base import TestBase


class TestComputeChecksums(TestBase):

    def setup(self):
        super(TestComputeChecksums, self).setup()
        self.preprocessor = ComputeChecksums()

    def test_code_cell_no_checksum(self):
        """Test that no checksum is computed for a regular code cell"""
        cell, resources = self.preprocessor.preprocess_cell(
            self._create_code_cell(), {}, 0)
        assert "nbgrader" not in cell.metadata or "checksum" not in cell.metadata.nbgrader

    def test_text_cell_no_checksum(self):
        """Test that no checksum is computed for a regular text cell"""
        cell, resources = self.preprocessor.preprocess_cell(
            self._create_text_cell(), {}, 0)
        assert "nbgrader" not in cell.metadata or "checksum" not in cell.metadata.nbgrader

    def test_checksum_cell_type(self):
        """Test that the checksum is computed for grade cells of different cell types"""
        cell1 = self._create_grade_cell("", "code", "foo", 1)
        cell1 = self.preprocessor.preprocess_cell(cell1, {}, 0)[0]
        cell2 = self._create_grade_cell("", "markdown", "foo", 1)
        cell2 = self.preprocessor.preprocess_cell(cell2, {}, 0)[0]

        assert cell1.metadata.nbgrader["checksum"]
        assert cell2.metadata.nbgrader["checksum"]
        assert cell1.metadata.nbgrader["checksum"] != cell2.metadata.nbgrader["checksum"]

    def test_checksum_points(self):
        """Test that the checksum is computed for grade cells with different points"""
        cell1 = self._create_grade_cell("", "code", "foo", 1)
        cell1 = self.preprocessor.preprocess_cell(cell1, {}, 0)[0]
        cell2 = self._create_grade_cell("", "code", "foo", 2)
        cell2 = self.preprocessor.preprocess_cell(cell2, {}, 0)[0]

        assert cell1.metadata.nbgrader["checksum"]
        assert cell2.metadata.nbgrader["checksum"]
        assert cell1.metadata.nbgrader["checksum"] != cell2.metadata.nbgrader["checksum"]

    def test_checksum_grade_id(self):
        """Test that the checksum is computed for grade cells with different ids"""
        cell1 = self._create_grade_cell("", "code", "foo", 1)
        cell1 = self.preprocessor.preprocess_cell(cell1, {}, 0)[0]
        cell2 = self._create_grade_cell("", "code", "bar", 1)
        cell2 = self.preprocessor.preprocess_cell(cell2, {}, 0)[0]

        assert cell1.metadata.nbgrader["checksum"]
        assert cell2.metadata.nbgrader["checksum"]
        assert cell1.metadata.nbgrader["checksum"] != cell2.metadata.nbgrader["checksum"]

    def test_checksum_source(self):
        """Test that the checksum is computed for grade cells with different sources"""
        cell1 = self._create_grade_cell("a", "code", "foo", 1)
        cell1 = self.preprocessor.preprocess_cell(cell1, {}, 0)[0]
        cell2 = self._create_grade_cell("b", "code", "foo", 1)
        cell2 = self.preprocessor.preprocess_cell(cell2, {}, 0)[0]

        assert cell1.metadata.nbgrader["checksum"]
        assert cell2.metadata.nbgrader["checksum"]
        assert cell1.metadata.nbgrader["checksum"] != cell2.metadata.nbgrader["checksum"]

    def test_no_checksum_grade_and_solution(self):
        """Test that a checksum is not created for grade cells that are also solution cells"""
        cell = self._create_grade_cell("", "markdown", "foo", 1)
        cell.metadata.nbgrader["solution"] = True
        cell = self.preprocessor.preprocess_cell(cell, {}, 0)[0]
        assert "checksum" not in cell.metadata.nbgrader
