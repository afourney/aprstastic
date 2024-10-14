import time
import threading
import aprslib
from aprslib.parsing import parse
from aprslib.exceptions import ParseError, UnknownFormat
from queue import Queue, Empty

EPSILON = 0.001


class APRSClient(object):
    """
    A thin, thread-safe, client around aprslib.
    Maybe we will implement our own one day!
    """

    def __init__(self, login: str, passcode: str, filters: None):
        super().__init__()
        self._login = login
        self._passcode = passcode
        self._filters = filters
        self._aprs = None
        self._rx_queue = Queue()
        self._tx_queue = Queue()

        self._rx_thread = threading.Thread(target=self._rx_thread_body)
        self._tx_thread = threading.Thread(target=self._tx_thread_body)
        self._rx_thread.start()
        self._tx_thread.start()

    def recv(self, raw=False) -> str | None:
        """
        Returns one packet from the receive queue, or None if the queue is empty."
        """
        try:
            packet = self._rx_queue.get(block=False)
            if raw:
                return packet
            else:
                try:
                    return parse(packet)
                except ParseError:
                    print("ParseError: " + packet.strip())
                except UnknownFormat:
                    print("UnknownFormat: " + packet.strip())
        except Empty:
            return None

    def send(self, packet: str) -> None:
        """
        Enqueue a packet on the send queue, to be sent ASAP.
        """
        self._tx_queue.put(packet)

    def set_filter(self, filters: str | None) -> None:
        """
        Update the filters controling which packets are received from APRS IS
        """
        self._tx_queue.put(_UpdateFilters(filters))

    def _tx_thread_body(self) -> None:
        while True:
            try:
                # Client has not been created yet
                if self._aprs is None:
                    time.sleep(0.1)
                    continue

                # Client is not yet connected
                if not self._aprs._connected:
                    time.sleep(0.1)
                    continue

                # Read a packet
                packet = self._tx_queue.get(block=False)
                if isinstance(packet, _UpdateFilters):
                    self._filters = packet.filters
                    if self._filters is None:
                        self._aprs.set_filter("")  # Default filter?
                    else:
                        self._aprs.set_filter(self._filters)
                else:
                    self._aprs.sendall(packet)
            except Empty:
                time.sleep(EPSILON)

    def _rx_thread_body(self) -> None:
        self._aprs = aprslib.IS(self._login, passwd=self._passcode, port=14580)
        if self._filters is not None:
            self._aprs.set_filter(self._filters)
        self._aprs.connect()
        self._aprs.consumer(
            lambda x: self._rx_queue.put(x, block=True), raw=True, blocking=True
        )


class _UpdateFilters(object):
    """
    Class used to update the filters.
    """

    def __init__(self, filters: str):
        super().__init__()
        self.filters = filters
