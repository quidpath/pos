"""
POS Service Models

Following Single Source of Truth architecture:
- Products are stored ONLY in Inventory service
- POS stores only transactional and configuration data
- Product references use UUID only (no data duplication)
"""

from .store import Store
from .terminal import POSTerminal
from .session import POSSession
from .order import POSOrder, POSOrderLine, POSPayment
from .promotion import Promotion
from .loyalty import LoyaltyProgram, LoyaltyCard
from .returns import ReturnOrder, ReturnOrderLine

__all__ = [
    'Store',
    'POSTerminal',
    'POSSession',
    'POSOrder',
    'POSOrderLine',
    'POSPayment',
    'Promotion',
    'LoyaltyProgram',
    'LoyaltyCard',
    'ReturnOrder',
    'ReturnOrderLine',
]
