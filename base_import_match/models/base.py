# Copyright 2017 Jairo Llopis <jairo.llopis@tecnativa.com>
# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, models


class Base(models.AbstractModel):
    _inherit = "base"

    @api.model
    def _match_by_fields(self, match_fields, converted_row, imported_row):
        """Find a single existing record matching on the given fields."""
        domain = []
        for fname in match_fields & converted_row.keys():
            value = converted_row[fname]
            # For x2many fields
            if isinstance(value, list) and value and isinstance(value[0], tuple):
                for ref in imported_row.get(fname, "").split(","):
                    ref = ref.strip()
                    if ref:
                        domain.append((fname, "=", ref))
            else:
                domain.append((fname, "=", value))
        if not domain:
            return self
        match = self.search(domain)
        return match if len(match) == 1 else self

    @api.model
    def load(self, fields, data):
        """Try to identify rows by other pseudo-unique keys.

        It searches for rows that have no XMLID specified, and gives them
        one if any :attr:`~.field_ids` combination is found. With a valid
        XMLID in place, Odoo will understand that it must *update* the
        record instead of *creating* a new one.
        """
        # UI-selected match fields prevail; configured rules are only used when the
        # context key is absent (e.g. programmatic imports).
        ctx_match_only = self.env.context.get("import_match_only_fields")
        match_only_fields = set(ctx_match_only or []) & set(fields)
        has_rules = ctx_match_only is None and bool(
            self.env["base_import.match"]._usable_rules(self._name, fields)
        )
        if match_only_fields or has_rules:
            newdata = list()
            # Change .id (dbid) by id (xmlid)
            if ".id" in fields:
                column = fields.index(".id")
                fields[column] = "id"
                # data[0][column] = "id"
                for values in data:
                    dbid = int(values[column])
                    values[column] = self.browse(dbid).get_external_id().get(dbid)
            # Data conversion to ORM format
            import_fields = list(map(models.fix_import_export_id_paths, fields))
            converted_data = self._convert_records(
                self._extract_records(import_fields, data)
            )
            # Mock Odoo to believe the user is importing the ID field
            if "id" not in fields:
                fields.append("id")
                import_fields.append(["id"])
            # Needed to match with converted data field names
            clean_fields = [f[0] for f in import_fields]
            for dbid, xmlid, record, info in converted_data:
                row = dict(zip(clean_fields, data[info["record"]], strict=False))
                match = self
                if xmlid:
                    # Skip rows with ID, they do not need all this
                    row["id"] = xmlid
                    newdata.append(tuple(row[f] for f in clean_fields))
                    continue
                elif dbid:
                    # Find the xmlid for this dbid
                    match = self.browse(dbid)
                elif match_only_fields:
                    # Match using user-selected fields from the UI
                    match = self._match_by_fields(match_only_fields, record, row)
                else:
                    # Store records that match a combination
                    match = self.env["base_import.match"]._match_find(self, record, row)
                # Give a valid XMLID to this row if a match was found
                # To generate externals IDS.
                match.export_data(fields)
                ext_id = match.get_external_id()
                row["id"] = ext_id[match.id] if match else row.get("id", "")
                # Store the modified row, in the same order as fields
                newdata.append(tuple(row[f] for f in clean_fields))
            # We will import the patched data to get updates on matches
            data = newdata
            # Rebuild fields/data without match-only columns.
            if match_only_fields:
                drop_set = {fields.index(f) for f in match_only_fields}
                keep_indexes = [i for i in range(len(fields)) if i not in drop_set]
                fields[:] = [fields[i] for i in keep_indexes]
                data = [tuple(row[i] for i in keep_indexes) for row in data]
        # Normal method handles the rest of the job
        return super().load(fields, data)
