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
)

urlpatterns = [
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
    path("promotions/", promotion_list_create),
    path("loyalty/programs/", loyalty_program_list_create),
    path("loyalty/cards/lookup/", loyalty_card_lookup),
]
