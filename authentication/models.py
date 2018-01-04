from collections import OrderedDict

from django.db import models
from django.utils import timezone
from django.core import exceptions

from datetime import datetime
from datetime import timedelta
from uuid import uuid4

from authtools.models import AbstractEmailUser
from pandas.io import json

from integration.models import RecordType, Account, Contact, Contract, DegreeCourse, DegreeCourseFees


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
    course = models.BooleanField()
    uuid = models.CharField(max_length=50)
    content = models.TextField(blank=True, null=True)

    expected_student_headers = ["Immatrikulationsnummer", "Nachname", "Vorname", "Geburtsdatum",
                                "Straße und Hausnummer", "PLZ", "Stadt", "universitäre E-Mail-Adresse",
                                "private E-Mail-Adresse", "Handynummer", "Studiengang"]
    expected_courses_headers = ["Name des Studiengangs", "Regelstudienzeit (in Semestern)", "Kosten pro Semester",
                                "Kosten pro Monat", "Kosten pro Monat über der Regelstudienzeit",
                                "Immatrikulationsgebühr (einmalig)", "Auslandssemestergebühr pro Monat",
                                "Urlaubssemestergebühr pro Monat", "Startdatum des Studiengangs"]

    def __str__(self):
        return "{course} by {user}".format(course=self.course, user=self.user)

    @staticmethod
    def is_valid(data, is_course):
        headers = CsvUpload.expected_courses_headers if is_course else CsvUpload.expected_student_headers
        headers_checked = 0

        for header in data.keys():
            if header not in headers:
                return False
            headers_checked += 1

        return headers_checked == len(headers)

    def parse_data(self):
        data = json.loads(self.content)
        rc = []
        i, done = 1, False
        headers = CsvUpload.expected_courses_headers if self.course else CsvUpload.expected_student_headers

        while not done:
            i += 1
            d_ = OrderedDict()
            for k in headers:
                if not str(i) in data[k]:
                    done = True
                    break
                if 'datum' in k:
                    d_.update({k: datetime.fromtimestamp(int(data[k][str(i)]) / 1000).date()})
                else:
                    d_.update({k: data[k][str(i)]})
            if d_:
                rc.append(d_)
        return rc

    def process(self):
        if self.course:
            rc = self._create_courses()
        else:
            rc = self._create_students()
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
        # course = university.degreecourse_set.get(pk=self.course)
        courses = {}

        for row in data:
            if not (any(row) and all(row)):
                return False

            acc = Account()
            acc.record_type_id = acc_rt
            acc.hochschule_ref = university

            acc.billing_street = row.get('Straße und Hausnummer')
            acc.billing_postal_code = row.get('PLZ')
            acc.billing_city = row.get('Stadt')

            acc.name = "{Vorname} {Nachname}".format(**row)
            acc.immatrikulationsnummer = row.get('Immatrikulationsnummer')
            acc.geburtsdatum = row.get('Geburtsdatum')  # datetime.strptime(row.get('Geburtsdatum'), '%d.%m.%Y')
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

            course_name = row.get('Studiengang')
            if course_name not in courses:
                courses.update({course_name: university.degreecourse_set.get(name_studiengang_auto=course_name)})
            course = courses.get(course_name)

            if not course:
                raise Exception()

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
            for account in accounts:
                account.delete()
            return False

        return True

    def _create_courses(self):
        if not self.user.is_unistaff:
            raise exceptions.PermissionDenied()

        if not self.content:
            raise exceptions.ObjectDoesNotExist()

        university = self.user.get_srecord().account
        courses = []
        courses_names = []
        courses_fees = {}
        data = self.parse_data()
        for row in data:
            if not (any(row) and all(row)):
                return False

            course = DegreeCourse()
            course.university = university
            course.name = row.get('Name des Studiengangs')
            course.start_of_studies = row.get('Startdatum des Studiengangs')  # datetime.strptime(row.get('Startdatum des Studiengangs'), '%d.%m.%Y')
            course.standard_period_of_study = row.get('Regelstudienzeit (in Semestern)')

            courses.append(course)
            courses_names.append(course.name)

            fees = DegreeCourseFees()

            fees.cost_per_semester = row.get('Kosten pro Semester')
            fees.cost_per_month = row.get('Kosten pro Monat')
            fees.cost_per_month_beyond_standard = row.get('Kosten pro Monat über der Regelstudienzeit')
            fees.matriculation_fee = row.get('Immatrikulationsgebühr (einmalig)')
            fees.fee_semester_abroad = row.get('Auslandssemestergebühr pro Monat')
            fees.fee_semester_off = row.get('Urlaubssemestergebühr pro Monat')

            courses_fees.update({course.unique_name: fees})

        DegreeCourse.objects.bulk_create(courses)

        sf_courses = DegreeCourse.objects.filter(university=university, name__in=courses_names)
        linked = 0
        for course in sf_courses:
            fee = courses_fees.get(course.unique_name)
            if fee is None:
                continue
            fee.degree_course_ref = course
            linked += 1

        if linked != len(courses_fees):
            print("Mismatch .. caution")

        DegreeCourseFees.objects.bulk_create(courses_fees.values())

        return True
