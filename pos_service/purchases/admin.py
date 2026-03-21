from django.contrib import admin
from .models import Supplier, PurchaseRequisition, PurchaseOrder, GoodsReceipt, SupplierBill

admin.site.register(Supplier)
admin.site.register(PurchaseRequisition)

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ["po_number", "supplier", "state", "total_amount", "created_at"]
    list_filter = ["state"]

admin.site.register(GoodsReceipt)
admin.site.register(SupplierBill)
