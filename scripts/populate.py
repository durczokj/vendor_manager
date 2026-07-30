r"""API-based sample data loader and end-to-end smoke script.

Usage
-----
    python scripts/populate.py \\
        --base-url http://localhost:8000 \\
        --user admin --password admin \\
        --reset --seed 42

This script exercises every ``/api/v1/…`` endpoint that the vendor_manager
application exposes for the covered entities.  It creates:

- 2 ``CostCenter``
- 6 ``Undertaking`` (one per manager ``Person``)
- 6 manager ``Person`` objects
- 3 ``Company``
- 3 ``Contract``
- 3 ``Order`` (one per company) + 3 initial ``OrderVersion`` objects
- 30 consultant ``Person`` objects
- 30 ``Engagement`` objects (one per consultant)
- 30 ``EngagementOrderVersionAssignment`` objects
- ≥ 30 ``EngagementUndertakingAssignment`` objects
- 3 ``Leave`` objects
- 2 cloned ``OrderVersion`` objects (via ``POST /api/v1/orders/{id}/versions/clone-latest/``)

Covered endpoints (FR-29 – FR-35, NFR-16)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- ``GET  /api/v1/cost-centers/``
- ``POST /api/v1/cost-centers/``
- ``GET  /api/v1/undertakings/``
- ``POST /api/v1/undertakings/``
- ``GET  /api/v1/people/``
- ``POST /api/v1/people/``
- ``GET  /api/v1/companies/``
- ``POST /api/v1/companies/``
- ``GET  /api/v1/contracts/``
- ``POST /api/v1/contracts/``
- ``GET  /api/v1/orders/``
- ``POST /api/v1/orders/``
- ``GET  /api/v1/order-versions/``
- ``POST /api/v1/order-versions/``
- ``POST /api/v1/orders/{id}/versions/clone-latest/``
- ``GET  /api/v1/engagements/``
- ``POST /api/v1/engagements/``
- ``POST /api/v1/engagement-order-version-assignments/``
- ``POST /api/v1/engagement-undertaking-assignments/``
- ``GET  /api/v1/leaves/``
- ``POST /api/v1/leaves/``
- ``DELETE`` on every resource type (when ``--reset`` is used)
"""

from __future__ import annotations

import argparse
import random
import sys
import time
from typing import Any

import requests
from faker import Faker

# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------


def _api(
    session: requests.Session,
    method: str,
    url: str,
    **kwargs: Any,
) -> Any:
    """Execute an HTTP request and raise loudly on any non-2xx response.

    Args:
        session: An authenticated ``requests.Session``.
        method: HTTP verb (``GET``, ``POST``, ``DELETE``, …).
        url: Full URL to call.
        **kwargs: Forwarded to ``session.request``.

    Returns:
        Parsed JSON body when the response contains one; otherwise an empty
        dict.

    Raises:
        SystemExit: Immediately on any non-2xx status.  Prints the endpoint,
            request body, and response body before exiting so the caller has
            full context.

    """
    body = kwargs.get("json")
    resp = session.request(method, url, **kwargs)
    if not resp.ok:
        print(
            f"\n[ERROR] {method} {url}",
            f"  Request : {body}",
            f"  Response: {resp.status_code} {resp.text}",
            sep="\n",
        )
        sys.exit(1)
    try:
        return resp.json()
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Reset helpers
# ---------------------------------------------------------------------------


def _delete_all(session: requests.Session, base: str, endpoint: str) -> int:
    """List and delete every resource at *endpoint*.

    Deletion is attempted in reverse-ID order so that child records are
    removed before parents where the ordering matters.

    Args:
        session: Authenticated session.
        base: Base URL (e.g. ``http://localhost:8000``).
        endpoint: Relative path (e.g. ``/api/v1/people/``).

    Returns:
        Number of resources deleted.

    """
    url = f"{base}{endpoint}"
    deleted = 0
    # Collect all pages.
    items: list[dict[str, Any]] = []
    page_url: str | None = url
    while page_url:
        data = _api(session, "GET", page_url)
        if isinstance(data, dict) and "results" in data:
            items.extend(data["results"])
            page_url = data.get("next")
        else:
            # Non-paginated response.
            items.extend(data if isinstance(data, list) else [])
            page_url = None
    for item in reversed(items):
        _api(session, "DELETE", f"{url}{item['id']}/")
        deleted += 1
    return deleted


def reset_all(session: requests.Session, base: str) -> None:
    """Delete every entity in reverse dependency order.

    Order:
    1. engagement-undertaking-assignments
    2. engagement-order-version-assignments
    3. leaves
    4. engagements
    5. order-versions
    6. orders
    7. contracts
    8. people (consultants — managers deleted last)
    9. undertakings
    10. cost-centers
    11. companies
    12. people (managers — those that remain after undertakings are gone)

    Args:
        session: Authenticated session.
        base: Base URL (e.g. ``http://localhost:8000``).

    """
    print("[reset] Deleting all existing data …")

    # Step 1-2: assignments (both kinds at the flat endpoints)
    _delete_all(session, base, "/api/v1/engagement-undertaking-assignments/")
    _delete_all(session, base, "/api/v1/engagement-order-version-assignments/")

    # Step 3: leaves
    _delete_all(session, base, "/api/v1/leaves/")

    # Step 4: engagements
    _delete_all(session, base, "/api/v1/engagements/")

    # Step 5: order-versions
    _delete_all(session, base, "/api/v1/order-versions/")

    # Step 6: orders
    _delete_all(session, base, "/api/v1/orders/")

    # Step 7: contracts
    _delete_all(session, base, "/api/v1/contracts/")

    # Step 8: all people (managers will fail if undertakings still exist,
    #          so we defer undertaking deletion to step 9 and do a two-pass
    #          approach — first delete non-manager people, then undertakings,
    #          then managers).
    _delete_all(session, base, "/api/v1/people/")

    # Step 9: undertakings (managers already gone in step 8)
    _delete_all(session, base, "/api/v1/undertakings/")

    # Step 10: cost-centers
    _delete_all(session, base, "/api/v1/cost-centers/")

    # Step 11: companies
    _delete_all(session, base, "/api/v1/companies/")

    print("[reset] Done.\n")


# ---------------------------------------------------------------------------
# Population helpers
# ---------------------------------------------------------------------------


def create_cost_centers(
    session: requests.Session,
    base: str,
    rng: random.Random,
) -> list[Any]:
    """Create 2 CostCenter objects.

    Args:
        session: Authenticated session.
        base: Base URL.
        rng: Seeded RNG.

    Returns:
        List of created CostCenter dicts.

    """
    url = f"{base}/api/v1/cost-centers/"
    result = []
    for i in range(1, 3):
        data = {"id": i, "name": f"Cost Center {i}"}
        obj = _api(session, "POST", url, json=data)
        result.append(obj)
    return result


def create_managers(
    session: requests.Session,
    base: str,
    fake: Faker,
) -> list[Any]:
    """Create 6 manager Person objects.

    IDs are ``M-001`` … ``M-006`` (fits CharField max_length=6).

    Args:
        session: Authenticated session.
        base: Base URL.
        fake: Seeded Faker instance.

    Returns:
        List of created Person dicts.

    """
    url = f"{base}/api/v1/people/"
    managers = []
    for i in range(1, 7):
        data = {
            "id": f"M-{i:03d}",
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "description": "Undertaking manager",
            "location": fake.city(),
        }
        obj = _api(session, "POST", url, json=data)
        managers.append(obj)
    return managers


def create_undertakings(
    session: requests.Session,
    base: str,
    cost_centers: list[Any],
    managers: list[Any],
    fake: Faker,
) -> list[Any]:
    """Create 6 Undertaking objects — one per manager.

    Args:
        session: Authenticated session.
        base: Base URL.
        cost_centers: Previously created CostCenter dicts.
        managers: Previously created manager Person dicts.
        fake: Seeded Faker instance.

    Returns:
        List of created Undertaking dicts.

    """
    url = f"{base}/api/v1/undertakings/"
    undertakings = []
    for i, manager in enumerate(managers, start=1):
        cc = cost_centers[(i - 1) % len(cost_centers)]
        data = {
            "id": i,
            "name": f"{fake.bs().title()} Undertaking",
            "cost_center": cc["id"],
            "manager": manager["id"],
        }
        obj = _api(session, "POST", url, json=data)
        undertakings.append(obj)
    return undertakings


def create_companies(
    session: requests.Session,
    base: str,
    fake: Faker,
) -> list[Any]:
    """Create 3 Company objects.

    Args:
        session: Authenticated session.
        base: Base URL.
        fake: Seeded Faker instance.

    Returns:
        List of created Company dicts.

    """
    url = f"{base}/api/v1/companies/"
    companies = []
    for i in range(1, 4):
        data = {
            "id": i,
            "name": f"{fake.company()} Ltd",
            "email": fake.company_email(),
        }
        obj = _api(session, "POST", url, json=data)
        companies.append(obj)
    return companies


def create_contracts(
    session: requests.Session,
    base: str,
    rng: random.Random,
) -> list[Any]:
    """Create 3 Contract objects (initial; more are created via clone-latest).

    Args:
        session: Authenticated session.
        base: Base URL.
        rng: Seeded RNG.

    Returns:
        List of created Contract dicts.

    """
    url = f"{base}/api/v1/contracts/"
    contracts = []
    statuses = ["ACTIVE", "PENDING", "CLOSED"]
    for i in range(1, 4):
        data = {
            "id": i,
            "name": f"Contract {i:03d}",
            "status": statuses[(i - 1) % len(statuses)],
            "size": rng.randint(50_000, 500_000),
        }
        obj = _api(session, "POST", url, json=data)
        contracts.append(obj)
    return contracts


def create_orders_and_versions(
    session: requests.Session,
    base: str,
    companies: list[Any],
    contracts: list[Any],
    rng: random.Random,
) -> tuple[list[Any], list[Any]]:
    """Create 3 Orders each with one initial OrderVersion.

    Args:
        session: Authenticated session.
        base: Base URL.
        companies: Previously created Company dicts.
        contracts: Previously created Contract dicts.
        rng: Seeded RNG.

    Returns:
        A 2-tuple: (orders list, order_versions list).

    """
    orders_url = f"{base}/api/v1/orders/"
    versions_url = f"{base}/api/v1/order-versions/"
    orders = []
    versions = []
    for i, (company, contract) in enumerate(zip(companies, contracts, strict=True), start=1):
        order_data = {"id": i, "name": f"Order {i:03d}", "company": company["id"]}
        order = _api(session, "POST", orders_url, json=order_data)
        orders.append(order)

        year = 2024 + (i - 1)
        ver_data = {
            "order": order["id"],
            "contract": contract["id"],
            "version_number": 1,
            "start_date": f"{year}-01-01",
            "end_date": f"{year}-12-31",
        }
        version = _api(session, "POST", versions_url, json=ver_data)
        versions.append(version)
    return orders, versions


def clone_order_versions(
    session: requests.Session,
    base: str,
    orders: list[Any],
    rng: random.Random,
) -> list[Any]:
    """Clone the latest version for 2 orders (FR-31).

    Creates 2 extra contracts (IDs 4 and 5) to satisfy the OneToOne
    constraint on ``OrderVersion.contract``.

    Args:
        session: Authenticated session.
        base: Base URL.
        orders: All Order dicts (at least 2 required).
        rng: Seeded RNG.

    Returns:
        List of newly created (cloned) OrderVersion dicts.

    """
    contracts_url = f"{base}/api/v1/contracts/"
    clones = []
    clone_orders = orders[:2]  # Clone for first two orders.

    for idx, order in enumerate(clone_orders, start=4):
        # Create a fresh contract for the new version.
        contract_data = {
            "id": idx,
            "name": f"Contract {idx:03d} (clone)",
            "status": "ACTIVE",
            "size": rng.randint(50_000, 500_000),
        }
        contract = _api(session, "POST", contracts_url, json=contract_data)

        # Clone via the custom action.
        clone_url = f"{base}/api/v1/orders/{order['id']}/versions/clone-latest/"
        year = 2026 + (idx - 4)
        payload = {
            "contract_id": contract["id"],
            "start_date": f"{year}-01-01",
            "end_date": f"{year}-12-31",
            "copy_engagement_assignments": True,
        }
        new_version = _api(session, "POST", clone_url, json=payload)
        clones.append(new_version)
    return clones


def create_consultants_with_engagements(
    session: requests.Session,
    base: str,
    order_versions: list[Any],
    undertakings: list[Any],
    fake: Faker,
    rng: random.Random,
) -> tuple[list[Any], list[Any], list[Any], list[Any]]:
    """Create 30 consultant Persons, each with an Engagement plus assignments.

    For every consultant the function creates:
    - 1 ``Engagement``
    - 1 ``EngagementOrderVersionAssignment``
    - 1 ``EngagementUndertakingAssignment``

    Args:
        session: Authenticated session.
        base: Base URL.
        order_versions: Created initial OrderVersion dicts (3 items).
        undertakings: Created Undertaking dicts (6 items).
        fake: Seeded Faker instance.
        rng: Seeded RNG.

    Returns:
        4-tuple: (consultants, engagements,
                  order_version_assignments, undertaking_assignments).

    """
    people_url = f"{base}/api/v1/people/"
    eng_url = f"{base}/api/v1/engagements/"
    ova_url = f"{base}/api/v1/engagement-order-version-assignments/"
    ua_url = f"{base}/api/v1/engagement-undertaking-assignments/"

    consultants: list[Any] = []
    engagements: list[Any] = []
    ova_list: list[Any] = []
    ua_list: list[Any] = []

    for i in range(1, 31):
        # Person.
        person_data = {
            "id": f"P-{i:03d}",
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "description": fake.job(),
            "location": fake.city(),
        }
        person = _api(session, "POST", people_url, json=person_data)
        consultants.append(person)

        # Engagement — one per consultant on one of the 3 order versions.
        ov = order_versions[(i - 1) % len(order_versions)]
        start_year = int(str(ov["start_date"])[:4])
        eng_data = {
            "person": person["id"],
            "start_date": f"{start_year}-01-01",
            "end_date": f"{start_year}-12-31",
            "daily_rate": str(rng.randint(300, 1200)),
            "fte": str(round(rng.choice([0.5, 0.75, 1.0]), 2)),
        }
        engagement = _api(session, "POST", eng_url, json=eng_data)
        engagements.append(engagement)

        # Order-version assignment.
        ova_data = {"engagement": engagement["id"], "order_version": ov["id"]}
        ova = _api(session, "POST", ova_url, json=ova_data)
        ova_list.append(ova)

        # Undertaking assignment.
        ut = undertakings[(i - 1) % len(undertakings)]
        ua_data = {
            "engagement": engagement["id"],
            "undertaking": ut["id"],
            "start_date": f"{start_year}-01-01",
            "end_date": f"{start_year}-12-31",
            "percentage": "1.00",
        }
        ua = _api(session, "POST", ua_url, json=ua_data)
        ua_list.append(ua)

    return consultants, engagements, ova_list, ua_list


def create_leaves(
    session: requests.Session,
    base: str,
    consultants: list[Any],
    rng: random.Random,
) -> list[Any]:
    """Create 3 Leave objects for 3 different consultants.

    Args:
        session: Authenticated session.
        base: Base URL.
        consultants: Created consultant Person dicts.
        rng: Seeded RNG.

    Returns:
        List of created Leave dicts.

    """
    url = f"{base}/api/v1/leaves/"
    leaves = []
    for i in range(3):
        person = consultants[i]
        year = 2024
        leave_data = {
            "person": person["id"],
            "start_date": f"{year}-0{i + 2}-01",
            "end_date": f"{year}-0{i + 2}-15",
            "percentage": "0.50",
        }
        leaf = _api(session, "POST", url, json=leave_data)
        leaves.append(leaf)
    return leaves


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser.

    Returns:
        Configured argument parser.

    """
    p = argparse.ArgumentParser(
        description=(
            "Populate a vendor_manager instance with sample data via the REST API. Doubles as an end-to-end smoke test."
        )
    )
    p.add_argument("--base-url", default="http://localhost:8000", help="Base URL of the running app.")
    p.add_argument("--user", required=True, help="HTTP Basic auth username (staff / superuser).")
    p.add_argument("--password", required=True, help="HTTP Basic auth password.")
    p.add_argument(
        "--reset",
        action="store_true",
        default=False,
        help="Delete all existing data before populating (reverse dependency order).",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Integer seed for deterministic random data generation.",
    )
    return p


def main() -> None:
    """Run the population script.

    Raises:
        SystemExit: On any API error or non-zero exit condition.

    """
    args = build_parser().parse_args()

    # Deterministic randomness.
    rng = random.Random(args.seed)
    fake = Faker()
    Faker.seed(args.seed)

    # Authenticated session — HTTP Basic only; no CSRF handling needed.
    session = requests.Session()
    session.auth = (args.user, args.password)

    # Smoke-test the health endpoint first.
    health_url = f"{args.base_url}/health/"
    health = session.get(health_url)
    if not health.ok:
        print(f"[ERROR] Health check failed: {health.status_code} {health.text}")
        sys.exit(1)

    t0 = time.time()

    if args.reset:
        reset_all(session, args.base_url)

    # ---- Create entities -----------------------------------------------
    print("[populate] Creating cost centers …")
    cost_centers = create_cost_centers(session, args.base_url, rng)

    print("[populate] Creating manager persons …")
    managers = create_managers(session, args.base_url, fake)

    print("[populate] Creating undertakings …")
    undertakings = create_undertakings(session, args.base_url, cost_centers, managers, fake)

    print("[populate] Creating companies …")
    companies = create_companies(session, args.base_url, fake)

    print("[populate] Creating contracts …")
    contracts = create_contracts(session, args.base_url, rng)

    print("[populate] Creating orders and initial order-versions …")
    orders, initial_versions = create_orders_and_versions(session, args.base_url, companies, contracts, rng)

    print("[populate] Creating consultants with engagements and assignments …")
    consultants, engagements, ova_list, ua_list = create_consultants_with_engagements(
        session, args.base_url, initial_versions, undertakings, fake, rng
    )

    print("[populate] Creating leaves …")
    leaves = create_leaves(session, args.base_url, consultants, rng)

    print("[populate] Cloning order versions (exercises clone-latest action) …")
    cloned_versions = clone_order_versions(session, args.base_url, orders, rng)

    # ---- Summary --------------------------------------------------------
    elapsed = time.time() - t0
    total_persons = len(managers) + len(consultants)
    total_contracts = len(contracts) + len(cloned_versions)  # clone creates extra contracts
    total_versions = len(initial_versions) + len(cloned_versions)

    print(
        f"\n[done] {elapsed:.1f}s — "
        f"CostCenters={len(cost_centers)}, "
        f"Undertakings={len(undertakings)}, "
        f"Companies={len(companies)}, "
        f"Contracts={total_contracts}, "
        f"Orders={len(orders)}, "
        f"OrderVersions={total_versions}, "
        f"Persons={total_persons}, "
        f"Engagements={len(engagements)}, "
        f"OVAssignments={len(ova_list)}, "
        f"UTAssignments={len(ua_list)}, "
        f"Leaves={len(leaves)}"
    )


if __name__ == "__main__":
    main()
