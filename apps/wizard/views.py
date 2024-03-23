from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.core.exceptions import ValidationError

from apps.wizard.serializers import WizardOpenedSectionSerializer
from apps.wizard.mixins import GenerateTimeTableMixin

import json


class GeneratedTimeTableView(GenerateTimeTableMixin, APIView):
    def get(self, request, format=None):
        opened_section_id_groups = request.data.get("groups", None)
        options = request.data.get("options", None)

        try:
            if opened_section_id_groups is None:
                raise ValidationError("groups are required")
            if options is None:
                raise ValidationError("options are required")
        except ValidationError as e:
            return Response(data={"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        timetables = self.get_timetables(opened_section_id_groups, options)

        res = []
        for table in timetables:
            res.append(WizardOpenedSectionSerializer(table, many=True).data)

        return Response(res)

    def post(self, request, format=None):
        return self.get(request, format)


class GeneratedTimeTableCountView(GenerateTimeTableMixin, APIView):
    def get(self, request, format=None):
        opened_section_id_groups = request.data.get("groups", None)
        options = request.data.get("options", None)

        try:
            if opened_section_id_groups is None:
                raise ValidationError("groups are required")
            if options is None:
                raise ValidationError("options are required")
        except ValidationError as e:
            return Response(data={"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        cnt = self.get_timetables_count(opened_section_id_groups, options)

        return Response(cnt)

    def post(self, request, format=None):
        return self.get(request, format)


class GeneratedTimeTableTestView(APIView):
    test_request = None

    def __init__(self):
        super().__init__()
        with open("test/request.json") as f:
            self.test_request = json.load(f)

    def get(self, request):
        for key, val in self.test_request.items():
            request.data[key] = val

        test_view = GeneratedTimeTableView()
        return test_view.get(request)


class GeneratedTimeTableCountTestView(APIView):
    test_request = None

    def __init__(self):
        super().__init__()
        with open("test/request.json") as f:
            self.test_request = json.load(f)

    def get(self, request):
        for key, val in self.test_request.items():
            request.data[key] = val

        test_view = GeneratedTimeTableCountView()
        return test_view.get(request)
