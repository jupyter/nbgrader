import json
from IPython.nbconvert.preprocessors import Preprocessor
from IPython.utils.traitlets import Unicode
from nbgrader import utils


class ExtractTests(Preprocessor):

    rubric_file = Unicode("rubric", config=True, help="Filename to write JSON rubric to")
    tests_file = Unicode("tests", config=True, help="Filename to write JSON test to")

    def _match_tests(self, nb):
        """Determine which tests correspond to which problems."""

        tests = {}
        rubric = {}

        last_problem = None
        last_problem_id = None

        for cell in nb.worksheets[0].cells:
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

    def _extract_outputs(self, resources):
        """Write out the rubric and tests if it's the solution version -- this
        should be in the correct format for FilesWriter (i.e., we need
        to dump to json strings since it writes files in binary
        format).

        """
        if 'outputs' not in resources:
            resources['outputs'] = {}

        rubric = resources['rubric']
        filename = self.rubric_file + ".json"
        resources['outputs'][filename] = json.dumps(rubric, indent=1)

        tests = resources['tests']
        filename = self.tests_file + ".json"
        resources['outputs'][filename] = json.dumps(tests, indent=1)

    def preprocess(self, nb, resources):
        # figure out which tests go with which problems
        resources['tests'], resources['rubric'] = self._match_tests(nb)

        nb, resources = super(ExtractTests, self).preprocess(nb, resources)

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
            else:
                resources['tests'][cell_id]['source'] = cell.source

        return cell, resources
