""" Create or update HRP projects datasets for HDX

Requires Python3
"""

import config
import ckanapi, ckancrawler, datetime, json, logging, re, requests, urllib, sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("update-hrp-quickcharts")


def process_packages(crawler):

    for package in crawler.packages(fq='organization:ocha-fts humanitarian response plan'):
        name = package['name']
        if re.match(r'^hrp-projects-[a-z]{3}$', name):
            if not package['has_quickcharts']:
                logger.info("Adding QuickCharts to %s", package['name'])
                add_quickcharts(crawler.ckan, package['id'])

def add_quickcharts (ckan, package_id):
    package = ckan.action.package_show(id=package_id)
    resource_id = package['resources'][0]['id']

    # Check if there's an existing view to update
    # This should never happen, since all resources are recreated,
    # but if the script changes in the future, this will protect
    # us against surprises
    views = ckan.action.resource_view_list(id=resource_id)
    for view in views:
        if view.get("view_type") == "hdx_hxl_preview":
            logger.info("Updating existing Quick Charts view for %s", package_id)
            view["hxl_preview_config"] = config.CONFIG['quickcharts_config']
            ckan.call_action("resource_view_update", view)
            return
        
    # Need to create a new view
    # This should always be the case right now
    logger.info("Adding new Quick Charts view for %s", package_id)
    view = {
        "description": "",
        "title": "Quick Charts",
        "resource_id": resource_id,
        "view_type": "hdx_hxl_preview",
        "hxl_preview_config": config.CONFIG['quickcharts_config'],
    }
    ckan.call_action('resource_view_create', view)


########################################################################
# Top level
########################################################################

# Open a CKAN API connection
crawler = ckancrawler.Crawler(config.CONFIG['ckanurl'], apikey=config.CONFIG['apikey'], user_agent=config.CONFIG.get('user_agent', None), delay=1)

# grab existing packages
process_packages(crawler)
