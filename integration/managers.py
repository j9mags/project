from salesforce.backend.manager import SalesforceManager


DefaultManager = SalesforceManager


class UniversityManager(DefaultManager):

    def get_queryset(self):
        return super(UniversityManager, self).get_queryset().filter(
            is_deleted=False,
            record_type__developer_name='Hochschule')


class StudentManager(DefaultManager):

    def get_queryset(self):
        return super(StudentManager, self).get_queryset().filter(
            is_deleted=False,
            record_type__developer_name='Sofortzahler')

