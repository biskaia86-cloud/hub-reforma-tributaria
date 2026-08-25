"""Integração do checkout Mercado Pago.

Em produção, o ideal é configurar também um Webhook (Mercado Pago Webhooks v2)
em um endpoint dedicado que chame confirm_payment quando o status mudar. Esta
versão inicial confirma no retorno do usuário ao app, sem infraestrutura extra.
"""

from __future__ import annotations

import os

import mercadopago

import database


PRODUCT_NAME = "Rota Simples - Enquadramento completo"
PRODUCT_PRICE = 97.00
PRODUCT_ACCESS_DAYS = 30


def _sdk() -> mercadopago.SDK:
    token = os.getenv("MERCADOPAGO_ACCESS_TOKEN", "").strip()
    if not token:
        raise RuntimeError("MERCADOPAGO_ACCESS_TOKEN não configurado.")
    return mercadopago.SDK(token)


def create_checkout_preference(email: str, lead_id: int) -> dict:
    app_url = os.getenv("APP_URL", "http://localhost:8501").rstrip("/")
    preference = {
        "items": [{"title": PRODUCT_NAME, "quantity": 1, "unit_price": PRODUCT_PRICE, "currency_id": "BRL"}],
        "payer": {"email": email},
        "external_reference": str(lead_id),
        "back_urls": {
            "success": f"{app_url}/?payment_id={{payment_id}}&status={{status}}",
            "failure": f"{app_url}/?status=failure",
            "pending": f"{app_url}/?payment_id={{payment_id}}&status=pending",
        },
        "auto_return": "approved",
    }
    response = _sdk().preference().create(preference)
    result = response.get("response", response)
    preference_id = result.get("id")
    checkout_url = result.get("init_point") or result.get("sandbox_init_point")
    if not preference_id or not checkout_url:
        raise RuntimeError("O Mercado Pago não retornou um checkout válido.")
    database.create_pending_access(email, preference_id, round(PRODUCT_PRICE * 100), lead_id)
    return {"checkout_url": checkout_url, "preference_id": preference_id}


def confirm_payment(payment_id: str) -> str:
    response = _sdk().payment().get(str(payment_id))
    payment = response.get("response", response)
    status = str(payment.get("status", "unknown"))
    if status == "approved":
        approved = database.approve_access(str(payment_id), days_valid=PRODUCT_ACCESS_DAYS)
        if not approved:
            payer_email = payment.get("payer", {}).get("email")
            amount = round(float(payment.get("transaction_amount", PRODUCT_PRICE)) * 100)
            if payer_email:
                database.create_pending_access(payer_email, str(payment_id), amount)
                database.approve_access(str(payment_id), days_valid=PRODUCT_ACCESS_DAYS)
    return status