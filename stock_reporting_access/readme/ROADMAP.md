The ``stock.valuation.layer`` model is restricted to Inventory Managers by
default.
If ``stock_account`` is installed after this module, the access rights for
``stock.valuation.layer`` must be added manually:

1. Go to Settings > Technical > Models
2. Search for ``stock.valuation.layer``
3. Open the model and go to the Access Rights tab
4. Add read-only permission for the "User: Inventory Reporting Access" group
