To use this module you need to:

1.  Go to a *Product \> General Information tab*.
2.  Create any record in "Secondary unit of measure".
3.  Set the conversion factor.
4.  Go to *Inventory tab* and set a second unit of measure.
5.  Push button 'On hand' and set quantities in stock for this
    product.
6.  Go to product list and you can see the secondary unit value.

When a transfer line is created, it gets the product's second unit of
measure for inventory (from the variant, or else from the template) by
default. A secondary unit passed by the document that creates the line,
such as a purchase order line, is kept.

To count an inventory adjustment in the secondary unit:

1.  Go to *Inventory \> Operations \> Physical Inventory*.
2.  Fill in the "Counted Quantity (Secondary Unit)" column for a product having a
    second unit of measure. The "Counted Quantity" column is filled in
    accordingly, and both stay in sync.
3.  Apply the adjustment as usual.
