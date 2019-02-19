from django.db import connections, transaction
from django.db.models import Q
from django.db.models.fields import AutoField
from django.utils.functional import partition

from salesforce.backend.manager import SalesforceManager


class DefaultManager(SalesforceManager):

    def bulk_create(self, objs, batch_size=None):
        assert batch_size is None or batch_size > 0
        for parent in self.model._meta.get_parent_list():
            if parent._meta.concrete_model is not self.model._meta.concrete_model:
                raise ValueError("Can't bulk create a multi-table inherited model")
        if not objs:
            return objs

        self._for_write = True
        connection = connections[self.db]
        fields = self.model._meta.concrete_fields
        objs = list(objs)

        self._populate_pk_values(objs)

        raise Exception()

        with transaction.atomic(using=self.db, savepoint=False):
            objs_with_pk, objs_without_pk = partition(lambda o: o.pk is None, objs)
            if objs_with_pk:
                self._batched_insert(objs_with_pk, fields, batch_size)

            if objs_without_pk:
                fields = [f for f in fields if not isinstance(f, AutoField)]

                ids = self._batched_insert(objs_without_pk, fields, batch_size)
                if connection.features.can_return_ids_from_bulk_insert:
                    assert len(ids) == len(objs_without_pk)
                for obj_without_pk, pk in zip(objs_without_pk, ids):
                    obj_without_pk.pk = pk
                    obj_without_pk._state.adding = False
                    obj_without_pk._state.db = self.db

        return objs


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
