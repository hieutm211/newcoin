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


class ConnectNodeResponse(MessageResponse):
    total_nodes: int


class AddTransactionRequest(BaseModel):
    transaction: Transaction
    signature: str


class AddTransactionResponse(MessageResponse):
    pending_transactions: List[Transaction]


class JoinNetworkRequest(BaseModel):
    node: str


class NewWalletResponse(BaseModel):
    private_key: str
    public_key: str


class NewTransactionRequest(BaseModel):
    transaction: Transaction
    private_key: str


class GetBalanceRequest(BaseModel):
    address: str


class GetBalanceResponse(BaseModel):
    total: float
    income: float
    outcome: float


class GetTransactionResponse(BaseModel):
    pending: List[Transaction]
    success: List[Transaction]
