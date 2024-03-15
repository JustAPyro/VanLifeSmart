let editor = document.querySelector("#editor");
let result_table = null


ace.edit(editor, {
    theme: "ace/theme/sql_server",
    mode: "ace/mode/sql"
});

window.addEventListener('DOMContentLoaded', event => {
    // Simple-DataTables
    // https://github.com/fiduswriter/Simple-DataTables/wiki

    const datatablesSimple = document.getElementById("sql_result_table");
    if (datatablesSimple) {
        let options = {
            searchable: false,
            paging: false
        }
        result_table = new simpleDatatables.DataTable(datatablesSimple, options);
    }
});




//- Using an anonymous function:
document.getElementById("submit_query").onclick = async () => {
    var editor = ace.edit("editor")

    const formData = new FormData();
    formData.append("sql_query", editor.getValue())
    let new_data = {}

    try {
        const response = await fetch("sql.json", {
            method: "POST",
            body: formData,
        });
        new_data = await response.json()
    } catch (e) {
        console.error(e)
    }


    result_table.insert(new_data)
};