The behavior is resolved with the following precedence (most specific wins):

1.  **Product** -- *Inventory* tab of a product, field *Byproduct Auto Pick*.
2.  **Product category** -- field *Byproduct Auto Pick* (cascades up the
    category tree).
3.  **Company** -- *Manufacturing \> Configuration \> Settings*, option
    *Auto-pick Manually Edited Byproducts*.

At product and category level the field has two values, and can also be left
empty:

-   **Empty**: fall back to the next level (category, then company).
-   **Always**: keep the manually entered byproduct quantity.
-   **Never**: reset to the quantity to produce (standard Odoo behavior).

To enable the behavior everywhere, tick the company-wide option and leave the
product and category fields empty. To enable it only for some products, set
them (or their category) to *Always*.
