from utils import sign_message
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from configs import ORIGINS
from models import (
    AddTransactionRequest,
    Block,
    GetBalanceRequest,
    GetBalanceResponse,
    GetTransactionResponse,
    NewTransactionRequest,
    NewWalletResponse,
    GetChainResponse,
    ConnectNodeRequest,
    ConnectNodeResponse,
    MessageResponse,
    JoinNetworkRequest,
)

from blockchain import Blockchain
from uuid import uuid4
import requests
from requests.exceptions import ConnectionError
from Crypto.PublicKey import RSA
import logging

logging.basicConfig(level=logging.INFO)

# Creating a Web App
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Creating an address for the node on Port 5000
node_address = str(uuid4()).replace("-", "")

# Creating a Blockchain
blockchain = Blockchain()


# Mining a new block
@app.post("/mine_block", response_model=Block)
async def mine_block(request: GetBalanceRequest):
    if len(blockchain.transactions) == 0:
        raise HTTPException(500, detail="there is no transactions.")

    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block["proof"]
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    block = blockchain.create_block(proof, previous_hash)

    blockchain.add_transaction("root", request.address, 10, "")

    return {
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


@app.post("/add_transaction")
async def add_transaction(request: AddTransactionRequest):
    try:
        block_index = blockchain.add_transaction(
            request.transaction.sender,
            request.transaction.receiver,
            request.transaction.amount,
            request.signature
        )
    except ValueError as err:
        print("slkdfjalkjdfklsjd lskdjfkerr")
        raise HTTPException(400, detail=err.args)

    return block_index


@app.post("/new_transaction")
async def new_transaction(request: NewTransactionRequest):
    print(request)
    message = request.transaction.json()
    try:
        signature = sign_message(message, request.private_key)
    except ValueError as err:
        raise HTTPException(400, detail=err.args)

    try:
        block_index = blockchain.add_transaction(
            request.transaction.sender,
            request.transaction.receiver,
            request.transaction.amount,
            signature
        )
    except ValueError as err:
        raise HTTPException(400, detail=err.args)

    # broadcast to nodes
    for node in blockchain.get_nodes():
        try:
            requests.post(
                f"http://{node}/add_transaction",
                json={
                    **request.transaction.dict(),
                    "signature": signature
                },
                timeout=15
            )
        except ConnectionError:
            logging.error(f"ConnectionError: Cannot connect to '{node}'.")
        else:
            logging.info(f"Connected to node '{node}'.")

    return block_index


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


@app.get("/new-wallet", response_model=NewWalletResponse)
def new_wallet():
    key = RSA.generate(2048)
    private_key = "\n".join(
        key.export_key().decode("utf-8").split("\n")[1:-1]
    )
    public_key = "\n".join(
        key.public_key().export_key().decode("utf-8").split("\n")[1:-1]
    )
    blockchain.add_transaction("root", public_key, 1000, "")
    return {"private_key": private_key, "public_key": public_key}


@app.post("/balance", response_model=GetBalanceResponse)
def get_balance(request: GetBalanceRequest):
    return blockchain.get_balance(request.address)


@app.post("/transactions", response_model=GetTransactionResponse)
def get_transactions(request: GetBalanceRequest):
    return blockchain.get_transactions(request.address)
