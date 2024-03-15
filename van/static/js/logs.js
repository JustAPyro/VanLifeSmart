var ws_log = new WebSocket("ws://localhost:8000/ws/logs");
ws_log.onmessage = function (event) {
    log_data = JSON.parse(event.data);

    var traffic_html = document.getElementById("traffic_log");
    for (line in log_data['traffic.txt']['log']) {
        traffic_html.insertAdjacentHTML("beforeend", log_data['traffic.txt']['log'][line]);
    }

    var apscheduler_html = document.getElementById("apscheduler_log");
    for (line in log_data['apscheduler.txt']['log']) {
        apscheduler_html.insertAdjacentHTML("beforeend", log_data['apscheduler.txt']['log'][line]);
    }

    var webserver_html = document.getElementById("webserver_log");
    for (line in log_data['server.txt']['log']) {
        webserver_html.insertAdjacentHTML("beforeend", log_data['server.txt']['log'][line]);
    }

    document.getElementById("server.txt_size").innerHTML = log_data['server.txt'].size.toFixed(3) + " " + log_data['server.txt'].size_type;
    document.getElementById("apscheduler.txt_size").innerHTML = log_data['apscheduler.txt'].size.toFixed(3) + " " + log_data['apscheduler.txt'].size_type;
    document.getElementById("traffic.txt_size").innerHTML = log_data['traffic.txt'].size.toFixed(3) + " " + log_data['traffic.txt'].size_type;

    }

    function delete_log(val){
        fetch("http://raspberrypi.local:8000/logs/"+val+".json", {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            },
            body: null //if you do not want to send any addional data,  replace the complete JSON.stringify(YOUR_ADDITIONAL_DATA) with null
        })
    }