from enum import Enum

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
    name: str | None
    branchNumber: str | None
    accountNumber: str | None
    routingNumber: str | None
    routingNumberISPB: str | None
    documentNumber: DocumentNumber | None


class BoletoMetadata(BaseModel):
    digitableLine: str | None
    barcode: str | None
    baseAmount: float | None
    interestAmount: float | None
    penaltyAmount: float | None
    discountAmount: float | None


class PaymentData(BaseModel):
    payer: Participant | None
    receiver: Participant | None
    referenceNumber: str | None
    receiverReferenceId: str | None
    paymentMethod: PaymentMethod | None
    reason: str | None
    boletoMetadata: BoletoMetadata | None


class CreditCardMetadata(BaseModel):
    installmentNumber: int | None
    totalInstallments: int | None
    totalAmount: float | None
    payeeMCC: int | None
    cardNumber: str | None
    billId: str | None
    purchaseDate: str | None


class Merchant(BaseModel):
    name: str | None
    businessName: str | None
    cnpj: str | None
    cnae: str | None
    category: str | None


class Transaction(BaseModel):
    id: str
    date: str = Field(
        ...,
        description="Date of the transaction in ISO 8601 format, e.g., '2023-10-01T12:00:00Z'",
    )
    description: str
    descriptionRaw: str | None = None
    amount: float
    amountInAccountCurrency: float | None = None
    balance: float | None = None
    currencyCode: str
    category: str | None = None
    categoryId: str | None = None
    accountId: str | None = None
    providerCode: str | None = None
    type: TransactionType
    status: TransactionStatus
    paymentData: PaymentData | None = None
    creditCardMetadata: CreditCardMetadata | None = None
    merchant: Merchant | None = None
    providerId: str | None = None
    operationType: str | None = None
    operationCategory: str | None = None


class TransactionsResponse(BaseModel):
    total: int
    totalPages: int
    page: int
    results: list[Transaction]
