from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field


class BankData(BaseModel):
    transferNumber: str
    closingBalance: float
    automaticallyInvestedBalance: float


class AccountType(str, Enum):
    BANK = "BANK"
    CREDIT = "CREDIT"
    PAYMENT_ACCOUNT = "PAYMENT_ACCOUNT"


class AccountSubtype(str, Enum):
    CHECKING_ACCOUNT = "CHECKING_ACCOUNT"
    SAVINGS_ACCOUNT = "SAVINGS_ACCOUNT"
    CREDIT_CARD = "CREDIT_CARD"


class CreditStatus(str, Enum):
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"


class HolderType(str, Enum):
    MAIN = "MAIN"
    ADDITIONAL = "ADDITIONAL"


class CreditLineLimitType(str, Enum):
    LIMITE_CREDITO_TOTAL = "LIMITE_CREDITO_TOTAL"
    LIMITE_CREDITO_MODALIDADE_OPERACAO = "LIMITE_CREDITO_MODALIDADE_OPERACAO"


class ConsolidationType(str, Enum):
    INDIVIDUAL = "INDIVIDUAL"
    CONSOLIDATED = "CONSOLIDATED"


class CreditData(BaseModel):
    minimumPayment: float | None
    balanceForeignCurrency: float | None
    availableCreditLimit: float | None
    creditLimit: float | None
    isLimitFlexible: bool | None
    balanceDueDate: str | None
    balanceCloseDate: str | None
    level: str | None
    brand: str | None
    status: CreditStatus | None
    holderType: HolderType | None


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


class Account(BaseModel):
    id: str
    type: AccountType
    subtype: AccountSubtype
    number: str
    name: str = Field(..., description="Name of the account")
    balance: float
    itemId: str
    currencyCode: str
    marketingName: str | None = None
    availableBalance: float | None = None
    creditLimit: float | None = None
    taxNumber: str | None = None
    owner: str | None = Field(
        default=None, description="Name of the owner of the account"
    )
    institution: str | None = None
    status: str | None = None
    lastUpdated: str | None = None
    category: str | None = None
    paymentDueDate: str | None = None
    dueAmount: float | None = None
    minimumPayment: float | None = None
    interestRate: float | None = None
    investmentType: str | None = None
    loanType: str | None = None
    bankData: BankData | None = None
    creditData: CreditData | None = None
    disaggregatedCreditLimits: list[DisaggregatedCreditLimit] | None = None
    updatedAt: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="Last updated timestamp in ISO 8601 format UTC",
    )


class AccountsResponse(BaseModel):
    results: list[Account]
    total: int
    page: int
    totalPages: int
