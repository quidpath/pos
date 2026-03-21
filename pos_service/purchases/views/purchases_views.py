import logging
import uuid
from decimal import Decimal

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from pos_service.purchases.models import (
    GoodsReceipt, GoodsReceiptLine, PurchaseOrder, PurchaseOrderLine,
    PurchaseRequisition, PurchaseRequisitionLine, RFQ, RFQLine,
    RFQSupplierQuote, Supplier, SupplierBill, SupplierContact,
)
from pos_service.purchases.serializers import (
    GoodsReceiptSerializer, PurchaseOrderSerializer,
    PurchaseRequisitionSerializer, RFQSerializer, RFQSupplierQuoteSerializer,
    SupplierBillSerializer, SupplierSerializer,
)
from pos_service.services.inventory_client import InventoryClient

logger = logging.getLogger(__name__)
inventory_client = InventoryClient()


def _ref(prefix):
    return f"{prefix}-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"


# ─── Suppliers ───────────────────────────────────────────────────────────────

@api_view(["GET", "POST"])
def supplier_list_create(request):
    corporate_id = request.corporate_id
    if request.method == "GET":
        qs = Supplier.objects.filter(corporate_id=corporate_id)
        search = request.GET.get("search")
        if search:
            from django.db.models import Q
            qs = qs.filter(Q(name__icontains=search) | Q(email__icontains=search))
        return Response(SupplierSerializer(qs, many=True).data)
    s = SupplierSerializer(data=request.data)
    if s.is_valid():
        s.save(corporate_id=corporate_id)
        return Response(s.data, status=201)
    return Response(s.errors, status=400)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
def supplier_detail(request, pk):
    corporate_id = request.corporate_id
    try:
        supplier = Supplier.objects.get(pk=pk, corporate_id=corporate_id)
    except Supplier.DoesNotExist:
        return Response({"error": "Not found"}, status=404)
    if request.method == "GET":
        return Response(SupplierSerializer(supplier).data)
    if request.method in ("PUT", "PATCH"):
        s = SupplierSerializer(supplier, data=request.data, partial=request.method == "PATCH")
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=400)
    supplier.is_active = False
    supplier.save()
    return Response(status=204)


# ─── Purchase Requisitions ───────────────────────────────────────────────────

@api_view(["GET", "POST"])
def requisition_list_create(request):
    corporate_id = request.corporate_id
    if request.method == "GET":
        return Response(PurchaseRequisitionSerializer(
            PurchaseRequisition.objects.filter(corporate_id=corporate_id), many=True
        ).data)
    ref = _ref("PR")
    s = PurchaseRequisitionSerializer(data={**request.data, "reference": ref, "corporate_id": str(corporate_id)})
    if s.is_valid():
        pr = s.save(corporate_id=corporate_id, requested_by=request.user_id)
        for line_data in request.data.get("lines", []):
            PurchaseRequisitionLine.objects.create(requisition=pr, **line_data)
        return Response(PurchaseRequisitionSerializer(pr).data, status=201)
    return Response(s.errors, status=400)


@api_view(["GET", "PATCH"])
def requisition_detail(request, pk):
    corporate_id = request.corporate_id
    try:
        pr = PurchaseRequisition.objects.get(pk=pk, corporate_id=corporate_id)
    except PurchaseRequisition.DoesNotExist:
        return Response({"error": "Not found"}, status=404)
    if request.method == "GET":
        return Response(PurchaseRequisitionSerializer(pr).data)
    s = PurchaseRequisitionSerializer(pr, data=request.data, partial=True)
    if s.is_valid():
        s.save()
        return Response(s.data)
    return Response(s.errors, status=400)


@api_view(["POST"])
def approve_requisition(request, pk):
    corporate_id = request.corporate_id
    try:
        pr = PurchaseRequisition.objects.get(pk=pk, corporate_id=corporate_id, state="submitted")
    except PurchaseRequisition.DoesNotExist:
        return Response({"error": "Not found or not submitted"}, status=404)
    pr.state = "approved"
    pr.approved_by = request.user_id
    pr.save()
    return Response(PurchaseRequisitionSerializer(pr).data)


# ─── Purchase Orders ─────────────────────────────────────────────────────────

@api_view(["GET", "POST"])
def po_list_create(request):
    corporate_id = request.corporate_id
    if request.method == "GET":
        qs = PurchaseOrder.objects.filter(corporate_id=corporate_id).select_related("supplier")
        state = request.GET.get("state")
        if state:
            qs = qs.filter(state=state)
        supplier = request.GET.get("supplier")
        if supplier:
            qs = qs.filter(supplier_id=supplier)
        return Response(PurchaseOrderSerializer(qs, many=True).data)

    po_number = _ref("PO")
    supplier_id = request.data.get("supplier")
    try:
        supplier = Supplier.objects.get(pk=supplier_id, corporate_id=corporate_id)
    except Supplier.DoesNotExist:
        return Response({"error": "Supplier not found"}, status=400)

    po = PurchaseOrder.objects.create(
        corporate_id=corporate_id,
        po_number=po_number,
        supplier=supplier,
        currency=request.data.get("currency", "KES"),
        payment_terms_days=request.data.get("payment_terms_days", supplier.payment_terms_days),
        expected_delivery_date=request.data.get("expected_delivery_date"),
        notes=request.data.get("notes", ""),
        created_by=request.user_id,
    )
    for line_data in request.data.get("lines", []):
        PurchaseOrderLine.objects.create(order=po, **{
            "product_id": line_data["product_id"],
            "product_name": line_data["product_name"],
            "quantity": Decimal(str(line_data["quantity"])),
            "uom": line_data.get("uom", "Units"),
            "unit_price": Decimal(str(line_data["unit_price"])),
            "tax_rate": Decimal(str(line_data.get("tax_rate", "16"))),
            "expected_date": line_data.get("expected_date"),
        })
    po.recalculate()
    return Response(PurchaseOrderSerializer(po).data, status=201)


@api_view(["GET", "PATCH"])
def po_detail(request, pk):
    corporate_id = request.corporate_id
    try:
        po = PurchaseOrder.objects.get(pk=pk, corporate_id=corporate_id)
    except PurchaseOrder.DoesNotExist:
        return Response({"error": "Not found"}, status=404)
    if request.method == "GET":
        return Response(PurchaseOrderSerializer(po).data)
    s = PurchaseOrderSerializer(po, data=request.data, partial=True)
    if s.is_valid():
        s.save()
        po.recalculate()
        return Response(PurchaseOrderSerializer(po).data)
    return Response(s.errors, status=400)


@api_view(["POST"])
def approve_po(request, pk):
    corporate_id = request.corporate_id
    try:
        po = PurchaseOrder.objects.get(pk=pk, corporate_id=corporate_id, state="submitted")
    except PurchaseOrder.DoesNotExist:
        return Response({"error": "Not found or not submitted"}, status=404)
    po.state = "approved"
    po.approved_by = request.user_id
    po.save()
    return Response(PurchaseOrderSerializer(po).data)


# ─── Goods Receipts ──────────────────────────────────────────────────────────

@api_view(["GET", "POST"])
def grn_list_create(request):
    corporate_id = request.corporate_id
    if request.method == "GET":
        return Response(GoodsReceiptSerializer(
            GoodsReceipt.objects.filter(corporate_id=corporate_id).select_related("purchase_order"), many=True
        ).data)
    po_id = request.data.get("purchase_order")
    try:
        po = PurchaseOrder.objects.get(pk=po_id, corporate_id=corporate_id)
    except PurchaseOrder.DoesNotExist:
        return Response({"error": "PO not found"}, status=400)

    ref = _ref("GRN")
    grn = GoodsReceipt.objects.create(
        corporate_id=corporate_id,
        reference=ref,
        purchase_order=po,
        warehouse_id=request.data.get("warehouse_id"),
        location_id=request.data.get("location_id"),
        received_date=request.data.get("received_date"),
        delivery_note=request.data.get("delivery_note", ""),
        received_by=request.user_id,
    )
    for line_data in request.data.get("lines", []):
        po_line = PurchaseOrderLine.objects.get(pk=line_data["po_line"], order=po)
        GoodsReceiptLine.objects.create(
            receipt=grn,
            po_line=po_line,
            quantity_received=Decimal(str(line_data["quantity_received"])),
            lot_number=line_data.get("lot_number", ""),
            expiry_date=line_data.get("expiry_date"),
            quality_pass=line_data.get("quality_pass", True),
        )
    return Response(GoodsReceiptSerializer(grn).data, status=201)


@api_view(["POST"])
def validate_grn(request, pk):
    """Validate GRN — update PO received qty and push to Inventory."""
    corporate_id = request.corporate_id
    try:
        grn = GoodsReceipt.objects.get(pk=pk, corporate_id=corporate_id, state="draft")
    except GoodsReceipt.DoesNotExist:
        return Response({"error": "Not found or already validated"}, status=404)

    for line in grn.lines.all():
        # Update PO line received qty
        po_line = line.po_line
        po_line.received_qty += line.quantity_received
        po_line.save()

        # Push stock receipt to Inventory service
        try:
            inventory_client.create_stock_move({
                "corporate_id": str(corporate_id),
                "reference": grn.reference,
                "move_type": "receipt",
                "product_id": str(po_line.product_id),
                "quantity": str(line.quantity_received),
                "location_to_id": str(grn.location_id) if grn.location_id else None,
                "state": "done",
            })
        except Exception as e:
            logger.warning("Could not push stock receipt to Inventory: %s", e)

    # Update PO state
    po = grn.purchase_order
    all_received = all(l.received_qty >= l.quantity for l in po.lines.all())
    po.state = "received" if all_received else "partial"
    po.save()

    grn.state = "validated"
    grn.validated_at = timezone.now()
    grn.save()
    return Response(GoodsReceiptSerializer(grn).data)


# ─── Supplier Bills ──────────────────────────────────────────────────────────

@api_view(["GET", "POST"])
def bill_list_create(request):
    corporate_id = request.corporate_id
    if request.method == "GET":
        qs = SupplierBill.objects.filter(corporate_id=corporate_id).select_related("supplier")
        state = request.GET.get("state")
        if state:
            qs = qs.filter(state=state)
        return Response(SupplierBillSerializer(qs, many=True).data)

    bill_number = _ref("BILL")
    supplier_id = request.data.get("supplier")
    try:
        supplier = Supplier.objects.get(pk=supplier_id, corporate_id=corporate_id)
    except Supplier.DoesNotExist:
        return Response({"error": "Supplier not found"}, status=400)

    s = SupplierBillSerializer(data={
        **request.data, "bill_number": bill_number, "corporate_id": str(corporate_id)
    })
    if s.is_valid():
        bill = s.save(corporate_id=corporate_id, bill_number=bill_number, supplier=supplier)
        return Response(SupplierBillSerializer(bill).data, status=201)
    return Response(s.errors, status=400)


@api_view(["GET", "PATCH"])
def bill_detail(request, pk):
    corporate_id = request.corporate_id
    try:
        bill = SupplierBill.objects.get(pk=pk, corporate_id=corporate_id)
    except SupplierBill.DoesNotExist:
        return Response({"error": "Not found"}, status=404)
    if request.method == "GET":
        return Response(SupplierBillSerializer(bill).data)
    s = SupplierBillSerializer(bill, data=request.data, partial=True)
    if s.is_valid():
        s.save()
        return Response(s.data)
    return Response(s.errors, status=400)
