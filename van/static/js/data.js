let data_table = null

window.addEventListener('DOMContentLoaded', event => {
    // Simple-DataTables
    // https://github.com/fiduswriter/Simple-DataTables/wiki

    const dt_object = document.getElementById("data_table");
    if (dt_object) {
        let options = {
        }
        data_table = new simpleDatatables.DataTable(dt_object, options);
        let columns = data_table.columns
        columns.hide(0);
        console.log(columns.visible(0))
        data_table.columns.hide(1);
        data_table.columns.hide(2);
        console.log(data_table.columns.visible(0))
    }
});

function toggle_column(column_index) {
    var data_columns = data_table.columns;
    var target = column_index - 1;

    if (data_columns.visible(target)) {
        data_columns.hide([target]);
    }
    else {
        data_columns.show([target]);
    }
}

