import abc

# Simple abstract base class for runnable actions
class Action(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def run(self):
        raise NotImplementedException('Must define run if extending Action')