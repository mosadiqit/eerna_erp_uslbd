from odoo.http import request
import graphene


class SaleOrderLine(graphene.ObjectType):
    id = graphene.ID()
    order_id = graphene.ID()
    name = graphene.String()
    product_id = graphene.ID()
    price_unit = graphene.Float()
    product_uom_qty = graphene.Int()
    qty_delivered = graphene.Int()
    qty_invoiced = graphene.Int()
    due_qty = graphene.Int()

    def resolve_due_qty(self, info):
        return self.product_uom_qty - self.qty_delivered

    def resolve_order_id(self, info):
        return self.order_id.id


class SaleOrder(graphene.ObjectType):
    id = graphene.ID()
    name = graphene.String()
    create_date = graphene.DateTime()
    create_uid = graphene.ID()
    order_line = graphene.List(SaleOrderLine)


class Query(graphene.ObjectType):
    sale_order = graphene.List(SaleOrder)

    def resolve_sale_order(self, info):
        print("desired_model = ",request.env['sale.order'])
        return request.env['sale.order'].search([], limit=5)

