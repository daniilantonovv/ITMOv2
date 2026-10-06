---
name: collection-approval
description: Use when saving a VkusVill product collection (подборка) to the dashboard — after the VkusVill MCP returned products and a cart link. Validates the data against the service contract, shows the operator a receipt, waits for an explicit "да", then saves through the collections MCP (save_collection).
---

# Collection approval

The service shows collections publicly, so nothing reaches it without a
human "yes". This skill is the path from "the VkusVill MCP returned products"
to "the collection is on the dashboard".

## Steps

1. **Collect the data into a file.** Write `data/pending/<slug>.json` with
   `title`, `category`, `cart_url` and `products` (each with `name`, `price`
   per unit, `quantity`, and `kcal`/`protein`/`fat`/`carbs` per unit). Use only
   values the VkusVill MCP returned. If a value is missing, leave its default
   (`0`). Never guess it. Format: `examples/dinner.json`.

2. **Run the preview.** From the project root:

   ```sh
   .venv/bin/python .opencode/skills/collection-approval/scripts/preview.py data/pending/<slug>.json
   ```

   | Exit | Meaning | Next |
   |---|---|---|
   | 0 | valid; the receipt and the question are printed | step 3 |
   | 1 | invalid; field errors are listed | fix the file from the MCP data, repeat step 2 |
   | 2 | this cart is already saved | do not save; tell the operator the existing id |

   A warning that duplicates could not be checked is not a failure, but tell
   the operator about it.

3. **Ask the operator.** Paste the receipt **as printed** and end your
   message with the question from the script. Then stop and wait.

4. **Read the answer.**
   - An explicit "да", "yes" or "сохраняй" for **this** receipt: go to step 5.
   - Requested edits: change the file and go back to step 2. The new receipt
     needs a new "да".
   - Anything else (silence, "потом", a question, "наверное"): do not save.

5. **Save.** Call the `collections` MCP tool `save_collection` with the same
   data and `operator_approved: true`. Report the `id`, the total and the
   dashboard address `http://localhost:8010`. If the tool returns an error,
   show it as is and do not retry with changed data unless the operator says so.

## Rules

- `operator_approved: true` only after an explicit yes in the **current**
  conversation, given to the receipt you showed. Approval does not carry over
  to another collection or to an edited one.
- One collection, one approval, one `save_collection` call.
- Never edit prices, nutrition or the cart link to make validation pass. If
  the data is invalid, it goes back to the VkusVill MCP or the operator.
