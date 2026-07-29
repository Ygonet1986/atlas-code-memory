"""Invoice generation and billing totals."""

def make_invoice(user_id: str, amount: float) -> dict:
    return {"user_id": user_id, "amount": amount, "currency": "USD"}
