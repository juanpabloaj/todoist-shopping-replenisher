# Phase 2/3 — Change Summary: Revisit Normalization Quality for Conservative Plural Handling

## Changes made

### `shopping_replenisher/normalize.py`
Added a 5-line comment block to `_singularize_word` explaining:
- Known imperfect outputs (`luces → luce`, `papeles → papele`) are intentional
- Why a more precise fix is unsafe: stripping `-es` would break English words like `noodles → noodl`
- The conservative final-`s` strip avoids incorrect merges even when cosmetically awkward

### `docs/domain_rules.md`
Added "Known Imperfect Outputs" subsection under "Light Singular/Plural Heuristic" section:
- Table showing `luces → luce` and `papeles → papele`
- Explains the tradeoff: simple `-es` rule can't distinguish Spanish from English without language detection
- States the conservative approach is intentional for v1

## Changes NOT made (per contract)
- No modifications to `tests/test_normalize.py` (tests already document the imperfect cases)
- No changes to normalization logic or behavior
- No changes to any other module
