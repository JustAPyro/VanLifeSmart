window.addEventListener('DOMContentLoaded', event => {
    // Simple-DataTables
    // https://github.com/fiduswriter/Simple-DataTables/wiki

    const datatablesSimple = document.getElementById('datatablesSimple');
    if (datatablesSimple) {
        let options = {
            searchable: false,
            paging: false
        }
        new simpleDatatables.DataTable(datatablesSimple, options);
    }
});
