# Copyright 2016 Grupo ESOC Ingeniería de Servicios, S.L.U. - Jairo Llopis
# Copyright 2016 Tecnativa - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from os import path

from odoo.tests.common import TransactionCase

PATH = path.join(path.dirname(__file__), "import_data", "%s.csv")
OPTIONS = {
    "headers": True,
    "quoting": '"',
    "separator": ",",
}


class ImportCase(TransactionCase):
    def _base_import_record(self, res_model, file_name=None, data=None):
        """Create and return a ``base_import.import`` record."""
        if file_name:
            with open(PATH % file_name) as demo_file:
                data = demo_file.read()
        return self.env["base_import.import"].create(
            {
                "res_model": res_model,
                "file": data,
                "file_name": f"{file_name or 'test'}.csv",
                "file_type": "csv",
            }
        )

    def test_res_partner_external_id(self):
        """Change name based on External ID."""
        deco_addict = self.env.ref("base.res_partner_2")
        record = self._base_import_record("res.partner", "res_partner_external_id")
        record.execute_import(["id", "vat", "name"], [], OPTIONS)
        deco_addict.env.cache.invalidate()
        self.assertEqual(deco_addict.name, "Deco Addict External ID Changed")

    def test_res_partner_dbid(self):
        """Change name based on DB ID."""
        deco_addict = self.env.ref("base.res_partner_2")
        gemini_furniture = self.env.ref("base.res_partner_3")
        record = self._base_import_record("res.partner", "res_partner_dbid")
        record.execute_import([".id", "vat", "name"], [], OPTIONS)
        deco_addict.env.cache.invalidate()
        self.assertEqual(deco_addict.name, "Deco Addict External DBID Changed")
        self.assertEqual(
            gemini_furniture.name, "Gemini Furniture External DBID Changed"
        )

    def test_res_partner_vat(self):
        """Change name based on VAT."""
        deco_addict = self.env.ref("base.res_partner_2")
        deco_addict.vat = "BE0477472701"
        record = self._base_import_record("res.partner", "res_partner_vat")
        record.execute_import(["name", "vat", "is_company"], [], OPTIONS)
        deco_addict.env.cache.invalidate()
        self.assertEqual(deco_addict.name, "Deco Addict Changed")

    def test_res_partner_invalid_combination_vat(self):
        """Change name based on VAT."""
        deco_addict = self.env.ref("base.res_partner_2")
        deco_addict.vat = "BE0477472701"
        record = self._base_import_record(
            "res.partner", "res_partner_invalid_combination_vat"
        )
        record.execute_import(["name", "vat", "is_company"], [], OPTIONS)
        deco_addict.env.cache.invalidate()
        self.assertEqual(deco_addict.name, deco_addict.name)

    def test_res_partner_parent_name_is_company(self):
        """Change email based on parent_id, name and is_company."""
        record = self._base_import_record(
            "res.partner", "res_partner_parent_name_is_company"
        )
        record.execute_import(
            ["name", "is_company", "parent_id/id", "email"], [], OPTIONS
        )
        self.assertEqual(
            self.env.ref("base.res_partner_address_4").email,
            "floyd.steward34.changed@example.com",
        )

    def test_res_partner_email(self):
        """Change name based on email."""
        record = self._base_import_record("res.partner", "res_partner_email")
        record.execute_import(["email", "name"], [], OPTIONS)
        self.assertEqual(
            self.env.ref("base.res_partner_address_4").name, "Floyd Steward Changed"
        )

    def test_res_partner_name(self):
        """Change function based on name."""
        record = self._base_import_record("res.partner", "res_partner_name")
        record.execute_import(["function", "name"], [], OPTIONS)
        self.assertEqual(
            self.env.ref("base.res_partner_address_4").function, "Function Changed"
        )

    def test_res_partner_name_duplicated(self):
        """Change function with duplicate names."""
        record = self._base_import_record("res.partner", "res_partner_name_mail")
        partner_1 = self.env.ref("base.res_partner_address_4")
        partner_2 = self.env.ref("base.res_partner_2")
        partner_2.name = partner_1.name
        partner_2.email = "unique@example.com"
        original_function_partner_1 = partner_1.function
        record.execute_import(["function", "name", "email"], [], OPTIONS)
        self.assertEqual(
            self.env.ref("base.res_partner_address_4").function,
            original_function_partner_1,
        )
        self.assertEqual(
            self.env.ref("base.res_partner_2").function, "Function Changed"
        )

    def test_match_only_from_ui(self):
        """Match by email via UI selection, update function, don't write email."""
        partner = self.env["res.partner"].create(
            {"name": "Match Partner", "email": "match@example.com"}
        )
        record = self._base_import_record(
            "res.partner", data="match@example.com,New Function\n"
        )
        options = dict(OPTIONS, import_match_only_fields=["email"])
        record.execute_import(["email", "function"], [], options)
        partner.env.cache.invalidate()
        self.assertEqual(partner.function, "New Function")
        self.assertEqual(partner.email, "match@example.com")

    def test_match_only_no_match_creates(self):
        """When match-only field doesn't find a record, create a new one."""
        record = self._base_import_record(
            "res.partner", data="nonexistent@example.com,New Partner\n"
        )
        options = dict(OPTIONS, import_match_only_fields=["email"])
        count_before = self.env["res.partner"].search_count([])
        record.execute_import(["email", "name"], [], options)
        count_after = self.env["res.partner"].search_count([])
        self.assertEqual(count_after, count_before + 1)

    def test_match_only_empty_skips_rules(self):
        """Empty match-only list from UI skips matching even if rules exist."""
        partner = self.env["res.partner"].create(
            {"name": "VAT Partner", "vat": "BE0411905847", "is_company": True}
        )
        original_name = partner.name
        record = self._base_import_record(
            "res.partner", data="Changed Name,BE0411905847,True\n"
        )
        # Empty list = user unchecked everything in UI -> no matching
        options = dict(OPTIONS, import_match_only_fields=[])
        count_before = self.env["res.partner"].search_count([])
        record.execute_import(["name", "vat", "is_company"], [], options)
        count_after = self.env["res.partner"].search_count([])
        partner.env.cache.invalidate()
        # Should create a new record, not update the existing one
        self.assertEqual(count_after, count_before + 1)
        self.assertEqual(partner.name, original_name)

    def test_res_users_login(self):
        """Change name based on login."""
        record = self._base_import_record("res.users", "res_users_login")
        record.execute_import(["login", "name"], [], OPTIONS)
        self.assertEqual(self.env.ref("base.user_demo").name, "Demo User Changed")
