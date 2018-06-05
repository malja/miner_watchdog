import json
import requests
import os
import time

from twisted.internet.protocol import Protocol, ClientFactory


class ServerReport(object):
    """
    Object used as wrapping around HTTP/S connection to monitoring server.
    """

    def __init__(self, status, app):
        """
        :param client.connection.ClaymoreResponse status: Class with response from claymore miner.
        :param client.App app: App instance.
        """

        self.data = status
        self.app = app

        self._status_code = 0
        self._response = None

    def send(self):
        """
        Send all data to server via POST.
        """

        payload = {
            "name": self.app.config.client.name,
            "version": self.app.version,
            "secret": self.app.config.client.secret,
            "interval": self.app.config.client.interval,
            "data": json.dumps({
                "version": self.data.version(),
                "runtime": self.data.runtime(),
                "hashrate": self.data.hashrate(),
                "pool": self.data.pool(),
                "gpus": self.data.gpuData()
            })
        }

        try:
            r = requests.post(self.app.config.server.address, data=payload)
            self._response = r.text
            self._status_code = r.status_code

        except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout) as e:
            self.app.logger.error("Server connection failed {}. Restarting computer".format(e))
            os.system("r")

        except Exception as e:
            self.app.logger.error("Unhandled connection error: {}".format(e))

    def __bool__(self):
        return self._status_code == 200

    def response(self):
        """
        Text printed out by server. Mainly for debugging purpuses (in default, server does not output anything).
        """
        return self._response

    def return_code(self):
        return self._status_code


class ClaymoreRequest(object):
    """
    Class for hiding all code for creating a JSON string with a message sent to Claymore miner. All methods are pure
    static.
    """

    @staticmethod
    def _message(method, params = None):
        """
        This method build a JSON string from method and additional parameters. You should not call this method directly
        but rather use one of "one purpose" one listed below.
        :param str method: One of supported methods. It sets type of message for claymore.
        :param list params: Array of optional parameters required for selected method.
        :return: JSON string.
        """

        message = {
            "id": 0,
            "jsonrpc": "2.0",
            "method": method,
        }

        if params:
            message["params"] = params

        return json.dumps(message, ensure_ascii=True).encode("ascii")

    @staticmethod
    def status():
        """
        Requests a recent miner stats - hashrate, runtime etc.
        :return: JSON string.
        """

        method = "miner_getstat1"
        return ClaymoreRequest._message(method)

    @staticmethod
    def restart():
        """
        Restarts Claymore miner.
        :return: JSON string.
        """

        method = "miner_restart"
        return ClaymoreRequest._message(method)

    @staticmethod
    def reboot():
        """
        Calls reboot.bat (Windows) or reboot.sh (Linux).
        :return: JSON string.
        """

        method = "miner_reboot"
        return ClaymoreRequest._message(method)

    @staticmethod
    def gpu(index, state):
        """
        Controls GPU - disable, ETH-only and dual mining mode.
        :param int index: Index of the card as seen by the miner. Or -1 for all cards.
        :param int state: 0 (disabled), 1 (ETH only), 2 (dual mining)
        :return: JSON string.
        """

        if index < -1:
            raise ValueError("Index have to be bigger than -1.")

        if state not in [0, 1, 2]:
            raise ValueError("State is required to be one of 0,1 or 2")

        method = "control_gpu"
        params = [index, state]
        return ClaymoreRequest._message(method, params)


class ClaymoreResponse(object):
    """
    Class wrapper around JSON response from claymore miner.
    """

    def __init__(self, data):
        """
        :param str data: RAW response as JSON string.
        """

        self._error = None
        self._version = None
        self._runtime = 0
        self._hashrate = 0
        self._gpu = []
        self._pool = None

        self._parse(data)

    def _parse(self, data):
        """
        Do not call this method directly.
        """

        # Claymore returns data as JSON string
        data_dict = json.loads(data.decode("utf-8"))

        # Get error message
        self._error = data_dict["error"]

        # Check error
        if self._error:
            return False

        result = data_dict["result"]

        # Get miner version
        self._version = result[0]

        # Get runtime
        self._runtime = int(result[1])

        # Get hashrate. It is in array with valid and invalid shares.
        # Hashrate is in kH/s
        # hashrate;valid shares;invalid shares
        shares = result[2].split(";")
        self._hashrate = int(shares[0])*1000

        # Hashrates are in kH/s
        gpu_hashrate = result[3].split(";")

        # Result[6] is list of temps and fanspeeds divided by ;
        # temp1;fan1;temp2;fan2 ...
        gpu_temp_fan = result[6].split(";")

        for index, hashrate in enumerate(gpu_hashrate):
            self._gpu.append(
                {
                    "index": index,
                    "hashrate": int(hashrate)*1000,
                    "temperature": int(gpu_temp_fan[index]),
                    "fanspeed": int(gpu_temp_fan[index+1])
                }
            )

        # Get Pool address
        self._pool = result[7]

        return True

    def hasError(self):
        return self._error is not None

    def getError(self):
        return self._error

    def hashrate(self):
        return self._hashrate

    def pool(self):
        return self._pool

    def version(self):
        return self._version

    def runtime(self):
        return self._runtime

    def gpuData(self):
        """
        Get whole dictionary with GPU related data.
        :returns: List of GPU dicts.
        """
        return self._gpu

    def gpu(self, index):
        """
        Returns data about GPU with selected index.
        :param int index: GPU number (as seen by miner).
        :returns: GPU dict.
        """
        return self._gpu[index]

    def __bool__(self):
        return self._error is None


class ClaymoreConnection(Protocol):

    def sendMessage(self, message):
        self.app.logger.debug("Sending message to Claymore miner.")
        self.transport.write(message)


    def dataReceived(self, data):

        self.app.logger.debug("Data received from Claymore miner.")
        status = ClaymoreResponse(data)
        self.app.onMinerResponse(status)

    def connectionMade(self):
        self.app.logger.info("Connected to Claymore miner")
        self.sendMessage(ClaymoreRequest.status())


class ClaymoreConnectionFactory(ClientFactory):
    def __init__(self, app):
        self.app = app

        # Sleep for selected time to give miner time to start properly.
        time.sleep(int(self.app.config.client.interval))

    def buildProtocol(self, addr):
        protocol = ClaymoreConnection()
        protocol.app = self.app
        return protocol

    def clientConnectionLost(self, connector, reason):
        self.app.onConnectionClosed(reason, connector)

    def clientConnectionFailed(self, connector, reason):
        self.app.logger.error("Connection failed: ".format(reason))
        self.app.onConnectionFailed(reason, connector)
