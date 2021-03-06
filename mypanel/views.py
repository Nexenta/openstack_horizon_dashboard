
from horizon import tabs
from horizon import views

from django.utils.translation import ugettext_lazy as _

from openstack_dashboard.dashboards.horizon_nedge_dashboard.mypanel import tabs as mydashboard_tabs
from openstack_dashboard.dashboards.horizon_nedge_dashboard.vendor.filesize import size
from openstack_dashboard.dashboards.horizon_nedge_dashboard.vendor.filesize import alternative

import sys
sys.path.append("/usr/lib/python2.7/dist-packages")
import requests
import json

from django.conf import settings

class IndexView(views.APIView):
    tab_group_class = mydashboard_tabs.MypanelTabs
    template_name = 'horizon_nedge_dashboard/mypanel/index.html'

    def get_data(self, request, context, *args, **kwargs):

        context['notifications'] = []
        context['n_nodes_good'] = 0
        context['n_nodes_bad'] = 0

        try:
            context['nedge_url'] = settings.NEDGE_URL
            print '+++ +++ endpoint'
            print context['nedge_url']
        except AttributeError:
            note = { 'message': _('Missing parameter NEDGE_URL in settings.py. For example, NEDGE_URL="http://192.168.100.1:8080/" with final slash.') }
            context['notifications'].append( note )
            return context

        try:
            status_endpoint = requests.get("%s/system/status" % settings.NEDGE_URL)
            # status_endpoint = requests.get('0.0.0.0')
            status = json.loads(status_endpoint.text)['response']['restWorker']
            context['system_status'] = status
            print '+++ +++ status'
            print context['system_status']
        except requests.exceptions.RequestException:
            context['system_status'] = "NOT OK"
            note = { 'message': _('System is down! Please make sure that Admin Rest worker is available at ' + context['nedge_url'] + '. ' +
                                  'To change this configuration, edit settings.py') }
            context['notifications'].append( note )
            print '+++ +++ notes'
            print context['notifications']
            return context

        stats_endpoint = requests.get("%s/system/stats" % settings.NEDGE_URL)

        context['nodes'] = []


        stats = json.loads(stats_endpoint.text)['response']['stats']

        nodes = stats['servers']
        for n in nodes:
            if 100 == nodes[n]['health']:
                nodes[n]['status'] = 'ONLINE' 
            else:
                nodes[n]['status'] = 'FAULTED'
            nodes[n]['capacity'] = size(nodes[n]['capacity'], system=alternative)
            nodes[n]['used'] = size(nodes[n]['used'], system=alternative)
            context['nodes'].append(n)

        context['nodes'] = nodes
        nodes_good = {x:nodes[x] for x in nodes if 100 == nodes[x]['health']}
        context['n_nodes_good'] = len(nodes_good)
        context['n_nodes_bad'] = len(nodes) - context['n_nodes_good']
        context['n_objects'] = stats['summary']['total_num_objects']
        context['capacity_total'] = size(stats['summary']['total_capacity'], system=alternative)
        context['capacity_used'] = size(stats['summary']['total_used'], system=alternative)
        context['capacity_available'] = size(stats['summary']['total_available'], system=alternative)

        data_reduction = stats['summary']['total_logical_used'] - stats['summary']['total_used']
        if data_reduction < 0:
            data_reduction = 0
        context['data_reduction'] = size(data_reduction, system=alternative)

        # reduction factor is the difference between logical and physical used, expressed as a portion of the logical used.
        context['reduction_factor'] = data_reduction / (stats['summary']['total_logical_used']+1)
        context['reduction_factor'] = "%sx" % context['reduction_factor']

        return context
