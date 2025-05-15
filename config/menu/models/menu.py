from django.db import models

from menu.constants import (MENU_NAME_MAX_LENGTH,
                            TITLE_MAX_LENGTH,
)


class Menu(models.Model):
    name = models.CharField("Имя",
                            max_length=MENU_NAME_MAX_LENGTH,
                            unique=True,
                            help_text="Используется для {% draw_menu 'name' %}")
    title = models.CharField("Заголовок",
                             max_length=TITLE_MAX_LENGTH,
                             blank=True)

    def __str__(self):
        return self.title or self.name
