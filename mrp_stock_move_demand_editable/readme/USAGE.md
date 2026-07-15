Prerequisite: the warehouse must be configured with *Pick components then
manufacture* (2 steps) or *Pick components, manufacture, then store products*
(3 steps).

1.  Confirm a manufacturing order. Odoo creates the related *Pick Components*
    transfer.
2.  Open the transfer. The **Demand** column of the operations is now editable
    even though the transfer is locked.
3.  Change the demand to the desired quantity (e.g. from 5 to 7).
4.  Click **Check Availability** to reserve the new quantity.

The reserved quantity is what the Barcode app shows as the target, so step 4 is
required for the operator to see the updated quantity on the shop floor.

The manufacturing order is not affected: it keeps consuming the quantity
defined by its bill of materials. Any surplus moved to the production area can
be returned to its original location using a return transfer.
