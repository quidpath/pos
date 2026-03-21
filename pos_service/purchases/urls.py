from django.urls import path

from .views.purchases_views import (
    approve_po,
    approve_requisition,
    bill_detail,
    bill_list_create,
    grn_list_create,
    po_detail,
    po_list_create,
    requisition_detail,
    requisition_list_create,
    supplier_detail,
    supplier_list_create,
    validate_grn,
)

urlpatterns = [
    path("suppliers/", supplier_list_create),
    path("suppliers/<uuid:pk>/", supplier_detail),
    path("requisitions/", requisition_list_create),
    path("requisitions/<uuid:pk>/", requisition_detail),
    path("requisitions/<uuid:pk>/approve/", approve_requisition),
    path("orders/", po_list_create),
    path("orders/<uuid:pk>/", po_detail),
    path("orders/<uuid:pk>/approve/", approve_po),
    path("receipts/", grn_list_create),
    path("receipts/<uuid:pk>/validate/", validate_grn),
    path("bills/", bill_list_create),
    path("bills/<uuid:pk>/", bill_detail),
]
