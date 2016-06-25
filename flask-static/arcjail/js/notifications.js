var popupNotification = function (text) {
    var body = document.getElementsByTagName('body')[0];
    var div = body.appendChild(document.createElement('div'));
    div.classList.add('popup-notification');
    div.appendChild(document.createTextNode(text));

    div.style.opacity = 1;

    setTimeout(function () {
        div.style.opacity = 0;
    }, 1000);

    setTimeout(function () {
        body.removeChild(div);
    }, 3500);
};

var popupError = function (text) {
    var body = document.getElementsByTagName('body')[0];
    var div = body.appendChild(document.createElement('div'));
    div.classList.add('popup-error');
    div.appendChild(document.createTextNode(text));

    div.style.opacity = 1;

    setTimeout(function () {
        div.style.opacity = 0;
    }, 1000);

    setTimeout(function () {
        body.removeChild(div);
    }, 3500);
};
