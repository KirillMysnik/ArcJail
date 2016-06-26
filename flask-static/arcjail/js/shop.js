APP['shop'] = function (motdPlayer) {
    var shop = this;
    var nodes = {};
    nodes['current-account'] = document.getElementById('current-account');
    nodes['categories-shop'] = document.getElementById('categories-shop');
    nodes['categories-inventory'] = document.getElementById('categories-inventory');
    nodes['items-container'] = document.getElementById('items-container');
    nodes['inventory-container'] = document.getElementById('inventory-container');
    nodes['item-stats'] = document.getElementById('item-stats');

    var currentAccount = 0;
    var categories;
    var shopItems, inventoryItems;
    var activeCategoryShop = "all", activeCategoryInventory = "all";

    var renderCurrentAccount = function (accountFormatted) {
        clearNode(nodes['current-account']);
        nodes['current-account'].appendChild(document.createTextNode(accountFormatted + "c"));
    };

    var renderShopItems = function () {
        clearNode(nodes['items-container']);
        for (var i = 0; i < shopItems.length; i++) {
            (function (item) {
                if (activeCategoryShop != "all" && item['category_id'] != activeCategoryShop)
                    return;

                if ((i + 1) % 9 == 0) {
                    var div = nodes['items-container'].appendChild(document.createElement('div'));
                    div.classList.add('clear');
                }

                var itemContainer = nodes['items-container'].appendChild(document.createElement('div'));
                itemContainer.classList.add('item-container');
                itemContainer.style.backgroundImage = 'url("/static/arcjail/img/items/' + item.icon + '")';

                var priceTag = itemContainer.appendChild(document.createElement('div'));
                priceTag.classList.add('price-tag');
                priceTag.appendChild(document.createTextNode(item.price + "c"));

                var canBuy = true;

                if (item.price > currentAccount) {
                    priceTag.classList.add('too-expensive');
                    canBuy = false;
                }

                if (item['cannot_buy_reason']) {
                    itemContainer.classList.add('cannot-buy');
                    canBuy = false;
                }

                if (canBuy)
                    itemContainer.addEventListener('click', function (e) {
                        motdPlayer.post({
                            action: "buy",
                            class_id: item.class_id,
                            instance_id: item.instance_id,
                        }, function (data) {
                            handleResponseData(data);
                        }, function (error) {
                            alert("Purchase error\n" + error);
                        });
                    });

                // Stats render
                itemContainer.addEventListener('mouseover', function (e) {
                    clearNode(nodes['item-stats']);
                    var span;

                    if (item['cannot_buy_reason']) {
                        span = nodes['item-stats'].appendChild(document.createElement('span'));
                        span.appendChild(document.createTextNode(item['cannot_buy_reason']));
                        span.classList.add('cannot-buy-reason');

                        nodes['item-stats'].appendChild(document.createElement('br'));
                        nodes['item-stats'].appendChild(document.createElement('br'));
                    }

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

            })(shopItems[i]);
        }

        var div = nodes['items-container'].appendChild(document.createElement('div'));
        div.classList.add('clear');
    };

    var renderInventoryItems = function () {
        clearNode(nodes['inventory-container']);
        for (var i = 0; i < inventoryItems.length; i++) {
            (function (item) {
                if (activeCategoryInventory != "all" && item['category_id'] != activeCategoryInventory)
                    return;

                if ((i + 1) % 9 == 0) {
                    var div = nodes['inventory-container'].appendChild(document.createElement('div'));
                    div.classList.add('clear');
                }

                var itemContainer = nodes['inventory-container'].appendChild(document.createElement('div'));
                itemContainer.classList.add('item-container');
                itemContainer.style.backgroundImage = 'url("/static/arcjail/img/items/' + item.icon + '")';

                var amountLabel = itemContainer.appendChild(document.createElement('div'));
                amountLabel.classList.add('amount');
                amountLabel.appendChild(document.createTextNode("x" + item.amount));

                var canUse = true;

                if (item['cannot_use_reason']) {
                    itemContainer.classList.add('cannot-use');
                    canUse = false;
                }

                if (canUse)
                    itemContainer.addEventListener('click', function (e) {
                        motdPlayer.post({
                            action: "use",
                            class_id: item.class_id,
                            instance_id: item.instance_id,
                        }, function (data) {
                            handleResponseData(data);
                        }, function (error) {
                            alert("Purchase error\n" + error);
                        });
                    });

                // Stats render
                itemContainer.addEventListener('mouseover', function (e) {
                    clearNode(nodes['item-stats']);
                    var span;

                    if (item['cannot_use_reason']) {
                        span = nodes['item-stats'].appendChild(document.createElement('span'));
                        span.appendChild(document.createTextNode(item['cannot_use_reason']));
                        span.classList.add('cannot-use-reason');

                        nodes['item-stats'].appendChild(document.createElement('br'));
                        nodes['item-stats'].appendChild(document.createElement('br'));
                    }

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

    var renderCategories = function () {
        clearNode(nodes['categories-shop']);
        clearNode(nodes['categories-inventory']);

        for (var i = 0; i < categories.length; i++) {
            (function (category) {
                var input;

                if (!category['hide_from_shop']) {
                    input = nodes['categories-shop'].appendChild(document.createElement('input'));
                    input.type = "button";
                    input.value = category['caption'];
                    input.classList.add('category-button');
                    if (category['id'] == activeCategoryShop)
                        input.classList.add('active');

                    input.addEventListener('click', function (e) {
                        activeCategoryShop = category['id'];
                        renderCategories();
                        renderShopItems();
                    });
                }

                input = nodes['categories-inventory'].appendChild(document.createElement('input'));
                input.type = "button";
                input.value = category['caption'];
                input.classList.add('category-button');
                if (category['id'] == activeCategoryInventory)
                    input.classList.add('active');

                input.addEventListener('click', function (e) {
                    activeCategoryInventory = category['id'];
                    renderCategories();
                    renderInventoryItems();
                });

            })(categories[i]);
        }
    };

    var handleResponseData = function (data) {
        if (data['popup_notify'])
            popupNotification(data['popup_notify']);

        if (data['popup_error'])
            popupError(data['popup_error']);

        currentAccount = data['account'];

        categories = data['categories'];
        shopItems = data['shop_items'];
        inventoryItems = data['inventory_items'];

        renderCategories();
        renderShopItems();
        renderInventoryItems();
        renderCurrentAccount(data['account_formatted']);
    };

    document.addEventListener('mousemove', function(e) {
        nodes['item-stats'].style.top = e.screenY + 2 + 'px';
        nodes['item-stats'].style.left = e.screenX + 15 + 'px';
    });

    motdPlayer.retarget('json-shop', function () {
        motdPlayer.post({
            action: "update",
        }, function (data) {
            handleResponseData(data);
        }, function (error) {
            alert("Initialization error\n" + error);
        });
    }, function (error) {
        alert("Retargeting error\n" + error);
    });
}
