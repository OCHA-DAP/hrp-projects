""" Create or update HRP projects datasets for HDX

Requires Python3
"""

import config
import json, logging, requests, sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scan-hrp-datasets")



########################################################################
# Constants
########################################################################

PLANS_URL = "https://api.hpc.tools/v2/public/plan"
API_PATTERN = "https://api.hpc.tools/v2/public/project/search?planCodes={code}&excludeFields=locations,governingEntities,targets&limit=100000"


########################################################################
# Functions
########################################################################

def scan_plans ():
    """ Scan all of the plans current on hpc.tools and sort into countries
    Include only plans from config.CONFIG['cutoff_year'] or later
    """

    plans_data = dict()
    countries_data = dict()

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
                try:
                    data = response.json()
                except requests.exceptions.JSONDecodeError as e:
                    logger.error("JSON parsing error for %s", plan_code)
                    logger.exception(e)
                    continue
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

    return {
        'countries': countries_data,
        'plans': plans_data,
    }



########################################################################
# Top level
########################################################################
        
# Scan all the plans current on hpc.tools
logger.info("Scanning plans from HPC.tools")
data = scan_plans()
json.dump(data, sys.stdout, indent=4)

exit(0)
    
