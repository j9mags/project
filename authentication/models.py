from django.db import models
from django.utils import timezone
from django.core import exceptions
from django.contrib.auth import get_user_model

from datetime import datetime
from datetime import timedelta
from uuid import uuid4

from authtools.models import AbstractEmailUser

from integration.models import RecordType, Account, Contact, Contract, DegreeCourse

import csv


class User(AbstractEmailUser):

    class Meta:
        swappable = 'AUTH_USER_MODEL'

    def is_student(self):
        return Account.students.filter(unimailadresse=self.email).exists()

    def is_unistaff(self):
        return Contact.university_staff.filter(email=self.email).exists()

    def get_srecord(self):
        rc = None
        if self.is_unistaff():
            rc = Contact.university_staff.get(email=self.email)
        elif self.is_student():
            rc = Account.students.get(unimailadresse=self.email)
        return rc

    def create_token(self, token=None, hours=96):
        token = str(token or uuid4())
        exipiry_date = timezone.now() + timedelta(hours=hours)

        pt = self.perishabletoken_set.create(token=token, expires_at=exipiry_date)

        return pt


class PerishableToken(models.Model):
    user = models.ForeignKey(User)

    token = models.CharField(max_length=50)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return self.expires_at < timezone.now()


class CsvUpload(models.Model):
    user = models.ForeignKey(User)
    course = models.CharField(max_length=18, null=True, blank=True)
    uuid = models.CharField(max_length=50)
    content = models.TextField(blank=True, null=True)

    def __str__(self):
        return "{course} by {user}".format(course=self.course, user=self.user)

    def get_data(self, page):
        min = (page - 1) * 20
        max = page * 20
        data = self.content.splitlines()
        lines = [data.pop(0)] + data[min + 1: max + 1]
        return csv.DictReader(lines, delimiter=";")

    def has_more_data(self, page):
        data = self.content.split('\n')
        max = page * 20

        return len(data) > max + 2

    def process(self):
        if self.course:
            self._create_students()
        else:
            self._create_courses()

        self.delete()

    def _create_students(self):
        if not self.user.is_unistaff:
            raise exceptions.PermissionDenied()

        if not self.content:
            raise exceptions.ObjectDoesNotExist()

        lines = self.content.splitlines()

        accs = []
        contacts = {}
        contracts = {}
        acc_mns = []

        acc_rt = RecordType.objects.get(sobject_type='Account', developer_name='Sofortzahler').id
        ctc_rt = RecordType.objects.get(sobject_type='Contact', developer_name='Sofortzahler').id
        ctr_id = RecordType.objects.get(sobject_type='Contract', developer_name='Sofortzahler').id

        university = self.user.get_srecord().account
        course = university.degreecourse_set.get(pk=self.course)

        reader = csv.DictReader(lines, delimiter=";")
        desc_skipped = False
        for row in reader:
            if not desc_skipped:
                desc_skipped = True
                continue

            acc = Account()
            acc.record_type_id = acc_rt
            acc.hochschule_ref = university

            acc.billing_street = row.get('Adresse')
            acc.billing_postal_code = row.get('PLZ')
            acc.billing_city = row.get('Stadt')

            acc.name = "{Vorname} {Name}".format(**row)
            acc.immatrikulationsnummer = row.get('Immatrikulationsnummer')
            acc.geburtsdatum = datetime.strptime(row.get('Geburtsdatum'), '%d.%m.%Y')
            acc.unimailadresse = row.get('Unimailadresse')
            acc.status = 'Immatrikuliert'

            accs.append(acc)
            acc_mns.append(acc.immatrikulationsnummer)

            ctc = Contact(
                last_name=row.get('Name'),
                first_name=row.get('Vorname'),
                email=row.get('private Emailadresse'),
                mobile_phone=row.get('Handynummer'),
                mailing_street=acc.billing_street,
                mailing_city=acc.billing_city,
                mailing_postal_code=acc.billing_postal_code,
                record_type_id=ctc_rt,
                student_contact=True,
            )
            contacts.update({acc.immatrikulationsnummer: ctc})

            ctr = Contract(
                university_ref=acc.hochschule_ref,
                studiengang_ref=course,
                record_type_id=ctr_id,
            )
            contracts.update({acc.immatrikulationsnummer: ctr})

        Account.objects.bulk_create(accs)

        ctc_to_insert = []
        ctr_to_insert = []
        accounts = Account.students.filter(immatrikulationsnummer__in=acc_mns, hochschule_ref=university)
        for acc in accounts:
            ctc = contacts[acc.immatrikulationsnummer]
            ctc.account = acc
            ctc_to_insert.append(ctc)

            ctr = contracts[acc.immatrikulationsnummer]
            ctr.account = acc
            ctr_to_insert.append(ctr)

        Contact.objects.bulk_create(ctc_to_insert)
        Contract.objects.bulk_create(ctr_to_insert)

    def _create_courses(self):
        if not self.user.is_unistaff:
            raise exceptions.PermissionDenied()

        if not self.content:
            raise exceptions.ObjectDoesNotExist()

        university = self.user.get_srecord().account
        courses = []
        lines = self.content.splitlines()
        reader = csv.DictReader(lines, delimiter=";")
        desc_skipped = False
        for row in reader:
            if not desc_skipped:
                desc_skipped = True
                continue

            course = DegreeCourse()
            course.university = university
            course.name = row.get('Studiengang Name')
            course.standard_period_of_study = row.get('Standard Study Period')
            course.cost_per_semester = row.get('Cost per Semester')
            course.cost_per_month = row.get('Cost per Month')
            course.cost_per_month_beyond_standard = row.get('Cost per Month beyond Standard Study Period')
            course.matriculation_fee = row.get('Matriculation Fee')
            course.start_of_studies_month = row.get('Starting Month of Studies')
            course.start_of_studies = row.get('Start of Studies')
            course.fee_semester_abroad = row.get('Fee Semester abroad')
            course.fee_semester_off = row.get('Fee Semester off')
            course.start_summer_semester = row.get('Starting Month Summer Semester')
            course.start_winter_semester = row.get('Starting Month Winter Semester')

            courses.append(course)
        DegreeCourse.objects.bulk_create(courses)
