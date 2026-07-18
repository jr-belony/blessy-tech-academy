from django.apps import AppConfig


class AcademieConfig(AppConfig):
    name = 'academie'

    def ready(self):
        import academie.signals  # noqa