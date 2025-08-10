from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

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
    minimumPayment: Optional[float]
    balanceForeignCurrency: Optional[float]
    availableCreditLimit: Optional[float]
    creditLimit: Optional[float]
    isLimitFlexible: Optional[bool]
    balanceDueDate: Optional[str]
    balanceCloseDate: Optional[str]
    level: Optional[str]
    brand: Optional[str]
    status: Optional[CreditStatus]
    holderType: Optional[HolderType]


class DisaggregatedCreditLimit(BaseModel):
    creditLineLimitType: Optional[CreditLineLimitType]
    consolidationType: Optional[ConsolidationType]
    identificationNumber: Optional[str]
    isLimitFlexible: Optional[bool]
    usedAmount: Optional[float]
    usedAmountCurrencyCode: Optional[str]
    limitAmount: Optional[float]
    limitAmountCurrencyCode: Optional[str]
    availableAmount: Optional[float]
    availableAmountCurrencyCode: Optional[str]


class Account(BaseModel):
    id: str
    type: AccountType
    subtype: AccountSubtype
    number: str
    name: str = Field(..., description="Name of the account")
    balance: float
    itemId: str
    currencyCode: str
    marketingName: Optional[str] = None
    availableBalance: Optional[float] = None
    creditLimit: Optional[float] = None
    taxNumber: Optional[str] = None
    owner: Optional[str] = Field(
        default=None, description="Name of the owner of the account"
    )
    institution: Optional[str] = None
    status: Optional[str] = None
    lastUpdated: Optional[str] = None
    category: Optional[str] = None
    paymentDueDate: Optional[str] = None
    dueAmount: Optional[float] = None
    minimumPayment: Optional[float] = None
    interestRate: Optional[float] = None
    investmentType: Optional[str] = None
    loanType: Optional[str] = None
    bankData: Optional[BankData] = None
    creditData: Optional[CreditData] = None
    disaggregatedCreditLimits: Optional[List[DisaggregatedCreditLimit]] = None
    updatedAt: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Last updated timestamp in ISO 8601 format UTC",
    )


class AccountsResponse(BaseModel):
    results: List[Account]
    total: int
    page: int
    totalPages: int
