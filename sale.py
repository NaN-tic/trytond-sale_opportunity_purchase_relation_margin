# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from decimal import Decimal

from trytond.pool import Pool, PoolMeta
from trytond.modules.product import price_digits

__all__ = ['SaleLine', 'Purchase', 'PurchaseLine']
__metaclass__ = PoolMeta

_QUANTIZE = Decimal(str(10 ** -price_digits[1]))
_CONFIRMED_STATES = ('confirmed', 'processing', 'done')


class SaleLine:
    __name__ = 'sale.line'

    @classmethod
    def update_cost_price(cls, lines):
        pool = Pool()
        Sale = pool.get('sale.sale')

        to_write = []
        sales = set()
        for line in lines:
            new_cost_price = line.calc_cost_price_from_purchase_lines()
            if new_cost_price != line.cost_price:
                to_write.extend(([line], {
                            'cost_price': new_cost_price,
                            }))
                if line.sale.state not in ('draft', 'quotation'):
                    sales.add(line.sale)

        if to_write:
            cls.write(*to_write)

        # Ensure that the margin cache is valid
        if sales:
            sales = list(sales)
            Sale.write(sales, {'margin_cache': None})
            Sale.store_cache(sales)

    def calc_cost_price_from_purchase_lines(self):
        if not self.purchase_lines:
            return self.product.cost_price

        confirmed_purchase_lines = any(l.purchase.state in _CONFIRMED_STATES
            for l in self.purchase_lines)
        cost_price = Decimal('0.0')
        quantity = 0
        for purchase_line in self.purchase_lines:
            if purchase_line.purchase.state == 'cancel':
                continue
            if (not confirmed_purchase_lines
                    or purchase_line.purchase.state in _CONFIRMED_STATES):
                cost_price += purchase_line.amount
                quantity += purchase_line.quantity
        if quantity:
            return (cost_price / Decimal(str(quantity))).quantize(_QUANTIZE)
        if self.product:
            return self.product.cost_price
        return cost_price


class Purchase:
    __name__ = 'purchase.purchase'

    @classmethod
    def cancel(cls, purchases):
        super(Purchase, cls).cancel(purchases)
        PurchaseLine.update_sale_lines_cost_price([l for p in purchases
                for l in p.lines])

    @classmethod
    def draft(cls, purchases):
        super(Purchase, cls).draft(purchases)
        PurchaseLine.update_sale_lines_cost_price([l for p in purchases
                for l in p.lines])

    @classmethod
    def confirm(cls, purchases):
        super(Purchase, cls).confirm(purchases)
        PurchaseLine.update_sale_lines_cost_price([l for p in purchases
                for l in p.lines])


class PurchaseLine:
    __name__ = 'purchase.line'

    @classmethod
    def create(cls, vlist):
        purchase_lines = super(PurchaseLine, cls).create(vlist)
        cls.update_sale_lines_cost_price(purchase_lines)
        return purchase_lines

    @classmethod
    def write(cls, *args):
        actions = iter(args)
        modified_lines = []
        for lines, values in zip(actions, actions):
            if 'unit_price' in values or 'sale_lines' in values:
                modified_lines.extend(lines)

        super(PurchaseLine, cls).write(*args)

        cls.update_sale_lines_cost_price(modified_lines)

    @classmethod
    def update_sale_lines_cost_price(cls, lines):
        pool = Pool()
        SaleLine = pool.get('sale.line')

        if not lines:
            return

        sale_lines = SaleLine.search([
                ('purchase_lines', 'in', [l.id for l in lines]),
                ])
        if sale_lines:
            SaleLine.update_cost_price(sale_lines)
