


function line_chart(canvas_name, data) {
    new Chart(document.getElementById(canvas_name), {
        type: 'line',
        data: {
        labels: data["labels"],
        datasets: [{
            data: data["tio"],
            label: "Outdoor Temp",
            borderColor: "#8e5ea2",
            fill: false
        }, {
            data: data["tio_apparent"],
            label:"Feels Like",
            borderColor: "#A34e2",
            fill: false
        }]},
        options: {
            title: {
                display: true,
                text: 'Boom'
            },
            hover: {
                mode: 'index',
                intersect: true
            },
            elements: {
                    point:{
                        radius: 0
                    }
                }
        }
    });
}