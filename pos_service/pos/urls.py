from django.urls import path

from .views.pos_views import (
    add_order_line,
    close_session,
    loyalty_card_lookup,
    loyalty_program_list_create,
    open_session,
    order_detail,
    order_list_create,
    process_payment,
    process_return,
    promotion_list_create,
    remove_order_line,
    session_list,
    store_detail,
    store_list_create,
    mark_order_as_paid,
    list_pending_orders,
)
from .views.summary import pos_summary
from .views.invoice_conversion import (
    convert_to_invoice,
    get_invoice_status,
    list_uninvoiced_orders,
)
from .views.product_views import (
    search_products,
    get_product,
    list_products_for_sale,
    get_products_bulk,
    check_stock,
)
from .views.product_sync import (
    sync_product_to_inventory,
    auto_sync_products,
)
# Product sync removed - using inventory query API directly

urlpatterns = [
    path("summary/", pos_summary, name="pos_summary"),
    path("stores/", store_list_create),
    path("stores/<uuid:pk>/", store_detail),
    path("terminals/<uuid:terminal_pk>/sessions/open/", open_session),
    path("sessions/", session_list),
    path("sessions/<uuid:pk>/close/", close_session),
    path("orders/", order_list_create),
    path("orders/<uuid:pk>/", order_detail),
    path("orders/<uuid:order_pk>/lines/", add_order_line),
    path("orders/<uuid:order_pk>/lines/<uuid:line_pk>/", remove_order_line),
    path("orders/<uuid:order_pk>/pay/", process_payment),
    path("orders/<uuid:order_pk>/return/", process_return),
    # Mark order as paid (for pending orders)
    path("orders/<uuid:order_pk>/mark-as-paid/", mark_order_as_paid, name="mark_order_as_paid"),
    path("orders/pending/", list_pending_orders, name="list_pending_orders"),
    # Invoice conversion endpoints
    path("orders/<uuid:order_pk>/convert-to-invoice/", convert_to_invoice, name="convert_to_invoice"),
    path("orders/<uuid:order_pk>/invoice-status/", get_invoice_status, name="get_invoice_status"),
    path("orders/uninvoiced/", list_uninvoiced_orders, name="list_uninvoiced_orders"),
    # Promotions & Loyalty
    path("promotions/", promotion_list_create),
    path("loyalty/programs/", loyalty_program_list_create),
    path("loyalty/cards/lookup/", loyalty_card_lookup),
    # Product query endpoints (from inventory service)
    path("products/", list_products_for_sale, name="list_products_for_sale"),
    path("products/search/", search_products, name="search_products"),
    path("products/bulk/", get_products_bulk, name="get_products_bulk"),
    path("products/auto-sync/", auto_sync_products, name="auto_sync_products"),
    path("products/<uuid:product_id>/", get_product, name="get_product"),
    path("products/<uuid:product_id>/stock/", check_stock, name="check_stock"),
    path("products/<uuid:product_id>/sync/", sync_product_to_inventory, name="sync_product_to_inventory"),
]
