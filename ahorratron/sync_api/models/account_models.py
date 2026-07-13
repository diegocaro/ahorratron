from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from ahorratron.sync_api.models.base import APIBaseModel
from ahorratron.sync_api.utils.helpers import utcnow


# Source: https://github.com/pluggyai/pluggy-node/blob/cc904e65641759a90959c7b9263c900295c8e7c7/src/types/account.ts
class BankData(BaseModel):
    transferNumber: str  # Primary identifier of the account to make bank transfers
    closingBalance: float  # Available balance of the account
    automaticallyInvestedBalance: float  # Automatically invested balance


class AccountType(StrEnum):
    BANK = "BANK"
    CREDIT = "CREDIT"
    PAYMENT_ACCOUNT = "PAYMENT_ACCOUNT"


class AccountSubtype(StrEnum):
    CHECKING_ACCOUNT = "CHECKING_ACCOUNT"
    SAVINGS_ACCOUNT = "SAVINGS_ACCOUNT"
    CREDIT_CARD = "CREDIT_CARD"


class CreditStatus(StrEnum):
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"


class HolderType(StrEnum):
    MAIN = "MAIN"
    ADDITIONAL = "ADDITIONAL"


class CreditLineLimitType(StrEnum):
    LIMITE_CREDITO_TOTAL = "LIMITE_CREDITO_TOTAL"
    LIMITE_CREDITO_MODALIDADE_OPERACAO = "LIMITE_CREDITO_MODALIDADE_OPERACAO"


class ConsolidationType(StrEnum):
    INDIVIDUAL = "INDIVIDUAL"
    CONSOLIDATED = "CONSOLIDATED"


class CreditData(BaseModel):
    minimumPayment: float | None  # Minimum payment required for the credit account
    balanceForeignCurrency: float | None  # Balance in foreign currency
    availableCreditLimit: float | None  # Available credit limit
    creditLimit: float | None  # Total credit limit
    isLimitFlexible: bool | None  # Indicates if the credit limit is flexible
    balanceDueDate: str | None  # Due date for the balance
    balanceCloseDate: str | None  # Date when the balance was closed
    level: str | None  # Account level (e.g., Gold, Platinum)
    brand: str | None  # Brand of the credit card
    status: CreditStatus | None  # Status of the credit account
    holderType: HolderType | None  # Type of account holder


class DisaggregatedCreditLimit(BaseModel):
    creditLineLimitType: CreditLineLimitType | None
    consolidationType: ConsolidationType | None
    identificationNumber: str | None
    isLimitFlexible: bool | None
    usedAmount: float | None
    usedAmountCurrencyCode: str | None
    limitAmount: float | None
    limitAmountCurrencyCode: str | None
    availableAmount: float | None
    availableAmountCurrencyCode: str | None


class Account(APIBaseModel):
    id: str  # Primary identifier of the account
    type: AccountType  # Type of the account (e.g., BANK, CREDIT)
    subtype: AccountSubtype  # Subtype of the account (e.g., CHECKING_ACCOUNT)
    number: str  # Account's financial institution number
    name: str = Field(..., description="Account's name or description")
    balance: float  # Current balance of the account
    itemId: str  # Primary identifier of the Item
    currencyCode: str  # ISO Currency code of the account's amounts
    marketingName: str | None = None  # Account's name provided by the institution
    availableBalance: float | None = None  # Available balance of the account
    creditLimit: float | None = None  # Credit limit of the account
    taxNumber: str | None = None  # Account owner's tax number
    owner: str | None = Field(default=None, description="Account owner's full name")
    institution: str | None = None  # Financial institution name
    status: str | None = None  # Status of the account
    lastUpdated: str | None = None  # Last update timestamp
    category: str | None = None  # Category of the account
    paymentDueDate: str | None = None  # Payment due date for credit accounts
    dueAmount: float | None = None  # Due amount for credit accounts
    minimumPayment: float | None = None  # Minimum payment required
    interestRate: float | None = None  # Interest rate for loans or credit
    investmentType: str | None = None  # Type of investment account
    loanType: str | None = None  # Type of loan account
    bankData: BankData | None = None  # Account related bank data (if BANK type)
    creditData: CreditData | None = None  # Account related credit data (if CREDIT type)
    disaggregatedCreditLimits: list[DisaggregatedCreditLimit] | None = (
        None  # Disaggregated credit limits
    )
    createdAt: datetime = Field(default_factory=utcnow)
    updatedAt: datetime = Field(default_factory=utcnow)


class AccountsResponse(BaseModel):
    results: list[Account]
    total: int
    page: int
    totalPages: int
