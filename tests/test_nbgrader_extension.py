import IPython
from nose.tools import assert_raises
from nbgrader.nbgrader_extension import SolutionInputTransformer, _parse_argument

lines = [
    "# YOUR CODE HERE",
    "{% if solution %}",
    "print(\"hello\")",
    "{% else %}",
    "print(\"goodbye\")",
    "{% endif %}"
]


def test_solutioninputtransformer_push():
        """Does push properly collect the lines?"""
        transformer = SolutionInputTransformer(True)
        for line in lines:
            transformer.push(line)
        assert transformer._lines == lines


def test_solutioninputtransformer_reset_solution():
    """Does reset properly transform the text with solution=True?"""
    transformer = SolutionInputTransformer(True)
    for line in lines:
        transformer.push(line)
    output = transformer.reset()
    assert output == "# YOUR CODE HERE\nprint(\"hello\")\n"
    assert transformer._lines == []


def test_solutioninputtransformer_reset_release():
    """Does reset properly transform the text with solution=False?"""
    transformer = SolutionInputTransformer(False)
    for line in lines:
        transformer.push(line)
    output = transformer.reset()
    assert output == "# YOUR CODE HERE\nprint(\"goodbye\")\n"
    assert transformer._lines == []


def test_parse_argument_invalid():
    """Does the parser throw an error when the argument is invalid?"""
    assert_raises(ValueError, _parse_argument, "foo")


def test_parse_argument_solution():
    """Does the parser correctly parse solution?"""
    assert _parse_argument("solution")


def test__parse_argument_release():
    """Does the parser correctly parse release?"""
    assert not _parse_argument("release")
