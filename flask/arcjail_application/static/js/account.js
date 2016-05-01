APP['account'] = function (motdPlayer) {
    var account = this;
    var nodes = {};
    nodes['current-account'] = document.getElementById('current-account');

    var renderCurrentAccount = function (account) {
        clearNode(nodes['current-account']);
        nodes['current-account'].appendChild(document.createTextNode(account));
    };

    motdPlayer.retarget('json-account', function () {
        motdPlayer.post({
            action: "init",
        }, function (data) {
            renderCurrentAccount(data['account']);
        }, function (error) {
            alert("Initialization error\n" + error);
        });
    }, function (error) {
        alert("Retargeting error\n" + error);
    });
}
