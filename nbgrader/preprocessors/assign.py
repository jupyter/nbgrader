import json
from IPython.nbconvert.preprocessors import ExecutePreprocessor
from IPython.utils.traitlets import Bool, Unicode
from IPython.nbformat.current import read as read_nb
from .. import utils


class Assign(ExecutePreprocessor):

    solution = Bool(False, config=True, help="Whether to generate the release version, or the solutions")

    title = Unicode("", config=True, help="Title of the assignment")

    disable_toolbar = Bool(True, config=True, help="Whether to hide the nbgrader toolbar after conversion")
    hide_test_cells = Bool(True, config=True, help="Whether to hide test cells after conversion")

    rubric_file = Unicode("rubric", config=True, help="Filename to write JSON rubric to")
    tests_file = Unicode("tests", config=True, help="Filename to write JSON test to")

    def __init__(self, *args, **kwargs):
        super(Assign, self).__init__(*args, **kwargs)

        # create the jinja templating environment
        self.env = utils.make_jinja_environment()

    def _match_tests(self, cells):
        """Determine which tests correspond to which problems."""

        tests = {}
        rubric = {}

        last_problem = None
        last_problem_id = None

        for cell in cells:
            cell_type = utils.get_assignment_cell_type(cell)

            # if it's a grading cell, then it becomes the most recent
            # problem (to assign the autograding tests to)
            if cell_type == "grade":
                last_problem = cell
                last_problem_id = last_problem.metadata['nbgrader']['id']

                if last_problem_id in rubric:
                    raise RuntimeError(
                        "problem '{}' already exists!".format(
                            last_problem_id))

                # extract the point value
                points = last_problem.metadata['nbgrader']['points']
                if points == '':
                    points = 0
                else:
                    points = float(points)

                # add the problem to the rubric
                rubric[last_problem_id] = {
                    'tests': [],
                    'points': points
                }

            # if it's an test cell, then we need to add it to
            # the list of tests for the last problem cell and record
            # it in the tests dictionary
            elif cell_type == "test":
                if not last_problem:
                    raise RuntimeError(
                        "autograding cell before any gradeable cells!")

                cell_id = cell.metadata['nbgrader']['id']
                if cell_id in tests:
                    raise RuntimeError(
                        "test id '{}' is used more than once".format(cell_id))

                weight = cell.metadata['nbgrader'].get('weight', 1)
                if weight == '':
                    weight = 1
                else:
                    weight = float(weight)

                # add the test to the tests dictionary
                tests[cell_id] = {
                    'weight': weight,
                    'problem': last_problem_id,
                    'cell_type': cell.cell_type
                }

                # add the test to the list of tests for the problem
                rubric[last_problem_id]['tests'].append(cell_id)

        # now normalize the test weights so that the weights of all
        # tests for a particular problem sum to one.
        for problem in rubric:
            # the total number of points this problem is worth
            total_points = float(rubric[problem]['points'])

            # get the list of tests for this problem
            problem_tests = rubric[problem]['tests']

            # compute the normalizing constant for the weights
            normalizer = float(sum(
                [tests[t]['weight'] for t in problem_tests]))

            # update weights and points for each test
            for test in problem_tests:
                tests[test]['weight'] /= normalizer
                tests[test]['points'] = total_points * tests[test]['weight']

        return tests, rubric

    def _preprocess_nb(self, nb, resources):
        cells = nb.worksheets[0].cells

        # figure out which tests go with which problems
        tests, rubric = self._match_tests(cells)
        resources['tests'] = tests
        resources['rubric'] = rubric

        # update the notebook with the new cells
        nb.worksheets[0].cells = cells

        # remove the cell toolbar, if it exists
        if "celltoolbar" in nb.metadata:
            del nb.metadata['celltoolbar']

        # mark in the notebook metadata whether it's a solution or not
        nb.metadata['disable_nbgrader_toolbar'] = self.disable_toolbar
        nb.metadata['hide_test_cells'] = self.hide_test_cells

        return nb, resources

    def _extract_outputs(self, resources):
        """Write out the rubric and tests if it's the solution version -- this
        should be in the correct format for FilesWriter (i.e., we need
        to dump to json strings since it writes files in binary
        format).

        """
        if self.solution:
            if 'outputs' not in resources:
                resources['outputs'] = {}

            rubric = resources['rubric']
            filename = self.rubric_file + ".json"
            resources['outputs'][filename] = json.dumps(rubric, indent=1)

            tests = resources['tests']
            filename = self.tests_file + ".json"
            resources['outputs'][filename] = json.dumps(tests, indent=1)

    def preprocess(self, nb, resources):
        nb, resources = self._preprocess_nb(nb, resources)

        if self.solution:
            nb, resources = super(Assign, self).preprocess(
                nb, resources)
        else:
            nb, resources = super(ExecutePreprocessor, self).preprocess(
                nb, resources)

        # extract rubric and tests
        self._extract_outputs(resources)

        return nb, resources

    def preprocess_cell(self, cell, resources, cell_index):

        # if it's an test cell, then record the source and then
        # clear it (so it's not visible to students)
        nbgrader_cell_type = utils.get_assignment_cell_type(cell)
        if nbgrader_cell_type == "test":
            cell_id = cell.metadata['nbgrader']['id']

            if cell.cell_type == 'code':
                resources['tests'][cell_id]['source'] = cell.input
                if self.hide_test_cells:
                    cell.input = ""
            else:
                resources['tests'][cell_id]['source'] = cell.source
                if self.hide_test_cells:
                    cell.source = ""

        # if it's the solution version, execute the cell
        if cell.cell_type == 'code' and self.solution:
            cell, resources = super(Assign, self)\
                .preprocess_cell(cell, resources, cell_index)

        return cell, resources
