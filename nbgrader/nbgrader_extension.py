from __future__ import print_function

import sys
from IPython.core.inputtransformer import InputTransformer
from . import utils


class SolutionInputTransformer(InputTransformer):
    """IPython input transformer that renders jinja templates in cells,
    allowing them to be run while the instructor is developing the
    assignment.

    Original version written by minrk:
    http://nbviewer.ipython.org/gist/minrk/c2b26ee47b7caaaa0c74

    """

    def __init__(self, solution, *args, **kwargs):
        super(SolutionInputTransformer, self).__init__(*args, **kwargs)

        self.solution = solution
        self._lines = []
        self.env = utils.make_jinja_environment()

    def push(self, line):
        self._lines.append(line)
        return None

    def reset(self):
        text = u'\n'.join(self._lines)
        self._lines = []
        template = self.env.from_string(text)
        try:
            return template.render(solution=self.solution)
        except Exception as e:
            print("Failed to render jinja template: %s" % e, file=sys.stderr)
            return text


def _parse_argument(line):
    if line.strip() not in ("solution", "release"):
        raise ValueError("invalid mode: {}".format(line.strip()))
    solution = line.strip() == "solution"
    return solution


def render_template_as(line):
    solution = _parse_argument(line)
    ip = get_ipython()
    transforms = ip.input_transformer_manager.physical_line_transforms
    transforms.insert(0, SolutionInputTransformer(solution))
