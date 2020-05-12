from traitlets import Bool

from .exchange import Exchange


class ExchangeCollect(Exchange):

    update = Bool(
        False,
        help="Update existing submissions with ones that have newer timestamps."
    ).tag(config=True)

    before_duedate = Bool(
        False,
        help="Collect the last submission before due date or the last submission if no submission before due date."
    ).tag(config=True)

    check_owner = Bool(
        default_value=True,
        help="Whether to cross-check the student_id with the UNIX-owner of the submitted directory."
    ).tag(config=True)
