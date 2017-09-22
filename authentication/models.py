from collections import OrderedDict

from django.db import models
from django.utils import timezone
from django.core import exceptions

from datetime import datetime
from datetime import timedelta
from uuid import uuid4

from authtools.models import AbstractEmailUser
from pandas.io import json

from integration.models import RecordType, Account, Contact, Contract, DegreeCourse


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

    expected_student_headers = ["Immatrikulationsnummer", "Nachname", "Vorname", "Geburtsdatum",
                                "Straße und Hausnummer", "PLZ", "Stadt", "universitäre E-Mail-Adresse",
                                "private E-Mail-Adresse", "Handynummer"]
    expected_courses_headers = ["Name des Studiengangs", "Regelstudienzeit (in Semestern)", "Kosten pro Semester",
                                "Kosten pro Monat", "Kosten pro Monat über der Regelstudienzeit",
                                "Immatrikulationsgebühr (einmalig)", "Auslandssemestergebühr pro Monat",
                                "Urlaubssemestergebühr pro Monat", "Startmonat des Studiengangs",
                                "Startdatum des Studiengangs", "Startmonat des Sommersemesters",
                                "Startmonat des Wintersemesters"]

    def __str__(self):
        return "{course} by {user}".format(course=self.course, user=self.user)

    @staticmethod
    def is_valid(data, is_course):
        headers = CsvUpload.expected_courses_headers if is_course else CsvUpload.expected_student_headers

        for header in data.keys():
            if header not in headers:
                return False

        return True

    def parse_data(self):
        data = json.loads(self.content)
        rc = []
        i, done = 0, False
        headers = CsvUpload.expected_student_headers if self.course else CsvUpload.expected_courses_headers
        while not done:
            i += 1
            d_ = OrderedDict()
            for k in headers:
                if not str(i) in data[k]:
                    done = True
                    break
                d_.update({k: data[k][str(i)]})
            if d_:
                rc.append(d_)
        return rc

    def process(self):
        if self.course:
            rc = self._create_students()
        else:
            rc = self._create_courses()
        if rc:
            self.delete()
        return rc

    def _create_students(self):
        if not self.user.is_unistaff:
            raise exceptions.PermissionDenied()

        if not self.content:
            raise exceptions.ObjectDoesNotExist()

        data = self.parse_data()
        accs = []
        contacts = {}
        contracts = {}
        acc_mns = []

        acc_rt = RecordType.objects.get(sobject_type='Account', developer_name='Sofortzahler').id
        ctc_rt = RecordType.objects.get(sobject_type='Contact', developer_name='Sofortzahler').id
        ctr_id = RecordType.objects.get(sobject_type='Contract', developer_name='Sofortzahler').id

        university = self.user.get_srecord().account
        course = university.degreecourse_set.get(pk=self.course)

        for row in data:
            if not(any(row) and all(row)):
                return False

            acc = Account()
            acc.record_type_id = acc_rt
            acc.hochschule_ref = university

            acc.billing_street = row.get('Straße und Hausnummer')
            acc.billing_postal_code = row.get('PLZ')
            acc.billing_city = row.get('Stadt')

            acc.name = "{Vorname} {Nachname}".format(**row)
            acc.immatrikulationsnummer = row.get('Immatrikulationsnummer')
            acc.geburtsdatum = datetime.strptime(row.get('Geburtsdatum'), '%d.%m.%Y')
            acc.unimailadresse = row.get('universitäre E-Mail-Adresse')
            acc.status = 'Immatrikuliert'

            accs.append(acc)
            acc_mns.append(acc.immatrikulationsnummer)

            ctc = Contact(
                last_name=row.get('Nachname'),
                first_name=row.get('Vorname'),
                email=row.get('private E-Mail-Adresse'),
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

        try:
            Contact.objects.bulk_create(ctc_to_insert)
        except Exception as e:
            print(e)
            # accounts.delete()
            for account in accounts:
                account.delete()
            return False

        try:
            Contract.objects.bulk_create(ctr_to_insert)
        except Exception as e:
            print(e)
            accounts.delete()
            return False

        return True

    def _create_courses(self):
        if not self.user.is_unistaff:
            raise exceptions.PermissionDenied()

        if not self.content:
            raise exceptions.ObjectDoesNotExist()

        university = self.user.get_srecord().account
        courses = []
        data = self.parse_data()
        for row in data:
            if not(any(row) and all(row)):
                return False

            course = DegreeCourse()
            course.university = university
            course.name = row.get('Name des Studiengangs')
            course.standard_period_of_study = row.get('Regelstudienzeit (in Semestern)')
            course.cost_per_semester = row.get('Kosten pro Semester')
            course.cost_per_month = row.get('Kosten pro Monat')
            course.cost_per_month_beyond_standard = row.get('Kosten pro Monat über der Regelstudienzeit')
            course.matriculation_fee = row.get('Immatrikulationsgebühr (einmalig)')
            course.fee_semester_abroad = row.get('Auslandssemestergebühr pro Monat')
            course.fee_semester_off = row.get('Urlaubssemestergebühr pro Monat')
            course.start_of_studies_month = row.get('Startmonat des Studiengangs')
            course.start_of_studies = datetime.strptime(row.get('Startdatum des Studiengangs'), '%d.%m.%Y')
            course.start_summer_semester = row.get('Startmonat des Sommersemesters')
            course.start_winter_semester = row.get('Startmonat des Wintersemesters')

            courses.append(course)
        DegreeCourse.objects.bulk_create(courses)
        return True
