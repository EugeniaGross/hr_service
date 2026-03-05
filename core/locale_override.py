from django.conf.locale.ru import formats as ru_formats

# Шаблоны отображения
ru_formats.DATE_FORMAT = "d/m/Y"
ru_formats.DATETIME_FORMAT = "d/m/Y H:i"
ru_formats.SHORT_DATE_FORMAT = "d/m/Y"
ru_formats.SHORT_DATETIME_FORMAT = "d/m/Y H:i"

# Форматы ввода
ru_formats.DATE_INPUT_FORMATS = ["%d/%m/%Y", "%m/%Y"]
ru_formats.DATETIME_INPUT_FORMATS = ["%d/%m/%Y %H:%M"]
ru_formats.YEAR_MONTH_FORMAT = "m/Y"
