$(document).ready(function(){
    getTalonData();
    init_handlers(chatSocket)
})

var chatSocket = new WebSocket('ws://' + window.location.host + '/ws/tablo');
var waitingList = $("#waitingList").get(0);
var inWorkList = $("#inWorkList").get(0);
setInterval(()=>{
    if (chatSocket.readyState == WebSocket.CLOSED){
        chatSocket = new WebSocket('ws://' + window.location.host + '/ws/tablo');
        init_handlers(chatSocket)
    }
    },10000)
function init_handlers(socket){
    socket.onopen = function(e) {
        console.log("WS Connection established");
    };
    socket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        const message = data.message;
        switch (data.type) {
            case "talon_create":
                var td = document.createElement('p');
                td.id = "talon" + message['id'].toString();
                td.textContent = message['name'];
                waitingList.appendChild(td);
                break;

            case "talon_update":
                var talon = $("#talon"+message['id'].toString()).get(0);
                inWorkList.appendChild(talon);
                break;

            case "talon_remove":
                $("#talon"+message['id'].toString()).remove();
                break;

            default:
                break;
        }
    };
    socket.onclose = function(e) {
        console.log("WS Connection closed");
    };
}

function getTalonData() {
    var ret_data = {};
    $.getJSON( '/queue/talon/api', function(data) {
            displayTalons(data);
        });
    return ret_data;
}

function displayTalons(data) {
    console.log(data);
    var waiting = data.filter(function(el){
        return !el.compliting_by;
    })
    var inWork = data.filter(function(el){
        return el.compliting_by;
    })
    removeAllChildren(inWorkList);
    removeAllChildren(waitingList);
    waiting.forEach((element, index) => {
        var td = document.createElement('p');
        td.id = "talon" + element['id'].toString();
        td.textContent = element['name'];
        waitingList.appendChild(td);
    });
    inWork.forEach((element, index) => {
        var td = document.createElement('p');
        td.id = "talon" + element['id'].toString();
        td.textContent = element['name'];
        inWorkList.appendChild(td);
    })
}

function removeAllChildren(element) {
  while (element.firstChild) {
    element.removeChild(element.firstChild);
  }
}