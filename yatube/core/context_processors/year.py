import datetime
today = datetime.date.today()


def year(request):
    """Добавляет переменную с текущим годом."""
    return {
        'year': today.year,
    }
