from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .models import *


class UniversityAccount(Account):
    class Meta:
        proxy = True

    default_record_type = RecordType.objects.get(
        sobject_type='Account', developer_name='Hochschule')


class StudentAccount(Account):
    class Meta:
        proxy = True

    default_record_type = RecordType.objects.get(
        sobject_type='Account', developer_name='Sofortzahler')


class UniversityContact(Contact):
    class Meta:
        proxy = True

    default_record_type = RecordType.objects.get(
        sobject_type='Contact', developer_name='Hochschule')


class UniversityContactInline(admin.StackedInline):
    model = UniversityContact

    fields = ('title', 'salutation', 'first_name',
              'last_name', 'email', 'mobile_phone')


@admin.register(UniversityAccount)
class UniversityAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">school</i>'

    fieldsets = (
        (None, {
            'fields': (('name', 'abwicklungsgebuhr_pro_einzug_pro_student'),)
        }),
        (_('Bank account'), {
            'fields': (('ibanhsauto', 'bichsauto'),)
        }),
        (_('Billing address'), {
            'fields': ('billing_street', ('billing_postal_code', 'billing_city', 'billing_country'))
        })
    )

    inlines = [UniversityContactInline]

    def get_queryset(self, request):
        qs = super(UniversityAdmin, self).get_queryset(request)
        return qs.filter(record_type__developer_name='Hochschule')

    def save_model(self, request, obj, form, change):
        obj.record_type = UniversityAccount.default_record_type
        super(UniversityAdmin, self).save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        contacts = formset.save(commit=False)
        for contact in contacts:
            contact.record_type = UniversityContact.default_record_type
            # contact.password_token = uuid.uuid4()
            contact.save()
        formset.save_m2m()


@admin.register(StudentAccount)
class StudentAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">person_outline</i>'

    exclude = ('record_type', 'is_deleted')

    def get_queryset(self, request):
        qs = super(StudentAdmin, self).get_queryset(request)
        return qs.filter(record_type__developer_name='Sofortzahler')

    def save_model(self, request, obj, form, change):
        obj.record_type = StudentAccount.default_record_type
        super(StudentAdmin, self).save_model(request, obj, form, change)


admin.site.register(RecordType)
