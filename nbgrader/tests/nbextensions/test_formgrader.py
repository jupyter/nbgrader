import pytest
import os
import shutil

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from .. import run_nbgrader
from ...api import Gradebook, MissingEntry
from . import formgrade_utils as utils


@pytest.fixture(scope="module")
def gradebook(request, tempdir, nbserver):
    # copy files from the user guide
    source_path = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "source", "user_guide", "source")
    submitted_path = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "source", "user_guide", "submitted")

    shutil.copytree(os.path.join(os.path.dirname(__file__), source_path), os.path.join("source"))
    shutil.copytree(os.path.join(os.path.dirname(__file__), submitted_path), os.path.join("submitted"))

    # rename to old names -- we do this rather than changing all the tests
    # because I want the tests to operate on files with spaces in the names
    os.rename(os.path.join("source", "ps1"), os.path.join("source", "Problem Set 1"))
    os.rename(os.path.join("source", "Problem Set 1", "problem1.ipynb"), os.path.join("source", "Problem Set 1", "Problem 1.ipynb"))
    os.rename(os.path.join("source", "Problem Set 1", "problem2.ipynb"), os.path.join("source", "Problem Set 1", "Problem 2.ipynb"))
    os.rename(os.path.join("submitted", "bitdiddle"), os.path.join("submitted", "Bitdiddle"))
    os.rename(os.path.join("submitted", "Bitdiddle", "ps1"), os.path.join("submitted", "Bitdiddle", "Problem Set 1"))
    os.rename(os.path.join("submitted", "Bitdiddle", "Problem Set 1", "problem1.ipynb"), os.path.join("submitted", "Bitdiddle", "Problem Set 1", "Problem 1.ipynb"))
    os.rename(os.path.join("submitted", "Bitdiddle", "Problem Set 1", "problem2.ipynb"), os.path.join("submitted", "Bitdiddle", "Problem Set 1", "Problem 2.ipynb"))
    os.rename(os.path.join("submitted", "hacker"), os.path.join("submitted", "Hacker"))
    os.rename(os.path.join("submitted", "Hacker", "ps1"), os.path.join("submitted", "Hacker", "Problem Set 1"))
    os.rename(os.path.join("submitted", "Hacker", "Problem Set 1", "problem1.ipynb"), os.path.join("submitted", "Hacker", "Problem Set 1", "Problem 1.ipynb"))
    os.rename(os.path.join("submitted", "Hacker", "Problem Set 1", "problem2.ipynb"), os.path.join("submitted", "Hacker", "Problem Set 1", "Problem 2.ipynb"))

    # run nbgrader assign
    run_nbgrader([
        "assign", "Problem Set 1",
        "--IncludeHeaderFooter.header={}".format(os.path.join("source", "header.ipynb"))
    ])

    # run the autograder
    run_nbgrader(["autograde", "Problem Set 1"])

    gb = Gradebook("sqlite:///gradebook.db")

    def fin():
        gb.close()
    request.addfinalizer(fin)

    return gb


@pytest.mark.nbextensions
def test_load_assignment_list(browser, port, gradebook):
    # load the main page and make sure it is the Assignments page
    utils._get(browser, utils._formgrade_url(port))
    utils._wait_for_gradebook_page(browser, port, "")
    utils._check_breadcrumbs(browser, "Assignments")

    # load the assignments page
    utils._load_gradebook_page(browser, port, "assignments")
    utils._check_breadcrumbs(browser, "Assignments")

    # click on the "Problem Set 1" link
    utils._click_link(browser, "Problem Set 1")
    utils._wait_for_gradebook_page(browser, port, "assignments/Problem Set 1")


@pytest.mark.nbextensions
def test_load_assignment_notebook_list(browser, port, gradebook):
    utils._load_gradebook_page(browser, port, "assignments/Problem Set 1")
    utils._check_breadcrumbs(browser, "Assignments", "Problem Set 1")

    # click the "Assignments" link
    utils._click_link(browser, "Assignments")
    utils._wait_for_gradebook_page(browser, port, "assignments")
    browser.back()

    # click on the problem link
    for problem in gradebook.find_assignment("Problem Set 1").notebooks:
        utils._click_link(browser, problem.name)
        utils._wait_for_gradebook_page(browser, port, "assignments/Problem Set 1/{}".format(problem.name))
        browser.back()


@pytest.mark.nbextensions
def test_load_assignment_notebook_submissions_list(browser, port, gradebook):
    for problem in gradebook.find_assignment("Problem Set 1").notebooks:
        utils._load_gradebook_page(browser, port, "assignments/Problem Set 1/{}".format(problem.name))
        utils._check_breadcrumbs(browser, "Assignments", "Problem Set 1", problem.name)

        # click the "Assignments" link
        utils._click_link(browser, "Assignments")
        utils._wait_for_gradebook_page(browser, port, "assignments")
        browser.back()

        # click the "Problem Set 1" link
        utils._click_link(browser, "Problem Set 1")
        utils._wait_for_gradebook_page(browser, port, "assignments/Problem Set 1")
        browser.back()

        submissions = problem.submissions
        submissions.sort(key=lambda x: x.id)
        for i, submission in enumerate(submissions):
            # click on the "Submission #i" link
            utils._click_link(browser, "Submission #{}".format(i + 1))
            utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submission.id))
            browser.back()


@pytest.mark.nbextensions
def test_assignment_notebook_submissions_show_hide_names(browser, port, gradebook):
    problem = gradebook.find_assignment("Problem Set 1").notebooks[0]
    utils._load_gradebook_page(browser, port, "assignments/Problem Set 1/{}".format(problem.name))
    submissions = problem.submissions
    submissions.sort(key=lambda x: x.id)
    submission = submissions[0]

    top_elem = browser.find_element_by_css_selector("#submission-1")
    col1, col2 = top_elem.find_elements_by_css_selector("td")[:2]
    hidden = col1.find_element_by_css_selector(".glyphicon.name-hidden")
    shown = col1.find_element_by_css_selector(".glyphicon.name-shown")

    # check that the name is hidden
    assert col2.text == "Submission #1"
    assert not shown.is_displayed()
    assert hidden.is_displayed()

    # click the show icon
    hidden.click()

    # check that the name is shown
    assert col2.text == "{}, {}".format(submission.student.last_name, submission.student.first_name)
    assert shown.is_displayed()
    assert not hidden.is_displayed()

    # click the hide icon
    shown.click()

    # check that the name is hidden
    assert col2.text == "Submission #1"
    assert not shown.is_displayed()
    assert hidden.is_displayed()


@pytest.mark.nbextensions
def test_load_student_list(browser, port, gradebook):
    # load the student view
    utils._load_gradebook_page(browser, port, "students")
    utils._check_breadcrumbs(browser, "Students")

    # click on student
    for student in gradebook.students:
        ## TODO: they should have a link here, even if they haven't submitted anything!
        if len(student.submissions) == 0:
            continue
        utils._click_link(browser, "{}, {}".format(student.last_name, student.first_name))
        utils._wait_for_gradebook_page(browser, port, "students/{}".format(student.id))
        browser.back()


@pytest.mark.nbextensions
def test_load_student_assignment_list(browser, port, gradebook):
    for student in gradebook.students:
        utils._load_gradebook_page(browser, port, "students/{}".format(student.id))
        utils._check_breadcrumbs(browser, "Students", student.id)

        try:
            gradebook.find_submission("Problem Set 1", student.id)
        except MissingEntry:
            ## TODO: make sure link doesn't exist
            continue

        utils._click_link(browser, "Problem Set 1")
        utils._wait_for_gradebook_page(browser, port, "students/{}/Problem Set 1".format(student.id))


@pytest.mark.nbextensions
def test_load_student_assignment_submissions_list(browser, port, gradebook):
    for student in gradebook.students:
        try:
            submission = gradebook.find_submission("Problem Set 1", student.id)
        except MissingEntry:
            ## TODO: make sure link doesn't exist
            continue

        utils._load_gradebook_page(browser, port, "students/{}/Problem Set 1".format(student.id))
        utils._check_breadcrumbs(browser, "Students", student.id, "Problem Set 1")

        for problem in gradebook.find_assignment("Problem Set 1").notebooks:
            submission = gradebook.find_submission_notebook(problem.name, "Problem Set 1", student.id)
            utils._click_link(browser, problem.name)
            utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submission.id))
            browser.back()
            utils._wait_for_gradebook_page(browser, port, "students/{}/Problem Set 1".format(student.id))


@pytest.mark.nbextensions
def test_switch_views(browser, port, gradebook):
    # load the main page
    utils._load_gradebook_page(browser, port, "assignments")

    # click the "Change View" button
    utils._click_link(browser, "Change View", partial=True)

    # click the "Students" option
    utils._click_link(browser, "Students")
    utils._wait_for_gradebook_page(browser, port, "students")

    # click the "Change View" button
    utils._click_link(browser, "Change View", partial=True)

    # click the "Assignments" option
    utils._click_link(browser, "Assignments")
    utils._wait_for_gradebook_page(browser, port, "assignments")


@pytest.mark.nbextensions
def test_formgrade_view_breadcrumbs(browser, port, gradebook):
    for problem in gradebook.find_assignment("Problem Set 1").notebooks:
        submissions = problem.submissions
        submissions.sort(key=lambda x: x.id)

        for submission in submissions:
            utils._get(browser, utils._formgrade_url(port, "submissions/{}".format(submission.id)))
            utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submission.id))

            # click on the "Assignments" link
            utils._click_link(browser, "Assignments")
            utils._wait_for_gradebook_page(browser, port, "assignments")

            # go back
            browser.back()
            utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submission.id))

            # click on the "Problem Set 1" link
            utils._click_link(browser, "Problem Set 1")
            utils._wait_for_gradebook_page(browser, port, "assignments/Problem Set 1")

            # go back
            browser.back()
            utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submission.id))

            # click on the problem link
            utils._click_link(browser, problem.name)
            utils._wait_for_gradebook_page(browser, port, "assignments/Problem Set 1/{}".format(problem.name))

            # go back
            browser.back()
            utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submission.id))


@pytest.mark.nbextensions
def test_load_live_notebook(browser, port, gradebook):
    for problem in gradebook.find_assignment("Problem Set 1").notebooks:
        submissions = problem.submissions
        submissions.sort(key=lambda x: x.id)

        for i, submission in enumerate(submissions):
            utils._get(browser, utils._formgrade_url(port, "submissions/{}".format(submission.id)))
            utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submission.id))

            # check the live notebook link
            utils._click_link(browser, "Submission #{}".format(i + 1))
            browser.switch_to_window(browser.window_handles[1])
            utils._wait_for_notebook_page(
                browser, port,
                utils._notebook_url(
                    port, "autograded/{}/Problem Set 1/{}.ipynb".format(submission.student.id, problem.name)))
            browser.close()
            browser.switch_to_window(browser.window_handles[0])


@pytest.mark.nbextensions
def test_formgrade_images(browser, port, gradebook):
    submissions = gradebook.find_notebook("Problem 1", "Problem Set 1").submissions
    submissions.sort(key=lambda x: x.id)

    for submission in submissions:
        utils._get(browser, utils._formgrade_url(port, "submissions/{}".format(submission.id)))
        utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submission.id))

        images = browser.find_elements_by_tag_name("img")
        for image in images:
            # check that the image is loaded, and that it has a width
            assert browser.execute_script("return arguments[0].complete", image)
            assert browser.execute_script("return arguments[0].naturalWidth", image) > 0


@pytest.mark.nbextensions
def test_next_prev_assignments(browser, port, gradebook):
    problem = gradebook.find_notebook("Problem 1", "Problem Set 1")
    submissions = problem.submissions
    submissions.sort(key=lambda x: x.id)

    # test navigating both with the arrow keys and with clicking the
    # next/previous links
    next_functions = [
        (utils._send_keys_to_body, browser, Keys.CONTROL, "."),
        (utils._click_element, browser, ".next a")
    ]
    prev_functions = [
        (utils._send_keys_to_body, browser, Keys.CONTROL, ","),
        (utils._click_element, browser, ".previous a")
    ]

    for n, p in zip(next_functions, prev_functions):
        # first element is the function, the other elements are the arguments
        # to that function
        next_function = lambda: n[0](*n[1:])
        prev_function = lambda: p[0](*p[1:])

        # Load the first submission
        utils._get(browser, utils._formgrade_url(port, "submissions/{}".format(submissions[0].id)))
        utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submissions[0].id))

        # Move to the next submission
        next_function()
        utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submissions[1].id))

        # Move to the next submission (should return to notebook list)
        next_function()
        utils._wait_for_gradebook_page(browser, port, "assignments/Problem Set 1/Problem 1")

        # Go back
        browser.back()
        utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submissions[1].id))

        # Move to the previous submission
        prev_function()
        utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submissions[0].id))

        # Move to the previous submission (should return to the notebook list)
        prev_function()
        utils._wait_for_gradebook_page(browser, port, "assignments/Problem Set 1/Problem 1")


@pytest.mark.nbextensions
def test_next_prev_failed_assignments(browser, port, gradebook):
    problem = gradebook.find_notebook("Problem 1", "Problem Set 1")
    submissions = problem.submissions
    submissions.sort(key=lambda x: x.id)

    # verify that we have the right number of submissions, and that one
    # failed tests and the other didn't
    assert len(submissions) == 2
    if submissions[0].failed_tests:
        assert not submissions[1].failed_tests
    else:
        assert submissions[1].failed_tests

    # Load the first submission
    utils._get(browser, utils._formgrade_url(port, "submissions/{}".format(submissions[0].id)))
    utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submissions[0].id))

    if submissions[0].failed_tests:
        # Go to the next failed submission (should return to the notebook list)
        utils._send_keys_to_body(browser, Keys.CONTROL, Keys.SHIFT, ".")
        utils._wait_for_gradebook_page(browser, port, "assignments/Problem Set 1/Problem 1")

        # Go back
        browser.back()
        utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submissions[0].id))

        # Go to the previous failed submission (should return to the notebook list)
        utils._send_keys_to_body(browser, Keys.CONTROL, Keys.SHIFT, ",")
        utils._wait_for_gradebook_page(browser, port, "assignments/Problem Set 1/Problem 1")

        # Go back
        browser.back()
        utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submissions[0].id))

        # Go to the other notebook
        utils._send_keys_to_body(browser, Keys.CONTROL, ".")
        utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submissions[1].id))

        # Go to the next failed submission (should return to the notebook list)
        utils._send_keys_to_body(browser, Keys.CONTROL, Keys.SHIFT, ".")
        utils._wait_for_gradebook_page(browser, port, "assignments/Problem Set 1/Problem 1")

        # Go back
        browser.back()
        utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submissions[1].id))

        # Go to the previous failed submission
        utils._send_keys_to_body(browser, Keys.CONTROL, Keys.SHIFT, ",")
        utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submissions[0].id))

    else:
        # Go to the next failed submission
        utils._send_keys_to_body(browser, Keys.CONTROL, Keys.SHIFT, ".")
        utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submissions[1].id))

        # Go back
        browser.back()
        utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submissions[0].id))

        # Go to the previous failed submission (should return to the notebook list)
        utils._send_keys_to_body(browser, Keys.CONTROL, Keys.SHIFT, ",")
        utils._wait_for_gradebook_page(browser, port, "assignments/Problem Set 1/Problem 1")

        # Go back
        browser.back()
        utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submissions[0].id))

        # Go to the other notebook
        utils._send_keys_to_body(browser, Keys.CONTROL, ".")
        utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submissions[1].id))

        # Go to the next failed submission (should return to the notebook list)
        utils._send_keys_to_body(browser, Keys.CONTROL, Keys.SHIFT, ".")
        utils._wait_for_gradebook_page(browser, port, "assignments/Problem Set 1/Problem 1")

        # Go back
        browser.back()
        utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submissions[1].id))

        # Go to the previous failed submission (should return to the notebook list)
        utils._send_keys_to_body(browser, Keys.CONTROL, Keys.SHIFT, ",")
        utils._wait_for_gradebook_page(browser, port, "assignments/Problem Set 1/Problem 1")


@pytest.mark.nbextensions
def test_tabbing(browser, port, gradebook):
    utils._load_formgrade(browser, port, gradebook)

    # check that the next arrow is selected
    assert utils._get_active_element(browser) == utils._get_next_arrow(browser)
    assert utils._get_index(browser) == 0

    # check that the first comment box is selected
    utils._send_keys_to_body(browser, Keys.TAB)
    assert utils._get_active_element(browser) == utils._get_comment_box(browser, 0)
    assert utils._get_index(browser) == 1

    # tab to the next and check that the first points is selected
    utils._send_keys_to_body(browser, Keys.TAB)
    assert utils._get_active_element(browser) == utils._get_score_box(browser, 0)
    assert utils._get_index(browser) == 2

    # tab to the next and check that the second points is selected
    utils._send_keys_to_body(browser, Keys.TAB)
    assert utils._get_active_element(browser) == utils._get_score_box(browser, 1)
    assert utils._get_index(browser) == 3

    # tab to the next and check that the second comment is selected
    utils._send_keys_to_body(browser, Keys.TAB)
    assert utils._get_active_element(browser) == utils._get_comment_box(browser, 1)
    assert utils._get_index(browser) == 4

    # tab to the next and check that the third points is selected
    utils._send_keys_to_body(browser, Keys.TAB)
    assert utils._get_active_element(browser) == utils._get_score_box(browser, 2)
    assert utils._get_index(browser) == 5

    # tab to the next and check that the fourth points is selected
    utils._send_keys_to_body(browser, Keys.TAB)
    assert utils._get_active_element(browser) == utils._get_score_box(browser, 3)
    assert utils._get_index(browser) == 6

    # tab to the next and check that the fifth points is selected
    utils._send_keys_to_body(browser, Keys.TAB)
    assert utils._get_active_element(browser) == utils._get_score_box(browser, 4)
    assert utils._get_index(browser) == 7

    # tab to the next and check that the third comment is selected
    utils._send_keys_to_body(browser, Keys.TAB)
    assert utils._get_active_element(browser) == utils._get_comment_box(browser, 2)
    assert utils._get_index(browser) == 8

    # tab to the next and check that the sixth points is selected
    utils._send_keys_to_body(browser, Keys.TAB)
    assert utils._get_active_element(browser) == utils._get_score_box(browser, 5)
    assert utils._get_index(browser) == 9

    # tab to the next and check that the fourth comment is selected
    utils._send_keys_to_body(browser, Keys.TAB)
    assert utils._get_active_element(browser) == utils._get_comment_box(browser, 3)
    assert utils._get_index(browser) == 10

    # tab to the next and check that the next arrow is selected
    utils._send_keys_to_body(browser, Keys.TAB)
    assert utils._get_active_element(browser) == utils._get_next_arrow(browser)
    assert utils._get_index(browser) == 0



@pytest.mark.nbextensions
@pytest.mark.parametrize("index", range(4))
def test_save_comment(browser, port, gradebook, index):
    utils._load_formgrade(browser, port, gradebook)
    elem = utils._get_comment_box(browser, index)

    if elem.get_attribute("value") != "":
        elem.click()
        elem.clear()
        utils._save_comment(browser, index)
        utils._load_formgrade(browser, port, gradebook)
        elem = utils._get_comment_box(browser, index)
        assert elem.get_attribute("value") == ""

    elem.click()
    elem.send_keys("this comment has index {}".format(index))
    elem.send_keys(Keys.ENTER)
    elem.send_keys("blah blah blah")
    utils._save_comment(browser, index)

    utils._load_formgrade(browser, port, gradebook)
    elem = utils._get_comment_box(browser, index)
    assert elem.get_attribute("value") == "this comment has index {}\nblah blah blah".format(index)



@pytest.mark.nbextensions
@pytest.mark.parametrize("index", range(6))
def test_save_score(browser, port, gradebook, index):
    utils._load_formgrade(browser, port, gradebook)
    elem = utils._get_score_box(browser, index)

    if elem.get_attribute("value") != "":
        elem.click()
        elem.clear()
        utils._save_score(browser, index)
        utils._load_formgrade(browser, port, gradebook)
        elem = utils._get_score_box(browser, index)
        assert elem.get_attribute("value") == ""

    # check whether it needs manual grading
    if elem.get_attribute("placeholder") != "":
        assert not utils._get_needs_manual_grade(browser, elem.get_attribute("id"))
        assert "needs_manual_grade" not in elem.get_attribute("class").split(" ")
    else:
        assert utils._get_needs_manual_grade(browser, elem.get_attribute("id"))
        assert "needs_manual_grade" in elem.get_attribute("class").split(" ")

    # set the grade
    elem.click()
    elem.send_keys("{}".format((index + 1) / 10.0))
    utils._save_score(browser, index)
    utils._load_formgrade(browser, port, gradebook)
    elem = utils._get_score_box(browser, index)
    assert elem.get_attribute("value") == "{}".format((index + 1) / 10.0)

    # check whether it needs manual grading
    assert not utils._get_needs_manual_grade(browser, elem.get_attribute("id"))
    assert "needs_manual_grade" not in elem.get_attribute("class").split(" ")

    # clear the grade
    elem.click()
    elem.clear()
    utils._save_score(browser, index)
    utils._load_formgrade(browser, port, gradebook)
    elem = utils._get_score_box(browser, index)
    assert elem.get_attribute("value") == ""

    # check whether it needs manual grading
    if elem.get_attribute("placeholder") != "":
        assert not utils._get_needs_manual_grade(browser, elem.get_attribute("id"))
        assert "needs_manual_grade" not in elem.get_attribute("class").split(" ")
    else:
        assert utils._get_needs_manual_grade(browser, elem.get_attribute("id"))
        assert "needs_manual_grade" in elem.get_attribute("class").split(" ")


@pytest.mark.nbextensions
def test_same_part_navigation(browser, port, gradebook):
    problem = gradebook.find_notebook("Problem 1", "Problem Set 1")
    submissions = problem.submissions
    submissions.sort(key=lambda x: x.id)

    # Load the first submission
    utils._get(browser, utils._formgrade_url(port, "submissions/{}".format(submissions[0].id)))
    utils._wait_for_formgrader(browser, port, "submissions/{}/?index=0".format(submissions[0].id))

    # Click the second comment box and navigate to the next submission
    utils._get_comment_box(browser, 1).click()
    utils._send_keys_to_body(browser, Keys.CONTROL, ".")
    utils._wait_for_formgrader(browser, port, "submissions/{}/?index=4".format(submissions[1].id))
    assert utils._get_active_element(browser) == utils._get_comment_box(browser, 1)

    # Click the third score box and navigate to the previous submission
    utils._get_score_box(browser, 2).click()
    utils._send_keys_to_body(browser, Keys.CONTROL, ",")
    utils._wait_for_formgrader(browser, port, "submissions/{}/?index=5".format(submissions[0].id))
    assert utils._get_active_element(browser) == utils._get_score_box(browser, 2)

    # Click the third comment box and navigate to the next submission
    utils._get_comment_box(browser, 2).click()
    utils._send_keys_to_body(browser, Keys.CONTROL, ".")
    utils._wait_for_formgrader(browser, port, "submissions/{}/?index=7".format(submissions[1].id))
    assert utils._get_active_element(browser) == utils._get_score_box(browser, 4)

    # Navigate to the previous submission
    utils._send_keys_to_body(browser, Keys.CONTROL, ",")
    utils._wait_for_formgrader(browser, port, "submissions/{}/?index=7".format(submissions[0].id))
    assert utils._get_active_element(browser) == utils._get_score_box(browser, 4)


@pytest.mark.nbextensions
def test_keyboard_help(browser, port, gradebook):
    utils._load_formgrade(browser, port, gradebook)

    # show the help dialog
    utils._click_element(browser, ".help")
    utils._wait_for_element(browser, "help-dialog")
    WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#help-dialog button.btn-primary")))

    # close it
    utils._click_element(browser, "#help-dialog button.btn-primary")
    modal_not_present = lambda browser: browser.execute_script("""return $("#help-dialog").length === 0;""")
    WebDriverWait(browser, 10).until(modal_not_present)


@pytest.mark.nbextensions
def test_flag(browser, port, gradebook):
    utils._load_formgrade(browser, port, gradebook)

    # mark as flagged
    assert utils._flag(browser) == "Submission flagged"

    # mark as unflagged
    assert utils._flag(browser) == "Submission unflagged"

    # mark as flagged
    assert utils._flag(browser) == "Submission flagged"

    # mark as unflagged
    assert utils._flag(browser) == "Submission unflagged"


@pytest.mark.nbextensions
def test_formgrade_show_hide_names(browser, port, gradebook):
    utils._load_formgrade(browser, port, gradebook)

    problem = gradebook.find_notebook("Problem 1", "Problem Set 1")
    submissions = problem.submissions
    submissions.sort(key=lambda x: x.id)
    submission = submissions[0]

    name = browser.find_elements_by_css_selector(".breadcrumb li")[-1]
    hidden = browser.find_element_by_css_selector(".glyphicon.name-hidden")
    shown = browser.find_element_by_css_selector(".glyphicon.name-shown")

    # check that the name is hidden
    assert name.text == "Submission #1"
    assert not shown.is_displayed()
    assert hidden.is_displayed()

    # click the show icon
    hidden.click()
    WebDriverWait(browser, 10).until_not(EC.presence_of_element_located((By.CSS_SELECTOR, ".tooltip")))

    # check that the name is shown
    assert name.text == "{}, {}".format(submission.student.last_name, submission.student.first_name)
    assert shown.is_displayed()
    assert not hidden.is_displayed()

    # click the hide icon
    shown.click()
    WebDriverWait(browser, 10).until_not(EC.presence_of_element_located((By.CSS_SELECTOR, ".tooltip")))

    # check that the name is hidden
    assert name.text == "Submission #1"
    assert not shown.is_displayed()
    assert hidden.is_displayed()
