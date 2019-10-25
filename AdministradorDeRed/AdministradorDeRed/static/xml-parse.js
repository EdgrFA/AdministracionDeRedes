alert("Hello! I am an alert box!!");
fetch('../static/ping-puller.xml')
    .then(function(resp){
        return resp.text();
    })
    .then(function(data){
        let parser = new DOMParser(),
            xmlDoc = parser.parseFromString(data, 'text/xml');
        var subredes = xmlDoc.getElementsByTagName('subred');
        
        var i, divData = "";
        var tab = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp"
        for (i = 0; i < subredes.length; i++) {
            divData += "<div>"
            divData += "<h4>Super Subred: " + subredes[i].getAttribute('id');
            divData += " (mascara: " + subredes[i].getAttribute('mascara');
            divData += ", broadcast: " + subredes[i].getAttribute('broadcast') + ")";
            divData += "</h4>"
            var hosts = subredes[i].childNodes;
            if(hosts.length == 0){
                divData += tab + "Sin dispositivos conectados. <br>"
            } else {
                var j;
                divData += tab + "Dispositivos conectados: <br>"
                for(j = 0; j < hosts.length; j++){
                    divData += tab + hosts[j].textContent + "<br>";
                }
            }

            divData += "<br></div>"
        }
        document.getElementById('tabla-subredes').innerHTML = divData;
    })