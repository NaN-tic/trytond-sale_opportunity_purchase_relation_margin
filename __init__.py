# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .sale import *


def register():
    Pool.register(
        SaleLine,
        Purchase,
        PurchaseLine,
        module='sale_opportunity_purchase_relation_margin', type_='model')
