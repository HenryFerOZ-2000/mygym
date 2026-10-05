from uuid import uuid4


def test_partial_multi_charge_payment_and_refund(gym_case):
    api, _, _, url, _, _, _, enroll = gym_case
    enroll()
    enroll()
    charges = api.get(url + "receivables/").json()["results"]
    payload = {
        "request_id": str(uuid4()),
        "amount": "40.00",
        "currency": "USD",
        "method": "CASH",
        "allocations": [
            {"charge_id": charges[0]["id"], "amount": "30.00"},
            {"charge_id": charges[1]["id"], "amount": "10.00"},
        ],
    }
    payment = api.post(url + "receivables/payments/", payload, format="json")
    assert payment.status_code == 201, payment.content
    assert (
        api.post(url + "receivables/payments/", payload, format="json").json()["id"]
        == payment.json()["id"]
    )
    balances = api.get(url + "receivables/").json()["results"]
    assert [c["balance"] for c in balances] == ["0.00", "20.00"]
    refund_url = url + "receivables/payments/" + payment.json()["id"] + "/refunds/"
    refund = {
        "request_id": str(uuid4()),
        "reason": "Devolución externa realizada",
        "allocations": [{"charge_id": charges[0]["id"], "amount": "12.00"}],
    }
    response = api.post(refund_url, refund, format="json")
    assert response.status_code == 201, response.content
    assert (
        api.post(refund_url, refund, format="json").json()["id"]
        == response.json()["id"]
    )
    assert api.get(url + "receivables/").json()["results"][0]["balance"] == "12.00"
    excessive = {
        **refund,
        "request_id": str(uuid4()),
        "allocations": [{"charge_id": charges[0]["id"], "amount": "19.00"}],
    }
    assert api.post(refund_url, excessive, format="json").status_code == 400
    assert (
        api.post(
            url + "receivables/payments/",
            {**payload, "request_id": str(uuid4())},
            format="json",
        ).status_code
        == 400
    )
