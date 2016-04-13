# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
try:
    from trytond.modules.sale.tests.test_sale_opportunity_purchase_relation_margin import suite
except ImportError:
    from .test_sale_opportunity_purchase_relation_margin import suite

__all__ = ['suite']
