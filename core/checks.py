from django.core.checks import register, Error
from check_licence import check_licence

@register()
def licence_check(app_configs, **kwargs):
    try:
        check_licence()
    except SystemExit:
        return [
            Error(
                "Licence validation failed",
                id="licence.E001",
            )
        ]
    return []