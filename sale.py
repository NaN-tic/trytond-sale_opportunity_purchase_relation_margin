#The COPYRIGHT file at the top level of this repository contains
#the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta

__all__ = ['SaleLine', 'PurchaseLine']
__metaclass__ = PoolMeta


class SaleLine:
    __name__ = 'sale.line'

    @fields.depends('purchase_lines')
    def on_change_purchase_lines(self):
        changes = {}
        if self.purchase_lines:
            changes['cost_price'] = self.purchase_lines[0].unit_price
        return changes


class PurchaseLine:
    __name__ = 'purchase.line'

    @classmethod
    def write(cls, *args):
        pool = Pool()
        SaleLine = pool.get('sale.line')
        Sale = pool.get('sale.sale')
        actions = iter(args)
        to_check = []
        for lines, values in zip(actions, actions):
            if 'unit_price' in values:
                to_check.extend(lines)
        super(PurchaseLine, cls).write(*args)
        to_write = []
        lines = SaleLine.search([
                ('purchase_lines', 'in', [l.id for l in to_check]),
                ])
        sales = set()
        for line in lines:
            if (line.purchase_lines and
                    line.cost_price != line.purchase_lines[0].unit_price):
                to_write.extend(([line], {
                            'cost_price': line.purchase_lines[0].unit_price,
                            }))
                if line.sale.state not in ('draft', 'quotation'):
                    sales.add(line.sale)
        if to_write:
            SaleLine.write(*to_write)
        # Ensure that the margin cache is valid
        if sales:
            sales = list(sales)
            Sale.write(sales, {'margin_cache': None})
            Sale.store_cache(sales)
