from django.contrib import admin
from .models import Store, POSTerminal, POSSession, POSOrder, POSOrderLine, POSPayment, Promotion, LoyaltyProgram, LoyaltyCard, ReturnOrder

admin.site.register(Store)
admin.site.register(POSTerminal)
admin.site.register(POSSession)
admin.site.register(Promotion)
admin.site.register(LoyaltyProgram)
admin.site.register(LoyaltyCard)


class POSOrderLineInline(admin.TabularInline):
    model = POSOrderLine
    extra = 0


@admin.register(POSOrder)
class POSOrderAdmin(admin.ModelAdmin):
    list_display = ["order_number", "state", "total_amount", "created_at"]
    list_filter = ["state"]
    search_fields = ["order_number", "customer_name"]
    inlines = [POSOrderLineInline]
