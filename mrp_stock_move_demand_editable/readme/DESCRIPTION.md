When manufacturing is configured with 2 or 3 steps (*Pick components then
manufacture*), Odoo generates a *Pick Components* transfer to move the raw
materials to the production area. The demand (initial requested quantity) of
this transfer is locked and cannot be changed.

This module makes the demand quantity of those *Pick Components* transfers
editable, so a different quantity than the one required by the manufacturing
order can be requested (for example, moving a larger quantity to the shop
floor and returning the surplus afterwards).
