from django.db.models import Q
from salesforce.backend.manager import SalesforceManager


DefaultManager = SalesforceManager


class UniversityManager(DefaultManager):

    def get_queryset(self):
        return super(UniversityManager, self).get_queryset().filter(record_type__developer_name='Hochschule')


class StudentManager(DefaultManager):

    BANNED_FIELDS = ['cspassword_token_pc', 'cspassword_time_pc', 'cancel_bank_account_pc']

    def bulk_create(self, objs, batch_size=None):
        fields = []
        orig = self.model._meta.fields
        for f in self.model._meta.fields:
            if f.name not in StudentManager.BANNED_FIELDS:
                fields.append(f)

        rc = super(StudentManager, self).bulk_create(objs, batch_size)

        self.model._meta.fields = orig
        return rc

    def get_queryset(self):
        return super(StudentManager, self).get_queryset().filter(
            Q(record_type__developer_name='Sofortzahler') | (
                Q(record_type__developer_name='UGVStudents') & Q(has_sofortzahler_contract_auto=True)))


class UGVStudentManager(DefaultManager):

    def get_queryset(self):
        return super(UGVStudentManager, self).get_queryset().filter(
            Q(record_type__developer_name='UGVStudents') & Q(has_sofortzahler_contract_auto=False))


class RepayerManager(DefaultManager):

    def get_queryset(self):
        return super(RepayerManager, self).get_queryset().filter(record_type__developer_name='Ruckzahler')


class UGVLeadManager(DefaultManager):

    def get_queryset(self):
        return super(UGVLeadManager, self).get_queryset().filter(record_type__developer_name='UGVStudents',
                                                                 is_converted=False)


class UGVSofortzahlerManager(DefaultManager):

    def get_queryset(self):
        return super(UGVSofortzahlerManager, self).get_queryset().filter(record_type__developer_name='UGVStudents')
