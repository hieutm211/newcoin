from fastapi import FastAPI
from models import (
    Transaction,
    MineBlockResponse,
    GetChainResponse,
    ConnectNodeRequest,
    ConnectNodeResponse,
    MessageResponse,
    AddTransactionResponse,
    JoinNetworkRequest,
)

from blockchain import Blockchain
from uuid import uuid4
import requests
from requests.exceptions import ConnectionError
import logging

logging.basicConfig(level=logging.INFO)

# Creating a Web App
app = FastAPI()

# Creating an address for the node on Port 5000
node_address = str(uuid4()).replace("-", "")

# Creating a Blockchain
blockchain = Blockchain()


# Mining a new block
@app.get("/mine_block", response_model=MineBlockResponse)
async def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block["proof"]
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    block = blockchain.create_block(proof, previous_hash)

    return {
        "message": "Congratulations, you just mined a block!",
        "index": block["index"],
        "timestamp": block["timestamp"],
        "proof": block["proof"],
        "previous_hash": block["previous_hash"],
        "transactions": block["transactions"],
    }


# Getting the full blockchain
@app.get("/get_chain", response_model=GetChainResponse)
async def get_chain():
    response = {"chain": blockchain.chain, "length": len(blockchain.chain)}
    return response


# Checking if the Blockchain is valid
@app.get("/is_valid", response_model=MessageResponse)
async def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)

    if is_valid:
        response = {"message": "All good. The Blockchain is valid."}
    else:
        response = {
            "message": (
                "Houston, we have a problem. The Blockchain is not valid."
            )
        }

    return response


@app.post("/add_transaction", response_model=AddTransactionResponse)
async def add_transaction(transaction: Transaction):
    index = blockchain.add_transaction(**vars(transaction))
    return {
        "message": f"This transaction will be added to Block {index}",
        "pending_transactions": blockchain.transactions,
    }


# Connecting new nodes


@app.post("/connect_node", response_model=ConnectNodeResponse)
async def connect_node(request: ConnectNodeRequest):
    blockchain.add_node(request.node)
    return {
        "message": "All the nodes are now connected.",
        "total_nodes": len(list(blockchain.nodes)),
    }


# Replaceing the chain by the longest chain if needed
@app.get("/replace_chain", response_model=MessageResponse)
async def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {
            "message": (
                "The nodes had different chains so the chain "
                "was replaced by the longest chain."
            ),
        }
    else:
        response = {
            "message": "All good. The chain is the largest one",
        }

    return response


@app.post("/join_network")
def join_network(request: JoinNetworkRequest):
    nodes = blockchain.get_nodes()
    for node in nodes:
        try:
            requests.post(
                f"http://{node}/connect_node", json={"node": request.node}
            )
        except ConnectionError:
            logging.error(f"ConnectionError: Cannot connect to '{node}'.")
        else:
            logging.info(f"Connected to node '{node}'.")
