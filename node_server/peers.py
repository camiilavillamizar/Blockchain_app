""" auxiliary functions to deal with peers.
"""
from typing import List, Set


def current_peers(chain: List) -> Set:
    """ evaluates the current peers in the network by adding
    up the diffs on the blockchain.

    it searches the blockchain from the bottom up, looking for transactions
    of type "peer_change". They can be of either leaving or entering, together
    with the address.
    """
    peers = set()
    for block in chain:
        for trans in block["transactions"]:
            if trans["type"] == "peer_change":
                if trans["entering"]:
                    peers.add(trans["address"])
                else:
                    peers.remove(trans["address"])
    return peers
