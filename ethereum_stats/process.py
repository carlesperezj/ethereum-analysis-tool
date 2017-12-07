from geth import LoggingMixin
from geth.process import BaseGethProcess, DevGethProcess


class RinkebyGethProcess(BaseGethProcess):
    def __init__(self, geth_kwargs=None):
        if geth_kwargs is None:
            geth_kwargs = {}

        if 'network_id' in geth_kwargs:
            raise ValueError(
                "You cannot specify `network_id` for a {0}".format(type(self).__name__)
            )

        geth_kwargs['network_id'] = '3'
        geth_kwargs['data_dir'] = get_ropsten_data_dir()

        super(RopstenGethProcess, self).__init__(geth_kwargs)

    @property
    def data_dir(self):
        return get_ropsten_data_dir()


class DevGethProcessWithLogging(LoggingMixin, DevGethProcess):
    pass


class RinkebyGethProcessWithLogging(LoggingMixin, RinkebyGethProcess):
    pass


