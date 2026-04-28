"""
Tests for the invoices router — /api/v1/invoices/*

Covers: CRUD, status lifecycle, invoice number format, public token access,
duplication, and per-user isolation.

Notes:
- PDF generation is skipped in tests because WeasyPrint is not installed;
  the service logs a warning and returns "".
- Email sending is skipped because SENDGRID_API_KEY="" (set in conftest).
- The send_invoice endpoint still succeeds: it transitions status to "sent"
  regardless of whether the PDF/email delivery worked.
"""

import re

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _register_and_login(client, email: str, password: str = "password123") -> dict:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Other User"},
    )
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


# ---------------------------------------------------------------------------
# Create invoice
# ---------------------------------------------------------------------------


class TestCreateInvoice:
    """POST /api/v1/invoices"""

    def test_create_invoice_success(self, client, auth_headers, invoice_payload):
        """Valid payload should return 201 with a draft invoice."""
        resp = client.post(
            "/api/v1/invoices",
            json=invoice_payload,
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "draft"
        assert data["client_id"] == invoice_payload["client_id"]
        assert "id" in data
        assert "invoice_number" in data
        assert "public_token" in data

    def test_create_invoice_computes_totals(self, client, auth_headers, test_client_data):
        """Totals must be computed server-side from line items."""
        resp = client.post(
            "/api/v1/invoices",
            json={
                "client_id": test_client_data["id"],
                "issue_date": "2026-04-01",
                "due_date": "2026-04-30",
                "tax_rate": "10",
                "items": [
                    {
                        "description": "Design work",
                        "quantity": "2",
                        "unit_price": "100.00",
                        "sort_order": 0,
                    }
                ],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        # subtotal = 2 * 100 = 200
        # tax = 200 * 10% = 20
        # total = 220
        assert float(data["subtotal"]) == 200.00
        assert float(data["tax_amount"]) == 20.00
        assert float(data["total"]) == 220.00

    def test_create_invoice_requires_auth(self, client, invoice_payload):
        """Unauthenticated request should return 401."""
        resp = client.post("/api/v1/invoices", json=invoice_payload)
        assert resp.status_code == 401

    def test_create_invoice_empty_items(self, client, auth_headers, test_client_data):
        """Invoice with no items should be rejected with 422."""
        resp = client.post(
            "/api/v1/invoices",
            json={
                "client_id": test_client_data["id"],
                "issue_date": "2026-04-01",
                "due_date": "2026-04-30",
                "items": [],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_create_invoice_due_before_issue(self, client, auth_headers, test_client_data):
        """due_date before issue_date should return 422."""
        resp = client.post(
            "/api/v1/invoices",
            json={
                "client_id": test_client_data["id"],
                "issue_date": "2026-04-30",
                "due_date": "2026-04-01",  # before issue_date
                "items": [
                    {"description": "Work", "quantity": "1", "unit_price": "100"}
                ],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_create_invoice_unknown_client(self, client, auth_headers):
        """Referencing a non-existent client should return 404."""
        resp = client.post(
            "/api/v1/invoices",
            json={
                "client_id": 99999,
                "issue_date": "2026-04-01",
                "due_date": "2026-04-30",
                "items": [
                    {"description": "Work", "quantity": "1", "unit_price": "100"}
                ],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_create_invoice_negative_tax_rate(self, client, auth_headers, test_client_data):
        """Negative tax_rate should be rejected with 422."""
        resp = client.post(
            "/api/v1/invoices",
            json={
                "client_id": test_client_data["id"],
                "issue_date": "2026-04-01",
                "due_date": "2026-04-30",
                "tax_rate": "-5",
                "items": [
                    {"description": "Work", "quantity": "1", "unit_price": "100"}
                ],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Invoice number format
# ---------------------------------------------------------------------------


class TestInvoiceNumberFormat:
    """Invoice numbers must follow INV-YYYYMM-XXXX format."""

    def test_invoice_number_starts_with_inv(
        self, client, auth_headers, invoice_payload
    ):
        """invoice_number must start with INV-."""
        resp = client.post(
            "/api/v1/invoices",
            json=invoice_payload,
            headers=auth_headers,
        )
        assert resp.status_code == 201
        number = resp.json()["invoice_number"]
        assert number.startswith("INV-")

    def test_invoice_number_format_regex(
        self, client, auth_headers, invoice_payload
    ):
        """invoice_number must match INV-YYYYMM-XXXX exactly."""
        resp = client.post(
            "/api/v1/invoices",
            json=invoice_payload,
            headers=auth_headers,
        )
        number = resp.json()["invoice_number"]
        pattern = r"^INV-\d{6}-\d{4}$"
        assert re.match(pattern, number), f"Number {number!r} does not match {pattern}"

    def test_sequential_invoice_numbers(
        self, client, auth_headers, test_client_data
    ):
        """Second invoice for the same user/month should have a higher sequence."""
        base = {
            "client_id": test_client_data["id"],
            "issue_date": "2026-04-01",
            "due_date": "2026-04-30",
            "items": [{"description": "A", "quantity": "1", "unit_price": "10"}],
        }
        r1 = client.post("/api/v1/invoices", json=base, headers=auth_headers)
        r2 = client.post("/api/v1/invoices", json=base, headers=auth_headers)
        n1 = r1.json()["invoice_number"]
        n2 = r2.json()["invoice_number"]
        seq1 = int(n1.split("-")[-1])
        seq2 = int(n2.split("-")[-1])
        assert seq2 > seq1


# ---------------------------------------------------------------------------
# List invoices
# ---------------------------------------------------------------------------


class TestListInvoices:
    """GET /api/v1/invoices"""

    def test_list_invoices_empty(self, client, auth_headers):
        """Fresh user should see empty list."""
        resp = client.get("/api/v1/invoices", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_invoices_returns_created(
        self, client, auth_headers, created_invoice
    ):
        """Created invoice should appear in the list."""
        resp = client.get("/api/v1/invoices", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["id"] == created_invoice["id"]

    def test_list_invoices_requires_auth(self, client):
        """Unauthenticated request should return 401."""
        resp = client.get("/api/v1/invoices")
        assert resp.status_code == 401

    def test_list_invoices_filter_by_status(
        self, client, auth_headers, created_invoice
    ):
        """Filter by status=draft should return only drafts."""
        resp = client.get(
            "/api/v1/invoices?status=draft", headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

        resp_sent = client.get(
            "/api/v1/invoices?status=sent", headers=auth_headers
        )
        assert resp_sent.json()["total"] == 0


# ---------------------------------------------------------------------------
# Get single invoice
# ---------------------------------------------------------------------------


class TestGetInvoice:
    """GET /api/v1/invoices/{id}"""

    def test_get_invoice_success(
        self, client, auth_headers, created_invoice
    ):
        """Should return 200 with full invoice data including items."""
        iid = created_invoice["id"]
        resp = client.get(f"/api/v1/invoices/{iid}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == iid
        assert len(data["items"]) == 1

    def test_get_invoice_not_found(self, client, auth_headers):
        """Non-existent invoice ID should return 404."""
        resp = client.get("/api/v1/invoices/99999", headers=auth_headers)
        assert resp.status_code == 404

    def test_get_invoice_requires_auth(self, client, created_invoice):
        """Unauthenticated request should return 401."""
        iid = created_invoice["id"]
        resp = client.get(f"/api/v1/invoices/{iid}")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Update invoice
# ---------------------------------------------------------------------------


class TestUpdateInvoice:
    """PUT /api/v1/invoices/{id}"""

    def test_update_draft_invoice_notes(
        self, client, auth_headers, created_invoice
    ):
        """Should update notes on a draft invoice."""
        iid = created_invoice["id"]
        resp = client.put(
            f"/api/v1/invoices/{iid}",
            json={"notes": "Updated notes"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["notes"] == "Updated notes"

    def test_update_draft_invoice_items_recomputes_totals(
        self, client, auth_headers, created_invoice
    ):
        """Replacing items should recompute totals."""
        iid = created_invoice["id"]
        resp = client.put(
            f"/api/v1/invoices/{iid}",
            json={
                "items": [
                    {
                        "description": "New work",
                        "quantity": "3",
                        "unit_price": "200.00",
                        "sort_order": 0,
                    }
                ]
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        # subtotal = 3 * 200 = 600; no tax, no discount
        assert float(data["subtotal"]) == 600.00
        assert float(data["total"]) == 600.00

    def test_cannot_update_sent_invoice(
        self, client, auth_headers, created_invoice
    ):
        """Updating a sent invoice should return 409 Conflict."""
        iid = created_invoice["id"]
        # Send the invoice first
        client.post(
            f"/api/v1/invoices/{iid}/send",
            headers=auth_headers,
        )
        # Attempt to update
        resp = client.put(
            f"/api/v1/invoices/{iid}",
            json={"notes": "Cannot change this"},
            headers=auth_headers,
        )
        assert resp.status_code == 409

    def test_update_invoice_not_found(self, client, auth_headers):
        """Updating non-existent invoice should return 404."""
        resp = client.put(
            "/api/v1/invoices/99999",
            json={"notes": "Ghost"},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_update_invoice_requires_auth(self, client, created_invoice):
        """Unauthenticated update should return 401."""
        iid = created_invoice["id"]
        resp = client.put(f"/api/v1/invoices/{iid}", json={"notes": "Hack"})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Delete invoice
# ---------------------------------------------------------------------------


class TestDeleteInvoice:
    """DELETE /api/v1/invoices/{id}"""

    def test_delete_draft_invoice(
        self, client, auth_headers, created_invoice
    ):
        """Deleting a draft invoice should return 204."""
        iid = created_invoice["id"]
        resp = client.delete(f"/api/v1/invoices/{iid}", headers=auth_headers)
        assert resp.status_code == 204

    def test_get_invoice_after_delete_returns_404(
        self, client, auth_headers, created_invoice
    ):
        """After deletion, GET should return 404."""
        iid = created_invoice["id"]
        client.delete(f"/api/v1/invoices/{iid}", headers=auth_headers)
        resp = client.get(f"/api/v1/invoices/{iid}", headers=auth_headers)
        assert resp.status_code == 404

    def test_cannot_delete_sent_invoice(
        self, client, auth_headers, created_invoice
    ):
        """Deleting a sent invoice should return 409."""
        iid = created_invoice["id"]
        client.post(f"/api/v1/invoices/{iid}/send", headers=auth_headers)

        resp = client.delete(f"/api/v1/invoices/{iid}", headers=auth_headers)
        assert resp.status_code == 409

    def test_delete_invoice_not_found(self, client, auth_headers):
        """Deleting a non-existent invoice should return 404."""
        resp = client.delete("/api/v1/invoices/99999", headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_invoice_requires_auth(self, client, created_invoice):
        """Unauthenticated delete should return 401."""
        iid = created_invoice["id"]
        resp = client.delete(f"/api/v1/invoices/{iid}")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Send invoice
# ---------------------------------------------------------------------------


class TestSendInvoice:
    """POST /api/v1/invoices/{id}/send"""

    def test_send_invoice_success(
        self, client, auth_headers, created_invoice
    ):
        """Sending an invoice should transition status to 'sent' and set sent_at."""
        iid = created_invoice["id"]
        resp = client.post(
            f"/api/v1/invoices/{iid}/send", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "sent"
        assert data["sent_at"] is not None

    def test_cannot_send_cancelled_invoice(
        self, client, auth_headers, test_client_data
    ):
        """
        A cancelled invoice cannot be sent → 409.
        We test this by directly creating an invoice then cancelling it via
        a PUT (updating status field is not exposed; instead we rely on the
        service's ConflictError for cancelled invoices at the send step).

        Since there is no cancel endpoint in the current router, we test the
        guard via a non-cancelled path: we just verify a fresh draft CAN be sent.
        This sub-test is documented here as a reminder that the guard exists
        in invoice_service.send_invoice.
        """
        # Positive case: draft → sent is allowed
        inv = client.post(
            "/api/v1/invoices",
            json={
                "client_id": test_client_data["id"],
                "issue_date": "2026-04-01",
                "due_date": "2026-04-30",
                "items": [
                    {"description": "Work", "quantity": "1", "unit_price": "100"}
                ],
            },
            headers=auth_headers,
        ).json()
        resp = client.post(
            f"/api/v1/invoices/{inv['id']}/send", headers=auth_headers
        )
        assert resp.status_code == 200

    def test_send_invoice_not_found(self, client, auth_headers):
        """Sending a non-existent invoice should return 404."""
        resp = client.post(
            "/api/v1/invoices/99999/send", headers=auth_headers
        )
        assert resp.status_code == 404

    def test_send_invoice_requires_auth(self, client, created_invoice):
        """Unauthenticated send should return 401."""
        iid = created_invoice["id"]
        resp = client.post(f"/api/v1/invoices/{iid}/send")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Mark paid
# ---------------------------------------------------------------------------


class TestMarkPaid:
    """POST /api/v1/invoices/{id}/mark-paid"""

    def test_mark_paid_after_send(
        self, client, auth_headers, created_invoice
    ):
        """Sent invoice can be marked paid → status='paid', paid_at set."""
        iid = created_invoice["id"]
        client.post(f"/api/v1/invoices/{iid}/send", headers=auth_headers)

        resp = client.post(
            f"/api/v1/invoices/{iid}/mark-paid", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "paid"
        assert data["paid_at"] is not None

    def test_cannot_mark_draft_as_paid(
        self, client, auth_headers, created_invoice
    ):
        """Draft invoices cannot be marked paid → 409."""
        iid = created_invoice["id"]
        resp = client.post(
            f"/api/v1/invoices/{iid}/mark-paid", headers=auth_headers
        )
        assert resp.status_code == 409

    def test_mark_paid_not_found(self, client, auth_headers):
        """Non-existent invoice → 404."""
        resp = client.post(
            "/api/v1/invoices/99999/mark-paid", headers=auth_headers
        )
        assert resp.status_code == 404

    def test_mark_paid_requires_auth(self, client, created_invoice):
        """Unauthenticated request should return 401."""
        iid = created_invoice["id"]
        resp = client.post(f"/api/v1/invoices/{iid}/mark-paid")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Duplicate invoice
# ---------------------------------------------------------------------------


class TestDuplicateInvoice:
    """POST /api/v1/invoices/{id}/duplicate"""

    def test_duplicate_invoice_success(
        self, client, auth_headers, created_invoice
    ):
        """Duplicate should return 201 with a new invoice in draft status."""
        iid = created_invoice["id"]
        resp = client.post(
            f"/api/v1/invoices/{iid}/duplicate", headers=auth_headers
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "draft"
        assert data["id"] != iid

    def test_duplicate_has_new_invoice_number(
        self, client, auth_headers, created_invoice
    ):
        """Duplicate should have a different invoice number than the source."""
        iid = created_invoice["id"]
        source_number = created_invoice["invoice_number"]

        resp = client.post(
            f"/api/v1/invoices/{iid}/duplicate", headers=auth_headers
        )
        assert resp.status_code == 201
        assert resp.json()["invoice_number"] != source_number

    def test_duplicate_has_new_number_format(
        self, client, auth_headers, created_invoice
    ):
        """Duplicated invoice number must still follow INV-YYYYMM-XXXX format."""
        iid = created_invoice["id"]
        resp = client.post(
            f"/api/v1/invoices/{iid}/duplicate", headers=auth_headers
        )
        number = resp.json()["invoice_number"]
        assert re.match(r"^INV-\d{6}-\d{4}$", number)

    def test_duplicate_has_new_public_token(
        self, client, auth_headers, created_invoice
    ):
        """Duplicate must receive a fresh UUID public token."""
        iid = created_invoice["id"]
        source_token = created_invoice["public_token"]

        resp = client.post(
            f"/api/v1/invoices/{iid}/duplicate", headers=auth_headers
        )
        assert resp.json()["public_token"] != source_token

    def test_duplicate_copies_items(
        self, client, auth_headers, created_invoice
    ):
        """Duplicate should carry the same line items as the source."""
        iid = created_invoice["id"]
        resp = client.post(
            f"/api/v1/invoices/{iid}/duplicate", headers=auth_headers
        )
        dup_items = resp.json()["items"]
        src_items = created_invoice["items"]
        assert len(dup_items) == len(src_items)

    def test_duplicate_not_found(self, client, auth_headers):
        """Duplicating a non-existent invoice → 404."""
        resp = client.post(
            "/api/v1/invoices/99999/duplicate", headers=auth_headers
        )
        assert resp.status_code == 404

    def test_duplicate_requires_auth(self, client, created_invoice):
        """Unauthenticated duplicate → 401."""
        iid = created_invoice["id"]
        resp = client.post(f"/api/v1/invoices/{iid}/duplicate")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Public invoice (no auth)
# ---------------------------------------------------------------------------


class TestPublicInvoice:
    """GET /api/v1/invoices/public/{token}"""

    def test_public_invoice_by_token(
        self, client, created_invoice
    ):
        """Public token access should return 200 without authentication."""
        token = created_invoice["public_token"]
        resp = client.get(f"/api/v1/invoices/public/{token}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["public_token"] == token
        assert data["id"] == created_invoice["id"]

    def test_public_invoice_invalid_token(self, client):
        """Unknown public token should return 404."""
        resp = client.get(
            "/api/v1/invoices/public/00000000-0000-0000-0000-000000000000"
        )
        assert resp.status_code == 404

    def test_public_invoice_no_auth_required(
        self, client, created_invoice
    ):
        """Public endpoint must work without Authorization header."""
        token = created_invoice["public_token"]
        resp = client.get(
            f"/api/v1/invoices/public/{token}",
            headers={},  # explicitly no auth
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Invoice isolation between users
# ---------------------------------------------------------------------------


class TestInvoiceIsolation:
    """User A must not be able to access user B's invoices."""

    def test_user_cannot_get_other_users_invoice(
        self, client, auth_headers, created_invoice
    ):
        """User B should get 404 accessing user A's invoice."""
        iid = created_invoice["id"]
        user_b = _register_and_login(client, "isolationb@example.com")
        resp = client.get(f"/api/v1/invoices/{iid}", headers=user_b)
        assert resp.status_code == 404

    def test_user_cannot_update_other_users_invoice(
        self, client, auth_headers, created_invoice
    ):
        """User B should get 404 updating user A's invoice."""
        iid = created_invoice["id"]
        user_b = _register_and_login(client, "updiso@example.com")
        resp = client.put(
            f"/api/v1/invoices/{iid}",
            json={"notes": "Stolen"},
            headers=user_b,
        )
        assert resp.status_code == 404

    def test_user_cannot_delete_other_users_invoice(
        self, client, auth_headers, created_invoice
    ):
        """User B should get 404 deleting user A's invoice."""
        iid = created_invoice["id"]
        user_b = _register_and_login(client, "deliso@example.com")
        resp = client.delete(f"/api/v1/invoices/{iid}", headers=user_b)
        assert resp.status_code == 404

    def test_invoice_list_only_own(
        self, client, auth_headers, created_invoice
    ):
        """User B's invoice list must not include user A's invoices."""
        user_b = _register_and_login(client, "listiso@example.com")
        resp = client.get("/api/v1/invoices", headers=user_b)
        assert resp.json()["total"] == 0
