var current_talon = null;

function NextVisitor() {
    $.ajax({
        type: "GET",
        url: '/queue/operator/api',
        success: function(data){
            console.log(data);
            current_talon = data
            $("#StatusString").get(0).textContent = "Текущий талон:" +  data.name;
        },
    })
}
function CompleteVisitor() {
    const csrftoken = Cookies.get('csrftoken');
    $.ajax({
        type: "POST",
        url: '/queue/operator/api',
        beforeSend: function(jqXHR, settings) {
            jqXHR.setRequestHeader('X-CSRFToken', csrftoken);
        },
        success: function(){
            current_talon = null;
            $("#StatusString").get(0).textContent = "Текущий талон: Отсутствует";
            $("#StatusString").innerText = "Статус: Ожидание";
        },
    })
}