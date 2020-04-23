""" Create or update HRP projects datasets for HDX

Requires Python3
"""

import config
import ckanapi, datetime, json, logging, re, requests, urllib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("make-hrp-datasets")



########################################################################
# Constants
########################################################################

PLANS_URL = "https://api.hpc.tools/v2/public/plan"
CKAN_PATTERN = "hrp-projects-{iso3}"
HXL_PATTERN = "https://proxy.hxlstandard.org/data/93fb54.csv?url={api_url}"
API_PATTERN = "https://api.hpc.tools/v2/public/project/search?planCodes={code}&excludeFields=locations,governingEntities,targets&limit=100000"



########################################################################
# Global variables
########################################################################

plans_data = dict()
""" Indexed by ISO3 code """

countries_data = dict()
""" Information about countries found """

dataset_date = "01/01/{}-12/31/{}".format(config.CONFIG['cutoff_year'], datetime.date.today().year)
""" The dataset goes to the end of the current year """



########################################################################
# Functions
########################################################################

def scan_plans ():
    """ Scan all of the plans current on hpc.tools and sort into countries
    Include only plans from config.CONFIG['cutoff_year'] or later

    Side effect: Uses global variables plans_data and countries_data
    """

    with requests.get(PLANS_URL) as response:
        data = response.json()['data']
        for plan in data:

            plan_code = plan['planVersion']['code']

            # skip if it's not an HPC project
            # if not plan['planVersion'].get('isForHPCProjects'):
            #     logger.info("Skipping %s (not HPC)", plan_code)
            #     continue

            # skip if there's no country ISO3
            iso3 = None
            for location in plan["locations"]:
                if location.get("adminLevel") == 0:
                    iso3 = location.get("iso3")
                    if iso3 not in countries_data:
                        countries_data[iso3] = location.get("name")
                    break
            if iso3 is None:
                logger.info("Skipping %s (no country code)", plan_code)
                continue

            # skip if it's from before the cutoff year
            has_recent = False
            for year in plan["years"]:
                if "year" in year and int(year["year"]) >= config.CONFIG['cutoff_year']:
                    has_recent = True
            if not has_recent:
                logger.info("Skipping %s (before %d)", plan_code, config.CONFIG['cutoff_year'])
                continue

            # skip if it doesn't have any projects
            with requests.get(API_PATTERN.format(code=plan_code)) as response:
                logger.info("Checking projects for %s...", plan_code)
                data = response.json()
                if len(data['data']['results']) < 1:
                    logger.info("Skipping %s (no projects)", plan_code)
                    continue

            # OK, this plan is a keeper
            if iso3 not in plans_data:
                plans_data[iso3] = list()
            plans_data[iso3].append({
                "code": plan_code,
                "name": plan['planVersion'].get('name'),
                "start": plan['planVersion'].get('startDate'),
                "end": plan['planVersion'].get('endDate'),
                "type": plan['categories'][0].get('name'),
            })


def make_dataset (iso3, plans):
    """ Create or replace the HDX dataset for the country """

    logger.info("Creating dataset for %s", iso3)

    dataset_id = CKAN_PATTERN.format(iso3=iso3.lower())
    country_name = re.sub(", .*$", "", countries_data[iso3])

    # Fill in full CKAN package except for resources
    package = {
        "data_update_frequency": "0",
        "license_title": "Creative Commons Attribution for Intergovernmental Organisations",
        "maintainer": "7ae95211-71dd-484e-8538-2c625315eb56",
        "private": False,
        "dataset_date": dataset_date,
        "caveats": "Includes only projects registered as part of the Humanitarian Programme Cycle. Some projects are excluded for protection or personal-privacy reasons.",
        "subnational": "1",
        "methodology": "Registry",
        "license_id": "cc-by-igo",
        "resources": [],
        "dataset_preview": "first_resource",
        "dataset_source": "HPC Tools",
        "tags": [
            {
                "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                "name": "activities - projects",
            },
            {
                "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                "name": "hxl",
            },
            {
                "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                "name": "who is doing what and where - 3w - 4w - 5w",
            },
        ],
        "groups": [
            {"name": iso3.lower()}
        ],
        "has_quickcharts": True,
        "owner_org": "ocha-fts",
        "name": dataset_id,
        "notes": "Projects proposed, in progress, or completed as part of the annual {name} Humanitarian Response Plans (HRPs) or other Humanitarian Programme Cycle plans. The original data is available on https://hpc.tools\r\n\r\nNote that some projects are not publicly listed, due to security or personal-privacy concerns.".format(
            name=country_name
        ),
        "title": "Humanitarian Response Plan projects for {name}".format(
            name=country_name
        )
    }

    # Add two resources (HXL and JSON) for each plan specified
    for plan in reversed(plans):
        api_url = API_PATTERN.format(code=plan['code'])
        hxl_url = HXL_PATTERN.format(api_url=urllib.parse.quote_plus(api_url))
        resource = {
            "name": "{code}-hrp-projects.csv".format(code=plan['code']),
            "description": "Projects for {name} ({type}): simplified CSV data, with HXL hashtags.".format(
                name=plan["name"],
                type=plan["type"],
            ),
            "format": "CSV",
            "mimetype": "text/csv",
            "resource_type": "api",
            "url": hxl_url,
            "url_type": "api"
        }
        package["resources"].append(resource)
        resource = {
            "name": "{code}-hrp-projects.json".format(code=plan['code']),
            "description": "Projects for {name} ({type}): original JSON, from HPC.tools".format(
                name=plan["name"],
                type=plan["type"],
            ),
            "format": "JSON",
            "mimetype": "application/json",
            "resource_type": "api",
            "url": api_url,
            "url_type": "api"
        }
        package["resources"].append(resource)

    return package


def save_dataset (ckan, package):
    """ Create or update the dataset on HDX """
    try:
        result = ckan.action.package_show(id=package['name'])
        ckan.call_action('package_update', package)
        logger.info("Updated %s...", package['name'])
    except:
        ckan.call_action('package_create', package)
        logger.info("Created %s...", package['name'])

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
ckan = ckanapi.RemoteCKAN(config.CONFIG['ckanurl'], apikey=config.CONFIG['apikey'], user_agent=config.CONFIG.get('user_agent', None))

# Scan all the plans current on hpc.tools
logger.info("Scanning plans from HPC.tools")
scan_plans()

# Iterate through the countries with plans
for iso3 in plans_data:
    package = make_dataset(iso3, plans_data[iso3])
    save_dataset(ckan, package)
    add_quickcharts(ckan, package['name'])

exit(0)
    
