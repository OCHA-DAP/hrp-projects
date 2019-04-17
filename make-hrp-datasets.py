import config
import ckanapi, json, pprint, urllib

CKAN_PATTERN = "hrp-projects-{iso3}"
HXL_PATTERN = "https://proxy.hxlstandard.org/data/93fb54.csv?url={api_url}"
API_PATTERN = "https://api.hpc.tools/v2/public/project/search?planCodes=H{iso3}{year}&excludeFields=locations,governingEntities,targets"

print(config.CONFIG)

# Open a CKAN API connection
ckan = ckanapi.RemoteCKAN(config.CONFIG['ckanurl'], apikey=config.CONFIG['apikey'], user_agent=config.CONFIG.get('user_agent', None))

# Load the JSON config
with open("plan-data.json", "r") as input:
    plans = json.load(input);

# Iterate through the plan configurations
for plan in plans:

    # CKAN dataset name
    dataset_id = CKAN_PATTERN.format(iso3=plan["iso3"])

    # Fill in full CKAN package except for resources
    package = {
        "data_update_frequency": "0",
        "license_title": "Creative Commons Attribution for Intergovernmental Organisations",
        "maintainer": "7ae95211-71dd-484e-8538-2c625315eb56",
        "private": False,
        "dataset_date": "01/01/2017-12/31/2019",
        "caveats": "Includes only projects registered as part of the Humanitarian Response Plan (HRP). Some projects are excluded for protection or personal-privacy reasons.",
        "subnational": "1",
        "methodology": "Registry",
        "license_id": "cc-by-igo",
        "resources": [],
        "dataset_preview": "first_resource",
        "dataset_source": "HPC Tools",
        "tags": [
            {"name": "3w"},
            {"name": "4w"},
            {"name": "finance"},
            {"name": "hxl"},
            {"name": "projects"}
        ],
        "groups": [
            {"name": plan["iso3"]}
        ],
        "has_quickcharts": True,
        "owner_org": "ocha-fts",
        "name": dataset_id,
        "notes": "Projects proposed, in progress, or completed as part of the annual {name} Humanitarian Response Plans (HRPs). The original data is available on https://hpc.tools\r\n\r\nNote that some projects are not publicly listed, due to security or personal-privacy concerns.".format(
            name=plan["name"]
        ),
        "title": "Humanitarian Response Plan projects for {name}".format(
            name=plan["name"]
        )
    }

    # Add two resources (HXL and JSON) for each year specified
    for year in sorted(plan["years"], reverse=True):
        api_url = API_PATTERN.format(
            iso3=plan["iso3"].upper(),
            year=year-2000
        )
        hxl_url = HXL_PATTERN.format(api_url=urllib.parse.quote_plus(api_url))
        resource = {
            "name": "{year}-{iso3}-hrp-projects.csv".format(
                year=year,
                iso3=plan["iso3"]
            ),
            "description": "{year} HRP projects for {name}: simplified CSV data, with HXL hashtags.".format(
                name=plan["name"],
                year=year
            ),
            "format": "CSV",
            "mimetype": "text/csv",
            "resource_type": "api",
            "url": hxl_url,
            "url_type": "api"
        }
        package["resources"].append(resource)
        resource = {
            "name": "{year}-{iso3}-hrp-projects.json".format(
                year=year,
                iso3=plan["iso3"]
            ),
            "description": "{year} HRP projects for {name}: original JSON data from https://hpc.tools".format(
                name=plan["name"],
                year=year
            ),
            "format": "JSON",
            "mimetype": "application/json",
            "resource_type": "api",
            "url": api_url,
            "url_type": "api"
        }
        package["resources"].append(resource)

    # see if the package already exists on CKAN
    try:
        result = ckan.action.package_show(id=dataset_id)
        ckan.call_action('package_update', package)
        print("Updated {}...".format(dataset_id))
    except:
        ckan.call_action('package_create', package)
        print("Created {}...".format(dataset_id))
