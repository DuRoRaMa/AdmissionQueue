
var chatSocket = new WebSocket('ws://' + window.location.host + '/ws/tablo');
init_handlers(chatSocket)
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
        document.querySelector('#list').append(data.message + '\n');
    };
    socket.onclose = function(e) {
        console.log("WS Connection closed");
    };
}