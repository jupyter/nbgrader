import traceback
import itertools
from nbgrader.preprocessors import LockCells

from .base import TestBase


class TestLockCells(TestBase):

    def setup(self):
        super(TestLockCells, self).setup()
        self.preprocessor = LockCells()

    @staticmethod
    def deletable(cell):
        return cell.metadata.get('deletable', True)

    def test_solution_cell_undeletable(self):
        """Do solution cells become undeletable?"""
        self.preprocessor.lock_solution_cells = True
        self.preprocessor.lock_grade_cells = False
        self.preprocessor.lock_all_cells = False
        cell = self._create_code_cell()
        cell.metadata['nbgrader'] = {}
        cell.metadata['nbgrader']['solution'] = True
        assert self.deletable(cell)
        new_cell = self.preprocessor.preprocess_cell(cell, {}, 0)[0]
        assert not self.deletable(new_cell)

    def test_solution_cell_unchanged(self):
        """Do solution cells remain unchanged?"""
        self.preprocessor.lock_solution_cells = False
        self.preprocessor.lock_grade_cells = False
        self.preprocessor.lock_all_cells = False
        cell = self._create_code_cell()
        cell.metadata['nbgrader'] = {}
        cell.metadata['nbgrader']['solution'] = True
        assert self.deletable(cell)
        new_cell = self.preprocessor.preprocess_cell(cell, {}, 0)[0]
        assert self.deletable(new_cell)

    def test_grade_cell_undeletable(self):
        """Do grade cells become undeletable?"""
        self.preprocessor.lock_solution_cells = False
        self.preprocessor.lock_grade_cells = True
        self.preprocessor.lock_all_cells = False
        cell = self._create_code_cell()
        cell.metadata['nbgrader'] = {}
        cell.metadata['nbgrader']['grade'] = True
        assert self.deletable(cell)
        new_cell = self.preprocessor.preprocess_cell(cell, {}, 0)[0]
        assert not self.deletable(new_cell)

    def test_grade_cell_unchanged(self):
        """Do grade cells remain unchanged?"""
        self.preprocessor.lock_solution_cells = False
        self.preprocessor.lock_grade_cells = False
        self.preprocessor.lock_all_cells = False
        cell = self._create_code_cell()
        cell.metadata['nbgrader'] = {}
        cell.metadata['nbgrader']['grade'] = True
        assert self.deletable(cell)
        new_cell = self.preprocessor.preprocess_cell(cell, {}, 0)[0]
        assert self.deletable(new_cell)

    def test_cell_undeletable(self):
        """Do normal cells become undeletable?"""
        self.preprocessor.lock_solution_cells = False
        self.preprocessor.lock_grade_cells = False
        self.preprocessor.lock_all_cells = True
        cell = self._create_code_cell()
        cell.metadata['nbgrader'] = {}
        assert self.deletable(cell)
        new_cell = self.preprocessor.preprocess_cell(cell, {}, 0)[0]
        assert not self.deletable(new_cell)

    def test_cell_unchanged(self):
        """Do normal cells remain unchanged?"""
        self.preprocessor.lock_solution_cells = False
        self.preprocessor.lock_grade_cells = False
        self.preprocessor.lock_all_cells = False
        cell = self._create_code_cell()
        cell.metadata['nbgrader'] = {}
        assert self.deletable(cell)
        new_cell = self.preprocessor.preprocess_cell(cell, {}, 0)[0]
        assert self.deletable(new_cell)

    def _test_preprocess_nb(self, lock_solution_cells, lock_grade_cells, lock_all_cells):
        """Is the test notebook processed without error?"""
        self.preprocessor.lock_solution_cells = lock_solution_cells
        self.preprocessor.lock_grade_cells = lock_grade_cells
        self.preprocessor.lock_all_cells = lock_all_cells
        self.preprocessor.preprocess(self.nbs["test.ipynb"], {})

    def test_preprocess_nb(self):
        args = itertools.product([True, False], [True, False], [True, False])
        for lsc, lgc, lac in args:
            yield self._test_preprocess_nb, lsc, lgc, lac
