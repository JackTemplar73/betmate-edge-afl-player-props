const customFilterDiv = document.querySelector('#custom-filters');
customFilterDiv.innerHTML = "";

const filterSelectLabel = document.createElement('label');
filterSelectLabel.innerText = "Select a field to filter";
filterSelectLabel.for = "filter-select";
filterSelectLabel.classList = "form-label fw-bold";

const filterSelect = document.createElement('select');
filterSelect.id = "filter-select";
filterSelect.classList = "form-select";

let filterOption = document.createElement("option");
filterOption.value = "";
filterOption.text = "Select a field";
filterSelect.appendChild(filterOption);

const filterAdd = document.createElement('button');
filterAdd.classList = "btn btn-primary btn-sm mx-1 my-2";
filterAdd.innerText = "Add filter";

const selectOptions = [];

window.addEventListener('DOMContentLoaded', (event) => {
    //try {
    //columnIds = [];
    //Reactable.getInstance(reactableId).allColumns.forEach((o) => columnIds.push(o.id));

    Object.keys(filterColumns).forEach(key => {
        if (
            (typeof ignoreFilterInDataset !== 'undefined' && ignoreFilterInDataset)
            || (Object.keys(Reactable.getInstance(reactableId).data[0]).includes(key))
        ) {
            //if (columnIds.includes(key)) {
            // if (typeof filterColumnsDefault !== 'undefined' && filterColumnsDefault.includes(key)) {
            //     filterCreate(key, true);
            // } else {

            filterOption = document.createElement("option");
            filterOption.id = `filter-select-${key}`;
            istotal = false;

            if (typeof filterColumns[key] === 'object') {
                filterOption.value = filterColumns[key]["column"];
                filterOption.text = filterColumns[key]["label"];

                if (filterColumns[key]["total"]) istotal = true;
            } else {
                filterOption.value = key;
                filterOption.text = filterColumns[key];
            }

            filterOption.dataset.istotal = istotal;

            if (filterOption.value && filterOption.text) {
                selectOptions.push(filterOption);
                filterSelect.appendChild(filterOption);
            }

            if (typeof filterColumnsDefault !== 'undefined' && filterColumnsDefault.includes(key)) filterCreate(filterOption.id, key, filterOption.text, istotal);
            // }
        } else {
            delete filterColumns[key];
        }
    })
    // } catch (e) {
    //     customFilterDiv.classList.add("d-none");
    // }
})

customFilterDiv.appendChild(filterSelectLabel);
customFilterDiv.appendChild(filterSelect);
customFilterDiv.appendChild(filterAdd);

const customFilterRow = document.createElement('div');
customFilterRow.classList = "d-flex flex-wrap";
customFilterDiv.appendChild(customFilterRow);

const filterCreate = function (id, column, label_text, total = false) {
    const columnLower = column.toLowerCase();

    const div = document.createElement('div');
    div.classList = "m-2";

    const label = document.createElement('label');
    label.innerText = label_text;
    label.for = `filter-min-${columnLower}`;
    label.classList = "form-label fw-bold";

    const divWarning = document.createElement('div');
    divWarning.id = `filter-warning-${columnLower}`;
    divWarning.dataset.column = column;
    divWarning.classList = "d-none";
    divWarning.innerHTML = `<span class="badge bg-primary bg-danger mb-1">DATA NOT AVAILABLE</span>`

    const inputGroup = document.createElement('div');
    inputGroup.classList = "input-group input-group-sm";

    const labelMin = document.createElement('span');
    labelMin.innerText = "from";
    labelMin.classList = "input-group-text";
    inputGroup.appendChild(labelMin);

    const valueMin = document.createElement('input');
    valueMin.id = `filter-min-${columnLower}`;
    valueMin.type = "text";
    valueMin.size = "4";
    inputGroup.appendChild(valueMin);

    const labelMax = document.createElement('span');
    labelMax.innerText = "to";
    labelMax.classList = "input-group-text";
    inputGroup.appendChild(labelMax);

    const valueMax = document.createElement('input');
    valueMax.id = `filter-max-${columnLower}`;
    valueMax.type = "text";
    valueMax.size = "4";
    inputGroup.appendChild(valueMax);

    const removeFilter = document.createElement('button');
    removeFilter.type = "button";
    removeFilter.classList = "btn-close small";
    div.appendChild(removeFilter);

    removeFilter.addEventListener('click', () => {
        filterCustom(column, "", "");
        selectOptions.forEach(opt => { if (id === opt.id) opt.disabled = false });
        div.remove();
    })

    div.appendChild(label);
    div.appendChild(divWarning);
    div.appendChild(inputGroup);

    valueMin.addEventListener('input', () => {
        filterCustom(column, valueMin.value, valueMax.value, total);
    })
    valueMax.addEventListener('input', () => {
        filterCustom(column, valueMin.value, valueMax.value, total);
    })

    customFilterRow.appendChild(div);

    selectOptions.forEach(opt => { if (id === opt.id) opt.disabled = true });

    if (typeof updateFiltersIndicator !== "undefined") updateFiltersIndicator();
}

filterAdd.addEventListener('click', (e) => {
    if (filterSelect.value) {
        const filterColumn = filterSelect.selectedOptions[0];
        filterCreate(filterColumn.id, filterColumn.value, filterColumn.text, filterColumn.dataset.istotal);

        filterSelect.value = "";
    }
})

////////////////////////////////////////////////////////////////////////////////////////////////

// ct_handles = {};
// //ct_sharedData = JSON.parse(document.querySelector(`script[data-for='${reactableId}']`).innerHTML).x.tag.attribs.crosstalkGroup;
// let reactableScript = document.querySelector(`script[data-for='${reactableId}']`);
// let ct_sharedData;

// if (reactableScript)
//     ct_sharedData = JSON.parse(reactableScript.innerHTML).x.tag.attribs.crosstalkGroup;
// else if (typeof ct_sharedData_temp !== 'undefined')
//     ct_sharedData = ct_sharedData_temp;

// const filterCustom = function (column, min_value, max_value) {
//     let handle;
//     if (ct_handles[column]) {
//         handle = ct_handles[column];
//     } else {
//         handle = new window.crosstalk.FilterHandle(ct_sharedData);
//         ct_handles[column] = handle;
//     }

//     if (min_value.length === 0 && max_value.length === 0) {
//         filterClear(column);
//     } else {
//         const filtered = [];

//         for (i = 0; i < Reactable.getInstance(reactableId).data.length; i++) {
//             const value = Reactable.getInstance(reactableId).data[i][column];
//             if ((value !== null) && (value >= min_value || min_value.length === 0) && (value <= max_value || max_value.length === 0)) filtered.push(i + 1);
//         };

//         handle.set(filtered);
//     }
// };

// const filterClear = function (column) {
//     if (ct_handles[column]) ct_handles[column].clear();
// }

// const filterClearAll = function () {
//     Object.keys(ct_handles).forEach(key => {
//         ct_handles[key].clear();
//     })
// }


const filterRange = function (rows, columnId, filterValue) {
    const [min, max, total] = filterValue
    const filter_total = total && total === 'true' && typeof match_count_column !== 'undefined' && Reactable.getInstance(reactableId).data.length > 0 && typeof Reactable.getInstance(reactableId).data[0][match_count_column] !== 'undefined';

    return rows.filter(row => {
        let value = row.values[columnId]
        if (filter_total) value = Math.round(value * row.values[match_count_column], 1)  // 'total' is a string, not logical

        return (value >= min || min.length === 0) && (value <= max || max.length === 0)
    })
}

const filterSet = function (rows, columnId, filterValues) {
    return rows.filter(row => {
        const value = row.values[columnId];
        return filterValues.includes(value) || (typeof filterValues === 'string' && value.toLowerCase().includes(filterValues.toLowerCase()));
    })
}

const filterRowId = function (rows, columnId, filterValues) {
    filterValues = filterValues.map(String);

    return rows.filter(row => {
        const value = row.id;
        return filterValues.includes(value);
    })
}

const filterCustom = function (column, min_value, max_value, total = false) {
    if (min_value.length === 0 && max_value.length === 0) {
        filterClear(column);
    } else {
        if (typeof setFilter !== "undefined")
            setFilter(column, [min_value, max_value, total]);
        else
            Reactable.setFilter(reactableId, column, [min_value, max_value, total]);
    }
};

const filterClear = function (column) {
    if (typeof setFilter !== "undefined")
        setFilter(column, undefined);
    else
        Reactable.setFilter(reactableId, column, undefined);
}

const filterClearAll = function () {
    //if (typeof updateFiltersIndicator !== "undefined") updateFiltersIndicator();
}


// function(rows, columnId, filterValue) {
//     return rows.filter(function (row) {
//         return row.values[columnId] >= filterValue[0] && row.values[columnId] <= filterValue[1]
//     })
// }