from enum import Enum

from pydantic import BaseModel, Field

# Source: https://github.com/pluggyai/pluggy-node/blob/cc904e65641759a90959c7b9263c900295c8e7c7/src/types/transaction.ts


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
    businessName: str | None = None
    cnpj: str | None = None
    cnae: str | None = None
    category: str | None = None


class Transaction(BaseModel):
    id: str  # Primary identifier of the transaction
    date: str = Field(
        ...,
        description="Date the transaction was made in ISO 8601 format, e.g., '2023-10-01T12:00:00Z'",  # Date the transaction was made
    )
    description: str  # Transaction original description
    descriptionRaw: str | None = (
        None  # Raw description provided by the financial institution
    )
    amount: float  # Amount of the transaction
    amountInAccountCurrency: float | None = None  # Amount in account's currency
    balance: float | None = None  # Current balance after transaction
    currencyCode: str  # ISO Currency code of the transaction
    category: str | None = None  # Category name of the transaction
    categoryId: str | None = None  # Category ID of the transaction
    accountId: str | None = None  # Primary identifier of the account
    providerCode: str | None = None  # Unique code provided by the institution
    type: TransactionType  # Direction of the transaction (DEBIT/CREDIT)
    status: TransactionStatus  # Status of the transaction (POSTED/PENDING)
    paymentData: PaymentData | None = (
        None  # Additional data related to payment or transfers
    )
    creditCardMetadata: CreditCardMetadata | None = (
        None  # Additional data for credit card transactions
    )
    merchant: Merchant | None = None  # Merchant associated with the transaction
    providerId: str | None = None  # Provider ID (for Open Finance connectors)
    operationType: str | None = None  # Operation type of the transaction
    operationCategory: str | None = None  # Operation category of the transaction


class TransactionsResponse(BaseModel):
    total: int
    totalPages: int
    page: int
    results: list[Transaction]
