import os
import signal
import concurrent.futures
import unittest
import requests
import json

from node_server import create_app

# aliases
nodo1 = "http://localhost:8000"
nodo2 = "http://localhost:8001"
nodo3 = "http://localhost:8002"


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
        self.maxDiff = None
        self.node1 = create_app()
        self.node2 = create_app()
        self.node3 = create_app()
        self.pid1 = os.fork()
        if self.pid1 == 0:
            self.node1.run(port=8000)

        self.pid2 = os.fork()
        if self.pid2 == 0:
            self.node2.run(port=8001)

        self.pid3 = os.fork()
        if self.pid3 == 0:
            self.node3.run(port=8002)

    def tearDown(self):
        """ elimina los servidores """
        for pid in [self.pid1, self.pid2, self.pid3]:
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                # looks pretty bad, but ¯\_(ツ)_/¯
                pass

    # ### ### pruebas

    def test_dos_nodos_diff(self):
        """ prueba que los nodos generados sean diferentes """
        requests.post(
            'http://localhost:8000/new_transaction',
            json={'content': 'contenido'}
        )

        rs1 = requests.get('http://localhost:8000/pending_tx')
        rs2 = requests.get('http://localhost:8001/pending_tx')
        self.assertNotEqual(rs1.content, rs2.content)

    # FIXME los nodos no realizan consenso cuando se minan en paralelo
    # def test_consenso_paralelo(self):
    #     """prueba que los nodos se pongan de acuerdo tras recibir un mensaje y
    #     minarlo."""
    #     # primero conectamos los nodos
    #     requests.post("http://localhost:8001/register_with",
    #                   json={'node_address': 'http://localhost:8000'})

    #     def commentNmine(args):
    #         print("agregando la transacción")
    #         requests.post(
    #             args["url"] + "/new_transaction",
    #             json={'content': args["content"]}
    #         )
    #         print("minando la transacción")
    #         requests.get(args["url"] + "/mine")

    #     # actualización paralela de los nodos.
    #     with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    #         pool.map(commentNmine, [{"url": "http://localhost:8000",
    #                                  "content": "contenido1"},
    #                                 {"url": "http://localhost:8001",
    #                                  "content": "contenido2"}])

    #     # las cadenas deberían ser iguales entre los nodos
    #     ch1 = json.loads(requests.get(
    #         'http://localhost:8000/chain').content)["chain"]
    #     print(ch1)
    #     ch2 = json.loads(requests.get(
    #         'http://localhost:8001/chain').content)["chain"]
    #     print(ch2)

    #     self.assertEqual(ch1, ch2)

    def test_consenso_seq(self):
        """prueba que los nodos se pongan de acuerdo tras recibir un mensaje y
        minarlo."""
        # primero conectamos los nodos
        requests.post(nodo2 + "/register_with",
                      json={'node_address': nodo1})

        def commentNmine(args):
            requests.post(
                args["url"] + "/new_transaction",
                json={'content': args["content"]}
            )
            requests.get(args["url"] + "/mine")

        # se ejecuta de forma secuencial
        commentNmine({"url": nodo1, "content": "contenido1"})
        commentNmine({"url": nodo2, "content": "contenido2"})

        # las cadenas deberían ser iguales entre los nodos
        ch1 = json.loads(requests.get(
            nodo1 + '/chain').content)["chain"]
        ch2 = json.loads(requests.get(
            nodo2 + '/chain').content)["chain"]

        self.assertEqual(ch1, ch2)

    def test_agregar_nodos(self):
        """ verifica que los nodos se agreguen de forma correcta,
        y que sean borrados cuando salgan de la red. """

        def checkPeers(addr):
            return json.loads(
                requests.get(addr + "/chain").content)["peers"]

        requests.post(nodo2 + "/register_with",
                      json={'node_address': nodo1})

        self.assertCountEqual(checkPeers(nodo1), [nodo2 + "/"])
        self.assertCountEqual(checkPeers(nodo2), [nodo1 + "/"])
        self.assertCountEqual(checkPeers(nodo3), [])

        requests.post(nodo3 + "/register_with",
                      json={'node_address': nodo1})

        self.assertCountEqual(checkPeers(nodo1), [nodo2 + "/", nodo3 + "/"])
        self.assertCountEqual(checkPeers(nodo2), [nodo1 + "/", nodo3 + "/"])
        self.assertCountEqual(checkPeers(nodo3), [nodo1 + "/", nodo2 + "/"])

        # prueba eliminar nodos
        requests.get(nodo2 + "/leave")

        self.assertCountEqual(checkPeers(nodo1), [nodo3 + "/"])
        self.assertCountEqual(checkPeers(nodo3), [nodo1 + "/"])
