// Copyright 2026 Quartile (https://www.quartile.co)
// License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import {BaseImportModel} from "@base_import/import_model";
import {patch} from "@web/core/utils/patch";

patch(BaseImportModel.prototype, {
    _onLoadSuccess(res) {
        // Store as plain object — Set doesn't work through Owl's reactive proxy
        this.matchFieldDefaults = {};
        for (const name of res.match_fields || []) {
            this.matchFieldDefaults[name] = true;
        }
        super._onLoadSuccess(res);
        for (const column of this.columns) {
            const fieldName = column.fieldInfo && column.fieldInfo.name;
            column.matchOnly = fieldName
                ? Boolean(this.matchFieldDefaults[fieldName])
                : false;
        }
    },

    setColumnField(column, fieldInfo) {
        super.setColumnField(column, fieldInfo);
        const fieldName = fieldInfo && fieldInfo.name;
        column.matchOnly =
            fieldName && this.matchFieldDefaults
                ? Boolean(this.matchFieldDefaults[fieldName])
                : false;
    },

    get formattedImportOptions() {
        const options = super.formattedImportOptions;
        const matchOnlyFields = [];
        for (const column of this.columns) {
            if (column.matchOnly && column.fieldInfo) {
                matchOnlyFields.push(column.fieldInfo.fieldPath);
            }
        }
        options.import_match_only_fields = matchOnlyFields;
        return options;
    },
});
