from django import forms
from django.contrib import admin
from django.db import models as django
from django.utils.text import Truncator
from django.utils.html import mark_safe, format_html

from . import models


class CountryTabularInline(admin.TabularInline):
    fields = ('code', 'name', )
    model = models.Country

    class CountryInlineFormset(forms.models.BaseInlineFormSet):
        def clean(self):
            for form_data in self.cleaned_data:
                code = form_data['code']
                if len(code) < 2:
                    raise forms.ValidationError('One of the countries code is invalid')
                return self.cleaned_data

    formset = CountryInlineFormset


class CityStackedInline(admin.TabularInline):
    model = models.City
    readonly_fields = ('wiki', )

    wiki_link_template = "<a href='https://en.wikipedia.org/wiki/{}' target='_blank'>" \
                         " <i style='padding-left:20px;margin-top:15px' class='material-icons left'>search</i>" \
                         "</a>"

    def wiki(self, city):
        if city.id:
            return mark_safe(self.wiki_link_template.format(city.name))
        return ""


class SeaStackedInline(admin.StackedInline):
    extra = 0
    fields = ('name', 'area', 'avg_depth', 'max_depth')
    model = models.Sea
    readonly_fields = ('avg_depth', 'max_depth')

    class SeaInlineFormset(forms.models.BaseInlineFormSet):
        def clean(self):
            for form_data in self.cleaned_data:
                name = form_data['name']
                if len(name) < 2:
                    raise forms.ValidationError('One of the seas name is too short')
                return self.cleaned_data

    formset = SeaInlineFormset


@admin.register(models.Ocean)
class OceanAdmin(admin.ModelAdmin):
    icon = '<i class="fa fa-tint"></i>'
    actions = None
    exclude = ('area', )
    readonly_fields = ('map', )
    inlines = [SeaStackedInline]
    list_display = ('name', 'area', 'short_description', 'map',)
    prepopulated_fields = {'slug': ('name', )}

    def map(self, ocean):
        if ocean.map_url:
            return format_html('<div class="col s12 center-align"><img src="{}" width="200" /></div>', ocean.map_url)
        return ""

    def short_description(self, ocean):
        return Truncator(ocean.description).words(100, truncate=' ...')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(models.Sea)
class SeaAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">bubble_chart</i>'
    fields = (('name', 'parent'),
              'ocean',
              ('area', 'avg_depth', 'max_depth'),
              'basin_countries')
    filter_horizontal = ('basin_countries', )
    list_display = ('name', 'parent', 'ocean', 'sea_area', )
    list_filter = ('parent', 'ocean', )

    def sea_area(self, sea):
        return None if sea.area == 0 else sea.area
    sea_area.empty_value_display = '?'


@admin.register(models.Continent)
class ContinentAdmin(admin.ModelAdmin):
    icon = '<i class="fa fa-globe"></i>'
    actions_selection_counter = False
    fieldsets = (
        (None, {
            'fields': ('name',)}),
        ('Details', {
            'fields': ('area', ('oceans', 'hemisphere'),
                       ('population', 'population_density'))}),
        ('Fun facts', {
            'fields': ('largest_country', 'biggest_mountain',
                       ('biggest_city', 'longest_river', ))})
    )
    inlines = [CountryTabularInline]
    list_display = (
        'name', 'surrounded_oceans', 'countries_count',
        'area', 'population', )
    list_filter = ('oceans', )
    ordering = ['population']
    raw_id_fields = ('oceans', )
    readonly_fields = ('biggest_city', 'longest_river', )

    def surrounded_oceans(self, contintent):
        return ', '.join(ocean.name for ocean in contintent.oceans.all())

    def countries_count(self, contintent):
        return contintent.countries.count()


class CountryForm(forms.ModelForm):
    class Meta:
        model = models.Country
        fields = '__all__'


@admin.register(models.Country)
class CountryAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">flag</i>'
    date_hierarchy = 'independence_day'
    form = CountryForm
    inlines = [CityStackedInline]
    list_display = (
        'tld', 'name', 'continent',
        'became_independent_in_20_century',
        'gay_friendly')
    list_display_links = ('tld', 'name', )
    list_filter = ('continent', )
    list_per_page = 50
    list_select_related = ('continent', )
    search_fields = ('code', 'name', )

    def tld(self, country):
        return '.' + country.code.lower()
    tld.short_description = 'TLD'
    tld.admin_order_field = 'code'

    def became_independent_in_20_century(self, country):
        if country.independence_day:
            return 1900 <= country.independence_day.year <= 2000
    became_independent_in_20_century.boolean = True


@admin.register(models.City)
class CityAdmin(admin.ModelAdmin):
    icon = '<i class="fa fa-building"></i>'
    list_display = ('name', 'country', 'population')
    list_filter = ('is_capital', 'country', (
        'country__continent', admin.RelatedOnlyFieldListFilter))
    search_fields = ('name', )
    formfield_overrides = {
        django.IntegerField: {
            'widget': forms.NumberInput(attrs={'min': 0})},
    }
    show_full_result_count = False
    raw_id_fields = ('country', )
    readonly_fields = ('became_independent_in_20_century', )

    def became_independent_in_20_century(self, city):
        if city.country_id is not None and city.country.independence_day:
            return 1900 <= city.country.independence_day.year <= 2000
    became_independent_in_20_century.boolean = True
