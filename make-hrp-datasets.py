import config
import ckanapi, datetime, json, logging, requests, urllib

PLANS_URL = "https://api.hpc.tools/v2/public/plan"
CKAN_PATTERN = "hrp-projects-{iso3}"
HXL_PATTERN = "https://proxy.hxlstandard.org/data/93fb54.csv?url={api_url}"
API_PATTERN = "https://api.hpc.tools/v2/public/project/search?planCodes={code}&excludeFields=locations,governingEntities,targets"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HPC projects")



########################################################################
# Global variables
########################################################################

plans_data = dict()
""" Indexed by ISO3 code """

countries_data = dict()
""" Information about countries found """

dataset_date = "01/01/2015-12/31/{}".format(datetime.date.today().year)
""" The dataset goes to the end of the current year """



########################################################################
# Functions
########################################################################

def scan_plans ():
    """ Scan all of the plans current on hpc.tools and sort into countries
    Include only plans from 2015 or later

    Side effect: Uses global variables plans_data and countries_data
    """

    with requests.get(PLANS_URL) as response:
        data = response.json()['data']
        for plan in data:

            # skip if it's not an HPC project
            if not plan['planVersion'].get('isForHPCProjects'):
                continue

            # skip if there's no country ISO3
            iso3 = None
            for location in plan["locations"]:
                if location.get("adminLevel") == 0:
                    iso3 = location.get("iso3")
                    if iso3 not in countries_data:
                        countries_data[iso3] = location.get("name")
                    break
            if iso3 is None:
                continue

            # skip if it's from before 2015
            has_recent = False
            for year in plan["years"]:
                if "year" in year and int(year["year"]) >= 2015:
                    has_recent = True
            if not has_recent:
                continue

            # OK, this plan is a keeper
            if iso3 not in plans_data:
                plans_data[iso3] = list()
            plans_data[iso3].append({
                "code": plan['planVersion'].get('code'),
                "name": plan['planVersion'].get('name'),
                "start": plan['planVersion'].get('startDate'),
                "end": plan['planVersion'].get('endDate'),
                "type": plan['categories'][0].get('name'),
            })


def make_dataset (iso3, plans):
    """ Create or replace the HDX dataset for the country """

    dataset_id = CKAN_PATTERN.format(iso3=iso3.lower())
    country_name = countries_data[iso3]

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
        ],
        "groups": [
            {"name": iso3}
        ],
        "has_quickcharts": True,
        "owner_org": "ocha-fts",
        "name": dataset_id,
        "notes": "Projects proposed, in progress, or completed as part of the annual {name} Humanitarian Response Plans (HRPs) or other Humanitarian Programme Cycle plans. The original data is available on https://hpc.tools\r\n\r\nNote that some projects are not publicly listed, due to security or personal-privacy concerns.".format(
            name=country_name
        ),
        "title": "Humanitarian Programme Cycle projects for {name}".format(
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
    logger.info("Creating dataset for %s", iso3)
    package = make_dataset(iso3, plans_data[iso3])
    save_dataset(ckan, package)

exit(0)
    
