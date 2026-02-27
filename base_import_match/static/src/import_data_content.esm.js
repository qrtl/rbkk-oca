// Copyright 2026 Quartile (https://www.quartile.co)
// License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import {ImportDataContent} from "@base_import/import_data_content/import_data_content";
import {patch} from "@web/core/utils/patch";

patch(ImportDataContent.prototype, {
    onMatchOnlyChanged(column, ev) {
        column.matchOnly = ev.target.checked;
    },
});
