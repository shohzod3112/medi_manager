from django.core.checks import register, Error
from check_licence import check_or_exit

@register()
def licence_check(app_configs, **kwargs):
    try:
        check_or_exit()
    except SystemExit:
        return [
            Error(
                "Licence validation failed",
                id="licence.E001",
            )
        ]
    return []