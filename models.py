from pydantic import BaseModel
from typing import List


class Transaction(BaseModel):
    sender: str
    receiver: str
    amount: float


class Block(BaseModel):
    index: int
    timestamp: str
    proof: int
    previous_hash: str
    transactions: List[Transaction]


class GetChainResponse(BaseModel):
    chain: List[Block]
    length: int


class MessageResponse(BaseModel):
    message: str


class ConnectNodeRequest(BaseModel):
    node: str


class MineBlockResponse(Block):
    message: str


class ConnectNodeResponse(MessageResponse):
    total_nodes: int


class AddTransactionResponse(MessageResponse):
    pending_transactions: List[Transaction]


class JoinNetworkRequest(BaseModel):
    node: str
