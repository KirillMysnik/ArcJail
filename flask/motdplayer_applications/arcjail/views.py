# This file is part of ArcJail.
#
# ArcJail is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ArcJail is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ArcJail.  If not, see <http://www.gnu.org/licenses/>.

from flask import render_template

from . import app, plugin_instance


@app.route(plugin_instance.get_base_authed_route('account'))
def route_account(steamid, auth_method, auth_token, session_id):
    context = {
        'server_id': plugin_instance.server_id,
        'stylesheets': ('motdplayer', 'main', 'account'),
        'scripts': ('motdplayer', 'dom', 'account'),
        'steamid': steamid,
        'auth_method': auth_method,
        'auth_token': auth_token,
        'session_id': session_id,
    }
    return render_template('arcjail/route_account.html', **context)


@plugin_instance.json_authed_request('json-account')
def route_json_account(data_exchanger, json_data):
    if json_data['action'] != "init":
        return None

    return data_exchanger.exchange({
        'action': "init",
    })


@app.route(plugin_instance.get_base_authed_route('shop'))
def route_shop(steamid, auth_method, auth_token, session_id):
    context = {
        'server_id': plugin_instance.server_id,
        'stylesheets': (
            'main', 'inventory', 'shop', 'notifications', 'categories'),
        'scripts': ('dom', 'shop', 'notifications'),
        'steamid': steamid,
        'auth_method': auth_method,
        'auth_token': auth_token,
        'session_id': session_id,
    }
    return render_template('arcjail/route_shop.html', **context)


@plugin_instance.json_authed_request('json-shop')
def route_json_shop(data_exchanger, json_data):
    if json_data['action'] == "update":
        return data_exchanger.exchange({
            'action': "update",
        })

    if json_data['action'] in ("buy", "use"):
        return data_exchanger.exchange({
            'action': json_data['action'],
            'class_id': json_data['class_id'],
            'instance_id': json_data['instance_id'],
        })

    return None


@app.route(plugin_instance.get_base_authed_route('inventory'))
def route_inventory(steamid, auth_method, auth_token, session_id):
    context = {
        'server_id': plugin_instance.server_id,
        'stylesheets': ('main', 'inventory', 'notifications', 'categories'),
        'scripts': ('dom', 'inventory', 'notifications'),
        'steamid': steamid,
        'auth_method': auth_method,
        'auth_token': auth_token,
        'session_id': session_id,
    }
    return render_template('arcjail/route_inventory.html', **context)


@plugin_instance.json_authed_request('json-inventory')
def route_json_inventory(data_exchanger, json_data):
    if json_data['action'] == "update":
        return data_exchanger.exchange({
            'action': "update",
        })

    if json_data['action'] == "use":
        return data_exchanger.exchange({
            'action': json_data['action'],
            'class_id': json_data['class_id'],
            'instance_id': json_data['instance_id'],
        })

    return None


@app.route(plugin_instance.get_base_authed_route('su'))
def route_su(steamid, auth_method, auth_token, session_id):
    context = {
        'server_id': plugin_instance.server_id,
        'stylesheets': ('main', 'su'),
        'scripts': (),
        'steamid': steamid,
        'auth_method': auth_method,
        'auth_token': auth_token,
        'session_id': session_id,
    }
    return render_template('arcjail/route_su.html', **context)


@app.route(plugin_instance.get_base_authed_route('su-offline-items'))
def route_su_offline_items(steamid, auth_method, auth_token, session_id):
    context = {
        'server_id': plugin_instance.server_id,
        'stylesheets': (
            'main', 'su', 'su-offline-items', 'inventory', 'notifications'),
        'scripts': ('dom', 'su-offline-items', 'notifications'),
        'steamid': steamid,
        'auth_method': auth_method,
        'auth_token': auth_token,
        'session_id': session_id,
    }
    return render_template('arcjail/route_su_offline_items.html', **context)


@plugin_instance.json_authed_request('ajax-su-offline-items')
def route_ajax_su_offline_items(data_exchanger, json_data):
    if json_data['action'] == "view-inventory":
        return data_exchanger.exchange({
            'action': "view-inventory",
            'steamid': json_data['steamid'],
        })

    if json_data['action'] == "give-item":
        try:
            amount = int(json_data['amount'])
            if amount <= 0:
                raise ValueError
        except ValueError:
            return {}

        return data_exchanger.exchange({
            'action': 'give-item',
            'steamid': json_data['steamid'],
            'class_id': json_data['class_id'],
            'instance_id': json_data['instance_id'],
            'amount': amount,
        })

    return None
