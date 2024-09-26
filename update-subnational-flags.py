""" Remove subnational flag from all HRP project datasets """

from config import CONFIG
import ckancrawler, logging, re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("update-subnational-flags")

crawler = ckancrawler.Crawler(CONFIG['ckanurl'], delay=0, user_agent=CONFIG['user_agent'], apikey=CONFIG['apikey'])

for i, package in enumerate(crawler.packages(q='"humanitarian response plan projects for"')):
    if re.match(r'^hrp-projects-[a-z]{3}$', package['name']) and package['organization']['name'] == 'ocha-fts':
        logger.info("Processing %s", package['name'])
        package["subnational"] = 0
        crawler.ckan.call_action('package_update', package)


