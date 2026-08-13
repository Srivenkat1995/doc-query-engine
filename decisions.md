# Architecture & Technical Decisions Log

This document records the architectural and design decisions made during the development of this project, including the context, trade-offs, and alternatives considered.

---

## Decision 001: Problem Framing, Domain Choice & V1 Scope

* **Status:** Accepted
* **Decision:** Scope the system around extracting structured financial data (Invoices and Receipts) and enabling hybrid natural language + field-level querying.
* **Alternatives Considered:** 
  - Generic unstructured PDF parser (too broad, hard to measure extraction quality).
  - Medical discharge records (high privacy complexity, harder to generate synthetic test datasets).
* **Reasoning:** Financial documents contain a mix of key-value pairs, nested tables, line items, and varied visual layouts. This presents real-world messiness while allowing for precise schema validation via Pydantic/Zod.
* **What was Deliberately Cut for V1:**
  - Support for multi-language handwritten scripts.
  - Live multi-user real-time collaborative editing (focused on single-user human-in-the-loop review instead).

---
