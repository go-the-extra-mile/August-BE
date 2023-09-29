import csv
import os
from django.core.management.base import BaseCommand, CommandError

from apps.courses.models import Building


class Command(BaseCommand):
    help = "Load a csv file of a certain model into the database"

    supported_models = ["buildings"]

    def add_arguments(self, parser):
        parser.add_argument(
            "model",
            type=str,
            help=f"What to initialize. Currently supports {self.supported_models}",
        )
        parser.add_argument("csv_file", type=str, help=f"Location of CSV file")
        parser.add_argument("--test", action='store_true', help="Only process first 3 rows(excluding header row) for testing")

    def handle(self, *args, **options):
        if options["model"] not in self.supported_models:
            raise CommandError(
                f"Unsupported model. Supported models are {self.supported_models}"
            )

        if options["model"] == "buildings":
            if len(options["csv_file"]) == 0:
                raise CommandError("A csv file must be given")

            if not os.path.isfile(options["csv_file"]):
                raise CommandError(f"File does not exist: {options['csv_file']}")

            with open(options["csv_file"], "r") as f:
                reader = csv.reader(f)
                next(reader)  # Skip the header row.
                for idx, row in enumerate(reader):
                    if options["test"] and (idx >= 4): break
                    try:
                        _, created = Building.objects.update_or_create(
                            nickname=row[1] if row[1] else None,
                            defaults={
                                "full_name": row[0] if row[0] else None,
                                "longitude": float(row[2]) if row[2] else None,
                                "latitude": float(row[3]) if row[3] else None,
                            },
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f"Error on creating building: {row[0]} {row[1]} {row[2]} {row[3]}"
                            )
                        )
                        self.stdout.write(self.style.ERROR(e))

            self.stdout.write(self.style.SUCCESS(f"Successfully initialized buildings"))
