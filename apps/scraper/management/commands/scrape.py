import requests
from django.core.management.base import BaseCommand, CommandError
import yaml

from apps.courses.models import *
from apps.scraper.scrapers import scrapers
from apps.scraper.utils import timeit

class Command(BaseCommand):
    help = "Scrape data from each institution websites or API and populate or update our database."

    def add_arguments(self, parser):
        parser.add_argument('--config', type=str, default='scrape_config.yaml', help='A config file name')
        parser.add_argument('--test', action='store_true', help='Only scrape one available semester of one department')
        parser.add_argument('--sync', action='store_true', help='Perform synchronous scraping')

    @timeit
    def handle(self, *args, **options):
        config = options['config']
        test = options['test']
        async_scrape = not (options['sync'])

        with open(config) as f:
            y = yaml.safe_load(f)
            all_semesters = y.get('all semesters', True)
            all_institutions = y.get('all institutions', True)

            if all_semesters and all_institutions:
                for (_, scraper) in scrapers.items():
                    scraper.arun(test=test) if async_scrape else scraper.run(test=test)
            elif all_semesters and not all_institutions:
                institutions = y.get('institutions')
                for inst in institutions:
                    scraper = scrapers.get(inst)
                    scraper.arun(test=test) if async_scrape else scraper.run(test=test)
                    print(f'Institution {inst} run finished')
            elif not all_semesters and all_institutions:
                semesters = y.get('semesters')
                for (_, scraper) in scrapers.items():
                    for sem in semesters:
                        scraper.arun_semester(sem, test=test) if async_scrape else scraper.run_semester(sem, test=test)
                        print(f'Semester {sem} run finished')
            else:
                targets = y.get('targets')
                for (institution, semesters) in targets.items():
                    scraper = scrapers.get(institution)
                    for sem in semesters:
                        scraper.arun_semester(sem, test=test) if async_scrape else scraper.run_semester(sem, test=test)
                        print(f'Semester {sem} run finished')
                    print(f'Institution {institution} run finished')