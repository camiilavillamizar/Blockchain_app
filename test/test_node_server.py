import unittest
from node_server import create_app
from multiprocessing import Process
import requests

# constants
nodelist = ["8000", "8001", "8002"]
loch = "http://localhost:"


class multiNodeTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """ create servers """
        cls.nodes = []
        cls.servers = []
        for node in nodelist:
            cls.nodes.append(create_app())

        # bring them up online
        for idx, node in enumerate(cls.nodes):
            p = Process(target=node.run, kwargs={"port": nodelist[idx]})
            cls.servers.append(p)
            p.start()

    @classmethod
    def tearDownClass(cls):
        """ shut down servers """
        for port in nodelist:
            requests.get(loch + port + "/leave")

    def setUp(self):
        """ initial test config. Should be none """
        pass

    def tearDown(self):
        """ erase all server state """
        for port in nodelist:
            requests.get(loch + port + "/debug_clear")

    # ## ## tests

    def test_add_transaction(self):
        """ adds a single transaction to the 8000 node """
        requests.post(loch + nodelist[0] + "/new_transaction",
                      json={"content": "contenido8000"})

        self.assertEqual(len(requests.get(
            loch + nodelist[0] + "/pending_tx").json()), 1)
        self.assertEqual(len(requests.get(
            loch + nodelist[1] + "/pending_tx").json()), 0)
        self.assertEqual(len(requests.get(
            loch + nodelist[2] + "/pending_tx").json()), 0)

    def test_add_other_transaction(self):
        """ test to see if fixtures are working well """
        requests.post(loch + nodelist[1] + "/new_transaction",
                      json={"content": "contenido8000"})

        self.assertEqual(len(requests.get(
            loch + nodelist[0] + "/pending_tx").json()), 0)
        self.assertEqual(len(requests.get(
            loch + nodelist[1] + "/pending_tx").json()), 1)
        self.assertEqual(len(requests.get(
            loch + nodelist[2] + "/pending_tx").json()), 0)

    def test_add_peers(self):
        """ tests that, on registering, all nodes have the other
        nodes as peers. """
        # adding all nodes on the network
        requests.post(loch + nodelist[1] + "/register_with",
                      json={"node_address": loch + nodelist[0]})
        requests.post(loch + nodelist[2] + "/register_with",
                      json={"node_address": loch + nodelist[0]})

        self.assertCountEqual(
            requests.get(loch + nodelist[0] + "/chain").json()["peers"],
            [loch + nodelist[1] + "/", loch + nodelist[2] + "/"])
        self.assertCountEqual(
            requests.get(loch + nodelist[1] + "/chain").json()["peers"],
            [loch + nodelist[0] + "/", loch + nodelist[2] + "/"])
        self.assertCountEqual(
            requests.get(loch + nodelist[2] + "/chain").json()["peers"],
            [loch + nodelist[0] + "/", loch + nodelist[1] + "/"])


    def test_mine_transaction(self):
        """ tests that, after mining a block, all the nodes on the network
        have it in their chains. """

        requests.post(loch + nodelist[1] + "/register_with",
                      json={"node_address": loch + nodelist[0]})

        requests.post(loch + nodelist[0] + "/new_transaction",
                      json={"content": "contenido8000"})

        requests.get(loch + nodelist[0] + "/mine")

        self.assertEqual(
            requests.get(loch + nodelist[0] + "/chain").json()["chain"],
            requests.get(loch + nodelist[1] + "/chain").json()["chain"])
