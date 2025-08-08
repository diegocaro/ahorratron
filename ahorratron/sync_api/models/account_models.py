from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class BankData(BaseModel):
    transferNumber: Optional[str]
    closingBalance: Optional[float]
    automaticallyInvestedBalance: Optional[float]
    overdraftContractedLimit: Optional[float]
    overdraftUsedLimit: Optional[float]
    unarrangedOverdraftAmount: Optional[float]


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
    name: str
    balance: float
    itemId: str
    currencyCode: str
    marketingName: Optional[str] = None
    availableBalance: Optional[float] = None
    creditLimit: Optional[float] = None
    taxNumber: Optional[str] = None
    owner: Optional[str] = None
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


class AccountsResponse(BaseModel):
    results: List[Account]
    total: int
    page: Optional[int] = None
    totalPages: Optional[int] = None
