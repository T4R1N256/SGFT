"""URL routes for apps.pos. Each package adds its views here; names describe the action."""
from django.urls import path

from . import views

app_name = "pos"
urlpatterns = [
    path("", views.order_builder, name="order_builder"),
    path("dishes/", views.dish_list, name="dish_list"),
    path("dishes/<int:dish_id>/add/", views.add_item, name="add_item"),
    path("dishes/<int:dish_id>/remove/", views.remove_dish, name="remove_dish"),
    path("items/<int:line_id>/remove/", views.remove_item, name="remove_item"),
    path("order/payment-method/", views.set_payment_method, name="set_payment_method"),
    path("order/confirm/", views.confirm_sale, name="confirm_sale"),
    path("cash-session/open/", views.open_session, name="open_session"),
    path("cash-session/close/", views.close_session, name="close_session"),
    # path("sync/", views_sync.sync_operations, name="sync_operations"),  # views_sync.py pending (Jesús + Jared)
]
