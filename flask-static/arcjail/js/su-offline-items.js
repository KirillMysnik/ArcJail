APP['su-offline-items'] = function (motdPlayer) {
    var main = this;
    var nodes = {};
    [
        "item-stats",
        "view-inventory-steamid",
        "view-inventory-submit",
        "inventory-container",
        "give-item-steamid",
        "give-item-classid",
        "give-item-instanceid",
        "give-item-amount",
        "give-item-submit"
    ].forEach(function (nodeId, index, array) {
        nodes[nodeId] = document.getElementById(nodeId);
    });

    var inventoryItems;

    var renderInventoryItems = function () {
        clearNode(nodes['inventory-container']);
        for (var i = 0; i < inventoryItems.length; i++) {
            (function (item) {
                if ((i + 1) % 10 == 0) {
                    var div = nodes['inventory-container'].appendChild(document.createElement('div'));
                    div.classList.add('clear');
                }

                var itemContainer = nodes['inventory-container'].appendChild(document.createElement('div'));
                itemContainer.classList.add('item-container');
                itemContainer.style.backgroundImage = 'url("/static/arcjail/img/items/' + item.icon + '")';

                var amountLabel = itemContainer.appendChild(document.createElement('div'));
                amountLabel.classList.add('amount');
                amountLabel.appendChild(document.createTextNode("x" + item['amount']));

                // Stats render
                itemContainer.addEventListener('mouseover', function (e) {
                    clearNode(nodes['item-stats']);
                    var span;

                    span = nodes['item-stats'].appendChild(document.createElement('span'));
                    span.appendChild(document.createTextNode(item['caption']));
                    span.classList.add('name');

                    nodes['item-stats'].appendChild(document.createElement('br'));
                    nodes['item-stats'].appendChild(document.createElement('br'));

                    span = nodes['item-stats'].appendChild(document.createElement('span'));
                    span.appendChild(document.createTextNode(item['description']));
                    span.classList.add('description');

                    nodes['item-stats'].appendChild(document.createElement('br'));
                    nodes['item-stats'].appendChild(document.createElement('br'));

                    var li, ul = nodes['item-stats'].appendChild(document.createElement('ul'));
                    [
                        'stat_max_per_slot',
                        'stat_team_restriction',
                        'stat_manual_activation',
                        'stat_auto_activation',
                        'stat_max_sold_per_round',
                    ].forEach(function (stat, index, array) {
                        if (item[stat] == null)
                            return;

                        li = ul.appendChild(document.createElement('li'));
                        li.appendChild(document.createTextNode(item[stat]));
                    });

                    nodes['item-stats'].appendChild(document.createElement('br'));

                    span = nodes['item-stats'].appendChild(document.createElement('span'));
                    span.appendChild(document.createTextNode(item['stat_price']));
                    span.classList.add('price');

                    nodes['item-stats'].classList.add('visible');
                });

                itemContainer.addEventListener('mouseout', function (e) {
                    nodes['item-stats'].classList.remove('visible');
                });

            })(inventoryItems[i]);
        }

        var div = nodes['inventory-container'].appendChild(document.createElement('div'));
        div.classList.add('clear');
    };

    nodes['view-inventory-submit'].addEventListener('click', function (e) {
        motdPlayer.post({
            action: "view-inventory",
            steamid: nodes['view-inventory-steamid'].value
        }, function (data) {
            if (data['popup_notify'])
                popupNotification(data['popup_notify']);

            if (data['popup_error'])
                popupError(data['popup_error']);

            if (data['inventory_items']) {
                inventoryItems = data['inventory_items'];
                renderInventoryItems();
            }
        }, function (error) {
            alert("Request error\n" + error);
        });
    });

    nodes['give-item-submit'].addEventListener('click', function (e) {
        motdPlayer.post({
            action: "give-item",
            steamid: nodes['give-item-steamid'].value,
            class_id: nodes['give-item-classid'].value,
            instance_id: nodes['give-item-instanceid'].value,
            amount: nodes['give-item-amount'].value
        }, function (data) {
            if (data['popup_notify'])
                popupNotification(data['popup_notify']);

            if (data['popup_error'])
                popupError(data['popup_error']);
        }, function (error) {
            alert("Request error\n" + error);
        });
    });

    document.addEventListener('mousemove', function(e) {
        nodes['item-stats'].style.top = e.screenY + 2 + 'px';
        nodes['item-stats'].style.left = e.screenX + 15 + 'px';
    });

    motdPlayer.retarget('ajax-su-offline-items', function () {

    }, function (error) {
        alert("Retargeting error\n" + error);
    });
};