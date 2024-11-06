""" Create or update HRP projects datasets for HDX

Requires Python3
"""

import config
import ckanapi, ckancrawler, datetime, json, logging, re, requests, urllib, sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("make-hrp-datasets")



########################################################################
# Constants
########################################################################

CKAN_PATTERN = "hrp-projects-{iso3}"

HXL_PATTERN = "https://proxy.hxlstandard.org/data/download/{code}-{iso3}-projects.csv?url={api_url}&tagger-match-all=on&tagger-01-header=name&tagger-01-tag=%23activity%2Bname&tagger-02-header=versioncode&tagger-02-tag=%23activity%2Bcode%2Bv_hpc&tagger-03-header=currentrequestedfunds&tagger-03-tag=%23value%2Brequested%2Busd&tagger-05-header=objective&tagger-05-tag=%23description%2Bobjective&tagger-06-header=partners&tagger-06-tag=%23org%2Bimpl%2Bname%2Blist&tagger-07-header=startdate&tagger-07-tag=%23date%2Bstart&tagger-08-header=enddate&tagger-08-tag=%23date%2Bend&tagger-09-header=governingEntities&tagger-09-tag=%23sector%2Bcluster%2Blocal%2Bname&tagger-17-header=globalclusters&tagger-17-tag=%23sector%2Bcluster%2Bglobal%2Bname&tagger-18-header=organizations&tagger-18-tag=%23org%2Bprog%2Bname&tagger-19-header=plans&tagger-19-tag=%23response%2Bplan%2Bname&header-row=1&filter01=cut&cut-skip-untagged01=on&filter02=add&add-tag02=%23response%2Bplan%2Bcode&add-value02=%7B%7B%23response%2Bplan%2Bname%7D%7D&add-header02=Response+plan+code&filter03=jsonpath&jsonpath-path03=$%5B0%5D.name&jsonpath-patterns03=%23*%2Bname&filter04=jsonpath&jsonpath-path04=$%5B0%5D.code&jsonpath-patterns04=%23*%2Bcode&filter05=clean&clean-date-tags05=%23date&_gl=1*1pie5e1*_ga*MTI1MTE3OTIzNy4xNjk1OTA2MTk3*_ga_E60ZNX2F68*MTY5NjUxMTk5Mi43LjEuMTY5NjUxMjAwMC41Mi4wLjA."

API_PATTERN = "https://api.hpc.tools/v2/public/project/search?planCodes={code}&excludeFields=location,governingEntities,targets&limit=100000"


########################################################################
# Global variables
########################################################################

dataset_date = "[{}-01-01T00:00:00 TO *]".format(config.CONFIG['cutoff_year'], datetime.date.today().year)
""" The dataset goes to the end of the current year """



########################################################################
# Functions
########################################################################

def get_existing_packages(crawler):
    """ Read a dict of existing packages """

    logger.info("Reading existing packages")

    packages = {}

    for package in crawler.packages(fq='organization:ocha-fts humanitarian response plan'):
        name = package['name']
        if re.match(r'^hrp-projects-[a-z]{3}$', name):
            packages[name] = package
        

    return packages

def make_dataset (iso3, plans, country_name):
    """ Create or replace the HDX dataset for the country """

    dataset_id = CKAN_PATTERN.format(iso3=iso3.lower())
    country_name = re.sub(", .*$", "", country_name) # remove any extra stuff

    # Fill in full CKAN package except for resources
    package = {
        "data_update_frequency": "0",
        "license_title": "Creative Commons Attribution for Intergovernmental Organisations",
        "maintainer": "7ae95211-71dd-484e-8538-2c625315eb56",
        "private": False,
        "dataset_date": dataset_date,
        "caveats": "1. Includes only projects registered as part of the Humanitarian Programme Cycle.\r\n2. Some projects are excluded for protection or personal-privacy reasons.\r\n3. For multi-country response plans, _all_ projects are included, and some might not apply to {name}.".format(name=country_name),
        "subnational": "0",
        "methodology": "Registry",
        "license_id": "cc-by-igo",
        "resources": [],
        "dataset_preview": "first_resource",
        "dataset_source": "HPC Tools",
        "tags": [
            {
                "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                "name": "humanitarian response plan-hrp",
            },
            {
                "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                "name": "hxl",
            },
            {
                "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                "name": "who is doing what and where-3w-4w-5w",
            },
        ],
        "groups": [
            {"name": iso3.lower()}
        ],
        "has_quickcharts": True,
        "owner_org": "ocha-fts",
        "name": dataset_id,
        "notes": "Projects proposed, in progress, or completed as part of the annual {name} Humanitarian Response Plans (HRPs) or other Humanitarian Programme Cycle plans. The original data is available on https://hpc.tools\r\n\r\n**Important:** some projects in {name} might be missing, and others might not apply specifically to {name}. See _Caveats_ under the _Metadata_ tab.".format(
            name=country_name
        ),
        "title": "Humanitarian Response Plan projects for {name}".format(
            name=country_name
        )
    }

    # Add two resources (HXL and JSON) for each plan specified
    for plan in sorted(plans, key=lambda plan: plan["start"], reverse=True):
        api_url = API_PATTERN.format(code=plan['code'])
        hxl_url = HXL_PATTERN.format(code=plan['code'].lower(), iso3=iso3.lower(), api_url=urllib.parse.quote_plus(api_url))
        resource = {
            "name": "{code}-{iso3}-projects.csv".format(code=plan['code'].lower(), iso3=iso3.lower()),
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
            "name": "{code}-{iso3}-projects.json".format(code=plan['code'].lower(), iso3=iso3.lower()),
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


def save_dataset (ckan, package, existing_package):
    """ Create or update the dataset on HDX """

    # easy case: the dataset doesn't exist yet
    if existing_package is None:
        logger.info("Trying to create package %s", package['name'])
        ckan.call_action('package_create', package)
        add_quickcharts(crawler.ckan, package['name'])
        logger.info("Created new dataset %s", package['name'])
        return

    # compare resources
    existing_resources = set()
    new_resources = set()

    for resource in package['resources']:
        existing_resources.add(resource['url'])
    for resource in existing_package['resources']:
        new_resources.add(resource['url'])

    # if no change, then no update
    if existing_resources == new_resources:
        logger.info("No changes to dataset %s", package['name'])
        return

    # otherwise, update the existing package with the new resources
    existing_package['resources'] = package['resources']
    ckan.call_action('package_update', existing_package)
    add_quickcharts(crawler.ckan, package['name'])
    logger.info("Updated existing dataset %s", package['name'])
    

def add_quickcharts (ckan, package_id):
    """ Add Quick Charts to an HRP Projects dataset """
    
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

if len(sys.argv) != 2:
    print("Usage: make-hrp-datasets.py <json-scan-file>")
    sys.exit(2)

with open(sys.argv[1], 'r') as input:
    data = json.load(input)

# Open a CKAN API connection
crawler = ckancrawler.Crawler(config.CONFIG['ckanurl'], apikey=config.CONFIG['apikey'], user_agent=config.CONFIG.get('user_agent', None), delay=0)

# grab existing packages
existing_packages = get_existing_packages(crawler)
print([key for key in existing_packages], file=sys.stderr)

# Iterate through the countries with plans
for iso3 in data['plans']:

    # make a new template package for comparison
    package = make_dataset(iso3, data['plans'][iso3], data['countries'][iso3])

    # create or update only if appropriate
    save_dataset(crawler.ckan, package, existing_packages.get(package['name']))

    # remove the package from the existing list (it's updated)
    if package['name'] in existing_packages:
        del existing_packages[package['name']]

# Clean up empty datasets
for name in existing_packages:
    crawler.ckan.action.package_delete(id=name)
    logger.info("Deleted stale dataset %s", name)

exit(0)

