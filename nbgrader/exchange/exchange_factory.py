from traitlets import Type
from traitlets.config import LoggingConfigurable

from nbgrader.exchange import default, abc


class ExchangeFactory(LoggingConfigurable):

    exchange = Type(
        default.Exchange,
        klass=abc.Exchange,
        help="A plugin for exchange."
    ).tag(config=True)

    fetch_assignment = Type(
        default.ExchangeFetchAssignment,
        klass=abc.ExchangeFetchAssignment,
        help="A plugin for fetching assignments."
    ).tag(config=True)

    fetch_feedback = Type(
        default.ExchangeFetchFeedback,
        klass=abc.ExchangeFetchFeedback,
        help="A plugin for fetching feedback."
    ).tag(config=True)

    release_assignment = Type(
        default.ExchangeReleaseAssignment,
        klass=abc.ExchangeReleaseAssignment,
        help="A plugin for releasing assignments."
    ).tag(config=True)

    release_feedback = Type(
        default.ExchangeReleaseFeedback,
        klass=abc.ExchangeReleaseFeedback,
        help="A plugin for releasing feedback."
    ).tag(config=True)

    list = Type(
        default.ExchangeList,
        klass=abc.ExchangeList,
        help="A plugin for listing exchange files."
    ).tag(config=True)

    submit = Type(
        default.ExchangeSubmit,
        klass=abc.ExchangeSubmit,
        help="A plugin for submitting assignments."
    ).tag(config=True)

    collect = Type(
        default.ExchangeCollect,
        klass=abc.ExchangeCollect,
        help="A plugin for collecting assignments."
    ).tag(config=True)

    def __init__(self, **kwargs):
        super(ExchangeFactory, self).__init__(**kwargs)

    def FetchAssignment(self, *args, **kwargs):
        if 'parent' not in kwargs:
            kwargs['parent'] = self
        return self.fetch_assignment(*args, **kwargs)

    def FetchFeedback(self, *args, **kwargs):
        if 'parent' not in kwargs:
            kwargs['parent'] = self
        return self.fetch_feedback(*args, **kwargs)

    def ReleaseAssignment(self, *args, **kwargs):
        if 'parent' not in kwargs:
            kwargs['parent'] = self
        return self.release_assignment(*args, **kwargs)

    def ReleaseFeedback(self, *args, **kwargs):
        if 'parent' not in kwargs:
            kwargs['parent'] = self
        return self.release_feedback(*args, **kwargs)

    def Collect(self, *args, **kwargs):
        if 'parent' not in kwargs:
            kwargs['parent'] = self
        return self.collect(*args, **kwargs)

    def Submit(self, *args, **kwargs):
        if 'parent' not in kwargs:
            kwargs['parent'] = self
        return self.submit(*args, **kwargs)

    def List(self, *args, **kwargs):
        if 'parent' not in kwargs:
            kwargs['parent'] = self
        lst = self.list(*args, **kwargs)
        return lst
