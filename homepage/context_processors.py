from django.conf import settings


def project(request):
    return {"sql_enabled": settings.DATA_SOURCE == "sqlite"}
