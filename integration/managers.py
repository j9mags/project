from django.db.models import Q
from salesforce.backend.manager import SalesforceManager

DefaultManager = SalesforceManager


class UniversityManager(DefaultManager):

    def get_queryset(self):
        return super(UniversityManager, self).get_queryset().filter(record_type__developer_name='Hochschule')


class StudentManager(DefaultManager):

    def get_queryset(self):
        return super(StudentManager, self).get_queryset().filter(
            Q(record_type__developer_name='Sofortzahler') | (
                    Q(record_type__developer_name='UGVStudents') & Q(has_sofortzahler_contract_auto=True)))


class UGVStudentManager(DefaultManager):

    def get_queryset(self):
        return super(UGVStudentManager, self).get_queryset().filter(Q(record_type__developer_name='UGVStudents')
                                                                 & Q(has_sofortzahler_contract_auto=False))


class UGVLeadManager(DefaultManager):

    def get_queryset(self):
        return super(UGVLeadManager, self).get_queryset().filter(record_type__developer_name='UGVStudents',
                                                                 is_converted=False)


class UGVSofortzahlerManager(DefaultManager):

    def get_queryset(self):
        return super(UGVSofortzahlerManager, self).get_queryset().filter(record_type__developer_name='UGVStudents')
