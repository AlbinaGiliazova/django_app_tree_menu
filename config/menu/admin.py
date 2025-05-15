from django.contrib import admin
from .models import Menu, MenuItem

class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 1

@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ("name", "title")
    inlines = [MenuItemInline]

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("title", "menu", "parent", "order")
    list_filter = ("menu",)
    search_fields = ("title", "url", "named_url")
    ordering      = ("menu","parent_id","order")
