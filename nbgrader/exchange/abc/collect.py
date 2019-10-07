from traitlets import Bool

from .exchange import Exchange


class ExchangeCollect(Exchange):

    update = Bool(
        False,
        help="Update existing submissions with ones that have newer timestamps."
    ).tag(config=True)

    check_owner = Bool(
        default_value=True,
        help="Whether to cross-check the student_id with the UNIX-owner of the submitted directory."
    ).tag(config=True)


    def init_src(self):
        pass

    def init_dest(self):
        pass

    def copy_files(self):
        pass
