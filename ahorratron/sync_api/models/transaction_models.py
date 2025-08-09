from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class TransactionStatus(str, Enum):
    POSTED = "POSTED"
    PENDING = "PENDING"


class TransactionType(str, Enum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"


class PaymentMethod(str, Enum):
    PIX = "PIX"
    TED = "TED"
    DOC = "DOC"
    BOLETO = "BOLETO"


class DocumentType(str, Enum):
    CPF = "CPF"
    CNPJ = "CNPJ"


class DocumentNumber(BaseModel):
    type: DocumentType
    value: str


class Participant(BaseModel):
    name: Optional[str]
    branchNumber: Optional[str]
    accountNumber: Optional[str]
    routingNumber: Optional[str]
    routingNumberISPB: Optional[str]
    documentNumber: Optional[DocumentNumber]


class BoletoMetadata(BaseModel):
    digitableLine: Optional[str]
    barcode: Optional[str]
    baseAmount: Optional[float]
    interestAmount: Optional[float]
    penaltyAmount: Optional[float]
    discountAmount: Optional[float]


class PaymentData(BaseModel):
    payer: Optional[Participant]
    receiver: Optional[Participant]
    referenceNumber: Optional[str]
    receiverReferenceId: Optional[str]
    paymentMethod: Optional[PaymentMethod]
    reason: Optional[str]
    boletoMetadata: Optional[BoletoMetadata]


class CreditCardMetadata(BaseModel):
    installmentNumber: Optional[int]
    totalInstallments: Optional[int]
    totalAmount: Optional[float]
    payeeMCC: Optional[int]
    cardNumber: Optional[str]
    billId: Optional[str]
    purchaseDate: Optional[str]


class Merchant(BaseModel):
    name: Optional[str]
    businessName: Optional[str]
    cnpj: Optional[str]
    cnae: Optional[str]
    category: Optional[str]


class Transaction(BaseModel):
    id: str
    date: str = Field(
        ...,
        description="Date of the transaction in ISO 8601 format, e.g., '2023-10-01T12:00:00Z'",
    )
    description: str
    descriptionRaw: Optional[str] = None
    amount: float
    amountInAccountCurrency: Optional[float] = None
    balance: Optional[float] = None
    currencyCode: str
    category: Optional[str] = None
    categoryId: Optional[str] = None
    accountId: Optional[str] = None
    providerCode: Optional[str] = None
    type: TransactionType
    status: TransactionStatus
    paymentData: Optional[PaymentData] = None
    creditCardMetadata: Optional[CreditCardMetadata] = None
    merchant: Optional[Merchant] = None
    providerId: Optional[str] = None
    operationType: Optional[str] = None
    operationCategory: Optional[str] = None


class TransactionsResponse(BaseModel):
    total: int
    totalPages: int
    page: int
    results: List[Transaction]
