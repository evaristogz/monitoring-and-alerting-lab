"""
Module for launch application
"""

import asyncio
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from prometheus_client import start_http_server
from application.app import SimpleServer


class Container:
    """
    Class Container configure necessary methods for launch application
    """

    def __init__(self):
        self._simple_server = SimpleServer()

    async def start_server(self):
        """Function for start server"""
        await self._simple_server.run_server()


if __name__ == "__main__":
    start_http_server(8000)
    container = Container()
    asyncio.run(container.start_server())
