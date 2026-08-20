# Companies & contracts

This page covers the two records that describe **who you are buying services from**: the
`Company` and the `Contract` that formalises the buying relationship.

## Purpose

Keep the master list of vendors and the contracts you hold with them, so that every
subsequent order and engagement can point back to a single, unambiguous vendor and
contract.

## Who can do this

Admin (create, edit, delete). UndertakingManager and Person can read companies and
contracts that are reachable through the orders and engagements they can see.

## Screens

- **Company list.** `/companies/`
- **Company detail.** `/companies/<id>/`
- **Create company.** `/companies/create/`
- **Edit company.** `/companies/<id>/update/`
- **Delete company.** `/companies/<id>/delete/` (intermediate confirmation)
- **Contract list.** `/contracts/`
- **Contract detail.** `/contracts/<id>/`
- **Create contract.** `/contracts/create/`
- **Edit contract.** `/contracts/<id>/update/`
- **Delete contract.** `/contracts/<id>/delete/`

!!! note "Screenshot pending"
    A screenshot of the company list will be added here. Tracked as a P6.T5 follow-up.

## Happy path — create a company

1. Open `/companies/` and click **Add company**.
2. Fill in the name and any descriptive fields.
3. Save. You are redirected to the new company's detail page.
4. From the detail page, use the **Contracts** related block to add the first contract
   (see below).

## Happy path — add a contract to a company

1. Open the company's detail page at `/companies/<id>/`.
2. In the **Contracts** related block, click **Add contract**.
3. Enter the contract name, start and end dates, and any identifiers your organisation
   uses.
4. Save. The contract now appears on the company detail page and in the top-level
   `/contracts/` list.

The contract is now available for orders and order versions
(per [Orders & versions](orders.md)).

!!! note "Screenshot pending"
    A screenshot of the contract edit form will be added here. Tracked as a P6.T5 follow-up.

## Happy path — delete a company or contract

1. Open the record's detail page.
2. Click **Delete**. You are taken to a confirmation page.
3. Click **Yes, delete** to confirm, or **Cancel** to go back.

Deletion is only possible when nothing else in the system still points to the record. If
you see a validation error, follow the fix in the table below.

## Common validation errors and how to fix them

| Message | What it means | How to fix |
|---|---|---|
| "Contract with this name already exists." | Contract names must be unique per company. | Rename the new contract, or open the existing one to edit it. |
| "Cannot delete: this company still has contracts." | You must delete or reassign every contract that belongs to the company first. | Open each contract from the detail page and delete or reassign it, then retry. |
| "Cannot delete: this contract is used by an order." | An order still references this contract. | Point the order at a different contract, or delete the order first. |

## Related workflows

- Next up: [Orders & versions](orders.md) — orders live under contracts.
- Related: [People & engagements](people-and-engagements.md) — engagements ultimately roll
  back up through order versions to a contract and a company.

---

*For the underlying implementation, developers can read
[Architecture](../developer-guide/architecture.md).*
