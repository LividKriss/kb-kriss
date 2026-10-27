# Threadflow: fixes and new feature (for Claude Code)

Source: Christopher Stangeby's fix requests of 26.10.2026 (Gmail thread "Threadflow Fixes"), clarified by Kriss on 27.10.2026.
Repo: Threadflow (Livid's production system, deployed via Replit). Read the repo's own docs/CLAUDE.md first and follow its conventions, tests and deploy flow.

---

## Task 1: Allow spaces in the Purchase Orders search field

**Where:** Inventory → Purchase Orders, the search field (search by order and by item).

**Problem:** Typing a space in the search field does nothing; spaces are stripped or blocked, so multi-word item names and references can't be searched.

**Expected:**
- Spaces can be typed and are kept in the query.
- Search by order number and by item name works with multi-word terms (e.g. "Kelvin Gray", "noil silk").
- Trim leading/trailing whitespace only when running the query, never while typing.

**Check:** look for a key handler, input mask or `replace(/\s/g, ...)` / `.trim()` on every keystroke in the search component, and for server-side tokenising that drops spaces.

**Done when:** a test (or manual check) shows that searching "Kelvin Gray" in Purchase Orders returns the matching POs/lines.

---

## Task 2: Treat 0 as a real value (measurement chart and comments)

**Where:** the measurement chart (style level), when defining base values, grading and other measurement values. Possibly also in sample comments where measurements are entered.

**Problem:** Entering 0 is treated as blank/empty. 0 is a real input (e.g. a grading step of 0 between sizes).

**Expected:**
- 0 is saved, displayed and used in calculations as 0.
- Only an empty field means "no value".
- Copying/grading logic must not skip or overwrite 0.

**Check:** falsy checks like `if (value)`, `value || null`, `value ? … : ''`, `Number(x) || undefined`, form libraries that coerce 0 to empty, and API/DB layers that map 0 to null. Fix both front end and back end.

**Done when:** a test covers saving and reloading a measurement row with 0 as base value and 0 as a grade step, and the chart shows 0 (not blank).

---

## Task 3: New page in Develop: Repair supplies orders (to Lisama)

**Goal:** Order repair supplies from Lisama (the factory) so they can be sent to the stores (Past, Trondheim etc.) for repairs. Today this is done ad hoc by email.

### 3.1 New page
Develop → new page **"Repair supplies"**. Lists repair supplies orders (number, supplier, status, created, expected delivery) and lets the user create a new one. Default supplier: Lisama (allow choosing another manufacturer if the data model makes that cheap; otherwise Lisama only).

### 3.2 A repair supplies order has line items of three kinds

**a) Belt loops**
- Fabric: choose the fabric (item) the belt loops are made of.
- Thread colour: choose among items in Develop → Items with item type **thread**.
- Quantity: number of finished belt loops to be sewn.

**b) Lining**
- A fixed, generic item "Lining" (no reference known).
- Quantity in **metres**.

**c) Threads**
- Choose a thread item (item type thread).
- Quantity in **cones** per reference.

### 3.3 Thread picker helper (used by belt loops and threads)
- Search threads directly by colour / item name / reference.
- Or search for a **style**, see the thread item(s) on that style's BOM, and add from there with one click. This is the usual way to find the right thread colour.

### 3.4 Submit and document
- **Submit** turns the draft into a submitted order with a number (follow the existing numbering conventions, e.g. a new prefix like `RS-00001`).
- Generate a styled **order document (PDF)** in the same style as existing PO/MO documents, listing all line items (type, fabric/thread/lining, colour, reference, quantity and unit), with delivery to Livid.
- The document must say clearly:
  - "This can be delivered with the next production delivery you send to Livid."
  - "Please confirm when you can prepare this and deliver it to us."
- Send to the supplier the same way POs/MOs are sent today (portal + email), reusing the existing send flow.

### 3.5 Pending matter and confirmation
- On submit, add the order as a **pending matter** for the supplier (same mechanism as the weekly pending-matters report / portal tasks).
- The supplier can **confirm** the order and enter the **date they can deliver** it, in the portal.
- Show the confirmed delivery date on the order and in the list.

### 3.6 Out of scope for now
- Prices/costing of repair supplies.
- Stock tracking of repair supplies at the stores.

**Done when:** a user can create a repair supplies order with all three line types, find a thread via a style's BOM, submit it, get the PDF, see it as a pending matter on Lisama's side, and Lisama can confirm with a delivery date. Add tests for the model/API and the confirm flow.

---

## Working notes
- Do all three tasks on a branch, one commit (or PR) per task.
- Run the existing test suite and add tests as listed above.
- Don't change existing PO/MO numbering or documents beyond reusing their components.
- Ask Kriss before any data migration on production.
