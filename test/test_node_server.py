import os
import re
import signal
import concurrent.futures
import unittest
import requests
import json
import subprocess
import time

from node_server import create_app
unittest.TestLoader.sortTestMethodsUsing = None

# aliases
nodo = "http://localhost:"
nodo1 = "http://localhost:8000"
nodo2 = "http://localhost:8001"
nodo3 = "http://localhost:8002"
nodos = [8000, 8001, 8002]

count = 0

class BasicsTestCase(unittest.TestCase):
    def setUp(self):
        self.node = create_app()
        self.app = self.node.test_client()

    def tearDown(self):
        pass

    # ### pruebas

    def test_no_main_page(self):
        response = self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 404)

    def test_for_sanity(self):
        self.assertEqual(5, 5)

    def test_dos_mensajes_simultaneos(self):
        """ Enviar dos mensajes al mismo tiempo a un nodo. """
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            pool.map(lambda content: self.app.post(
                '/new_transaction',
                json={'content': content}
            ), ["primer mensaje", "segundo mensaje"])
        queue = json.loads(self.app.get('/pending_tx').data)
        self.assertCountEqual(["primer mensaje", "segundo mensaje"],
                              [x["content"] for x in queue])


class multiNodesTestCase(unittest.TestCase):
    """ pruebas con dos o más nodos. Es necesario conectarlos, así que hay que
        dejar los puertos que usen libres. """

    def setUp(self):
        global count
        self.port1 = 8000 + count
        count += 1
        self.port2 = 8000 + count
        count += 1
        self.port3 = 8000 + count
        count += 1
        self.node1 = create_app()
        self.node2 = create_app()
        self.node3 = create_app()

        self.pid1 = os.fork()
        if self.pid1 == 0:
            self.node1.run(port=8000 + str(self.port1))

        self.pid2 = os.fork()
        if self.pid2 == 0:
            self.node2.run(port=8000 + str(self.port2))

        self.pid3 = os.fork()
        if self.pid3 == 0:
            self.node3.run(port=8000 + str(self.port3))

    def tearDown(self):
        """ elimina los servidores """
        for pid in [self.pid1, self.pid2, self.pid3]:
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                pass

    # ### ### pruebas

    def test_dos_nodos_diff(self):
        """ prueba que los nodos generados sean diferentes """
        requests.post(
            nodo + str(self.port1) + '/new_transaction',
            json={'content': 'contenido'}
        )

        rs1 = requests.get(nodo + str(self.port1) + '/pending_tx')
        rs2 = requests.get(nodo + str(self.port2) + '/pending_tx')
        self.assertNotEqual(rs1.content, rs2.content)

    # FIXME los nodos no realizan consenso cuando se minan en paralelo
    def test_consenso_paralelo(self):
        """prueba que los nodos se pongan de acuerdo tras recibir un mensaje y
        minarlo."""
        # primero conectamos los nodos
        requests.post(nodo + str(self.port2) + "/register_with",
                      json={'node_address': nodo + str(self.port1)})

        def commentNmine(args):
            print("agregando la transacción")
            requests.post(
                args["url"] + "/new_transaction",
                json={'content': args["content"]}
            )
            print("minando la transacción")
            requests.get(args["url"] + "/mine")

        # actualización paralela de los nodos.
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            pool.map(commentNmine, [{"url": nodo + str(self.port1),
                                     "content": "contenido1"},
                                    {"url": nodo + str(self.port2),
                                     "content": "contenido2"}])

        # las cadenas deberían ser iguales entre los nodos
        ch1 = json.loads(requests.get(
            nodo + str(self.port1) + '/chain').content)["chain"]
        print(ch1)
        ch2 = json.loads(requests.get(
            nodo + str(self.port2) + '/chain').content)["chain"]
        print(ch2)

        self.assertEqual(ch1, ch2)

    def test_consenso_seq(self):
        """prueba que los nodos se pongan de acuerdo tras recibir un mensaje y
        minarlo."""
        # primero conectamos los nodos
        requests.post(nodo + str(self.port2) + "/register_with",
                      json={'node_address': nodo + str(self.port1)})

        def commentNmine(args):
            requests.post(
                args["url"] + "/new_transaction",
                json={'content': args["content"]}
            )
            requests.get(args["url"] + "/mine")

        # se ejecuta de forma secuencial
        commentNmine({"url": nodo + str(self.port1), "content": "contenido1"})
        commentNmine({"url": nodo + str(self.port2), "content": "contenido2"})

        # las cadenas deberían ser iguales entre los nodos
        ch1 = json.loads(requests.get(
            nodo + str(self.port1) + '/chain').content)["chain"]
        ch2 = json.loads(requests.get(
            nodo + str(self.port2) + '/chain').content)["chain"]

        self.assertEqual(ch1, ch2)

    def test_agregar_nodos(self):
        """ verifica que los nodos se agreguen de forma correcta,
        y que sean borrados cuando salgan de la red. """

        def checkPeers(addr):
            return json.loads(
                requests.get(addr + "/chain").content)["peers"]

        requests.post(nodo + str(self.port2) + "/register_with",
                      json={'node_address': nodo + str(self.port1)})

        self.assertCountEqual(checkPeers(nodo + str(self.port1)), [nodo + str(self.port2) + "/"])
        self.assertCountEqual(checkPeers(nodo + str(self.port2)), [nodo + str(self.port1) + "/"])
        self.assertCountEqual(checkPeers(nodo + str(self.port3)), [])

        requests.post(nodo + str(self.port3) + "/register_with",
                      json={'node_address': nodo + str(self.port1)})

        self.assertCountEqual(checkPeers(nodo + str(self.port1)), [nodo + str(self.port2) + "/", nodo + str(self.port3) + "/"])
        self.assertCountEqual(checkPeers(nodo + str(self.port2)), [nodo + str(self.port1) + "/", nodo + str(self.port3) + "/"])
        self.assertCountEqual(checkPeers(nodo + str(self.port3)), [nodo + str(self.port1) + "/", nodo + str(self.port2) + "/"])

        # prueba eliminar nodos
        requests.get(nodo + str(self.port2) + "/leave")

        self.assertCountEqual(checkPeers(nodo + str(self.port1)), [nodo + str(self.port3) + "/"])
        self.assertCountEqual(checkPeers(nodo + str(self.port3)), [nodo + str(self.port1) + "/"])
