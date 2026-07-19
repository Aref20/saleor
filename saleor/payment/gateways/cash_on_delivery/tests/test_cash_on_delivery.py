from decimal import Decimal

import pytest

from .....plugins.manager import get_plugins_manager
from .... import ChargeStatus, TransactionKind, gateway
from ..plugin import CashOnDeliveryGatewayPlugin


@pytest.fixture(autouse=True)
def setup_cod_gateway(settings):
    settings.PLUGINS = [
        "saleor.payment.gateways.cash_on_delivery.plugin.CashOnDeliveryGatewayPlugin"
    ]
    return settings


def _as_cod_payment(payment):
    """Route a payment fixture through the COD gateway plugin."""
    payment.gateway = CashOnDeliveryGatewayPlugin.PLUGIN_ID
    payment.save(update_fields=["gateway"])
    return payment


@pytest.fixture
def cod_payment(payment_dummy):
    return _as_cod_payment(payment_dummy)


@pytest.fixture
def cod_payment_txn_preauth(payment_txn_preauth):
    return _as_cod_payment(payment_txn_preauth)


@pytest.fixture
def cod_payment_txn_captured(payment_txn_captured):
    return _as_cod_payment(payment_txn_captured)


def test_authorize_success(cod_payment):
    txn = gateway.authorize(
        payment=cod_payment,
        token="COD",
        manager=get_plugins_manager(allow_replica=False),
        channel_slug=cod_payment.order.channel.slug,
    )
    assert txn.is_success
    assert txn.kind == TransactionKind.AUTH
    assert txn.payment == cod_payment
    cod_payment.refresh_from_db()
    assert cod_payment.is_active


def test_void_success(cod_payment_txn_preauth):
    assert cod_payment_txn_preauth.is_active
    assert cod_payment_txn_preauth.charge_status == ChargeStatus.NOT_CHARGED
    txn = gateway.void(
        payment=cod_payment_txn_preauth,
        manager=get_plugins_manager(allow_replica=False),
        channel_slug=cod_payment_txn_preauth.order.channel.slug,
    )
    assert txn.is_success
    assert txn.kind == TransactionKind.VOID
    assert txn.payment == cod_payment_txn_preauth
    cod_payment_txn_preauth.refresh_from_db()
    assert not cod_payment_txn_preauth.is_active
    assert cod_payment_txn_preauth.charge_status == ChargeStatus.NOT_CHARGED


@pytest.mark.parametrize(
    ("amount", "charge_status"),
    [("98.40", ChargeStatus.FULLY_CHARGED), (70, ChargeStatus.PARTIALLY_CHARGED)],
)
def test_capture_success(amount, charge_status, cod_payment_txn_preauth):
    txn = gateway.capture(
        payment=cod_payment_txn_preauth,
        manager=get_plugins_manager(allow_replica=False),
        amount=Decimal(amount),
        channel_slug=cod_payment_txn_preauth.order.channel.slug,
    )
    assert txn.is_success
    assert txn.payment == cod_payment_txn_preauth
    cod_payment_txn_preauth.refresh_from_db()
    assert cod_payment_txn_preauth.charge_status == charge_status
    assert cod_payment_txn_preauth.is_active


@pytest.mark.parametrize(
    (
        "initial_captured_amount",
        "refund_amount",
        "final_captured_amount",
        "final_charge_status",
        "active_after",
    ),
    [
        (80, 80, 0, ChargeStatus.FULLY_REFUNDED, False),
        (80, 10, 70, ChargeStatus.PARTIALLY_REFUNDED, True),
    ],
)
def test_refund_success(
    initial_captured_amount,
    refund_amount,
    final_captured_amount,
    final_charge_status,
    active_after,
    cod_payment_txn_captured,
):
    payment = cod_payment_txn_captured
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = initial_captured_amount
    payment.save()
    txn = gateway.refund(
        payment=payment,
        manager=get_plugins_manager(allow_replica=False),
        amount=Decimal(refund_amount),
        channel_slug=payment.order.channel.slug,
    )

    payment.refresh_from_db()
    assert txn.kind == TransactionKind.REFUND
    assert txn.is_success
    assert txn.payment == payment
    assert payment.charge_status == final_charge_status
    assert payment.captured_amount == final_captured_amount
    assert payment.is_active == active_after
