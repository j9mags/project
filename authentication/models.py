from collections import OrderedDict

import dateutil
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.core import exceptions
import dateutil.parser
import re

import traceback
from django.utils.translation import ugettext_lazy as _

from datetime import datetime
from datetime import timedelta
from uuid import uuid4

from authtools.models import AbstractEmailUser

from integration.models import RecordType, Account, Contact, Contract, Lead, Application

PANDAS_MISSING = False

try:
    from pandas.io import json
except ModuleNotFoundError as e:
    PANDAS_MISSING = True


class User(AbstractEmailUser):
    class Meta:
        swappable = 'AUTH_USER_MODEL'

    @property
    def is_student(self):
        return Account.students.filter(Q(unimailadresse=self.email) | (
            Q(is_person_account=True) & Q(has_sofortzahler_contract_auto=True) & Q(
                person_email=self.email))).exists()

    @property
    def is_ugv_student(self):
        return Account.ugv_students.filter(Q(unimailadresse=self.email) | (
            Q(is_person_account=True) & Q(has_sofortzahler_contract_auto=False) & Q(
                person_email=self.email))).exists()

    @property
    def is_repayer(self):
        return Account.repayers.filter(person_email=self.email).exists()

    @property
    def is_unistaff(self):
        return Contact.university_staff.filter(email=self.email).exists()

    @property
    def srecord(self):
        rc = None
        if self.is_unistaff:
            rc = Contact.university_staff.get(email=self.email)
        elif self.is_student:
            rc = Account.students.get(Q(unimailadresse=self.email) | (
                Q(is_person_account=True) & Q(has_sofortzahler_contract_auto=True) & Q(
                    person_email=self.email)))
        elif self.is_ugv_student:
            rc = Account.ugv_students.get(Q(unimailadresse=self.email) | (
                Q(is_person_account=True) & Q(has_sofortzahler_contract_auto=False) & Q(
                    person_email=self.email)))
        elif self.is_repayer:
            rc = Account.repayers.get(person_email=self.email)
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
        return self.expires_at and (self.expires_at < timezone.now())


class CsvUpload(models.Model):
    user = models.ForeignKey(User)
    upload_type = models.CharField(max_length=2)
    uuid = models.CharField(max_length=50)
    content = models.TextField(blank=True, null=True)

    expected_student_headers = ["Immatrikulationsnummer", "Nachname", "Vorname", "Geburtsdatum",
                                "Straße und Hausnummer", "PLZ", "Stadt", "universitäre E-Mail-Adresse",
                                "private E-Mail-Adresse", "Handynummer", "Studiengang"]
    # expected_courses_headers = ["Name des Studiengangs", "Regelstudienzeit (in Semestern)", "Kosten pro Semester",
    #                             "Kosten pro Monat", "Kosten pro Monat über der Regelstudienzeit",
    #                             "Immatrikulationsgebühr (einmalig)", "Auslandssemestergebühr pro Monat",
    #                             "Urlaubssemestergebühr pro Monat", "Startdatum des Studiengangs"]
    expected_application_headers = ["Nachname", "Vorname", "Biologisches Geschlecht", "Straße und Hausnummer", "PLZ",
                                    "Stadt", "Land", "Geburtsdatum", "Geburtsort", "Staatsbürgerschaft",
                                    "Kein OECD Ausweis", "Aktuelle Straße und Hausnummer", "Aktuelle PLZ ",
                                    "Aktuelle Stadt", "Aktuelles Land", "Kommunikationssprache", "Handynummer",
                                    "private E-Mail-Adresse", "Studiengang", "Vertrag", "Studienbeginn",
                                    "Hochschulstatus", "Risiko nicht bei CHANCEN eG", "Link zu weiteren Dokumenten"]

    @staticmethod
    def is_valid(data, upload_type):
        headers = {
            'ap': CsvUpload.expected_application_headers,
            'st': CsvUpload.expected_student_headers
        }.get(upload_type, ['Wrong'])
        headers_checked = 0

        for header in data.keys():
            if header not in headers:
                return False
            headers_checked += 1

        return headers_checked == len(headers)

    def parse_data(self):
        data = json.loads(self.content)
        rc = []
        i, done = 2, False

        headers = {
            'ap': CsvUpload.expected_application_headers,
            'st': CsvUpload.expected_student_headers
        }.get(self.upload_type, ['Wrong'])

        while not done:
            i += 1
            d_ = OrderedDict()
            for k in headers:
                if not str(i) in data[k]:
                    done = True
                    break
                if 'datum' in k and data[k][str(i)] is not None:
                    try:
                        d_.update({k: datetime.fromtimestamp(int(data[k][str(i)]) / 1000).date()})
                    except ValueError:
                        d_.update({k: None})
                else:
                    d_.update({k: data[k][str(i)]})
            if d_:
                rc.append(d_)
        return rc

    def process(self):
        # if self.course:
        #     rc = self._create_courses()
        # else:
        data = self.parse_data()
        row = data and data[0]

        if not row:
            return False

        rc = {
            'ap': self._create_applicants,
            'st': self._create_students,
        }.get(self.upload_type, lambda x: False)(data)

        if rc:
            self.delete()
        return rc

    def _create_students(self, data):
        if not self.user.is_unistaff:
            raise exceptions.PermissionDenied()

        if not self.content:
            raise exceptions.ObjectDoesNotExist()

        accs = []
        contacts = {}
        contracts = {}
        acc_mns = []

        acc_rt = RecordType.objects.get(sobject_type='Account', developer_name='Sofortzahler').id
        ctc_rt = RecordType.objects.get(sobject_type='Contact', developer_name='Sofortzahler').id
        ctr_id = RecordType.objects.get(sobject_type='Contract', developer_name='Sofortzahler').id

        university = self.user.srecord.account

        courses = {x.name: x for x in university.degreecourse_set.all()}

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
            # if course_name not in courses:
            #     courses.update({course_name: university.degreecourse_set.get(name=course_name)})
            course = courses.get(course_name)

            if not course:
                raise Exception()

            ctr = Contract(
                university_ref=acc.hochschule_ref,
                studiengang_ref=course,
                degree_course_fees_ref=course.active_fees,
                record_type_id=ctr_id,
                status='Deaktiviert'
            )
            contracts.update({acc.immatrikulationsnummer: ctr})

        Account.students.bulk_create(accs)

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
            print(repr(e), e)
            traceback.print_exc()
            # accounts.delete()
            for account in accounts:
                account.delete()
            return False

        try:
            Contract.objects.bulk_create(ctr_to_insert)
        except Exception as e:
            print(repr(e), e)
            traceback.print_exc()
            for account in accounts:
                account.delete()
            return False

        return True

    def _create_applicants(self, data):
        if not self.user.is_unistaff:
            raise exceptions.PermissionDenied()

        if not self.content:
            raise exceptions.ObjectDoesNotExist()
        languages = {'Deutsch': 'German', 'Englisch': 'English'}
        sex = {'weiblich': 'Female', 'männlich': 'Male', 'geschlechtsneutral': 'Third gender'}
        boolean_answer = {'Ja': True, 'Yes': True}

        university = self.user.srecord.account
        courses = {}
        contracts = {}
        for degree_course in university.degreecourse_set.all():
            courses[degree_course.name] = degree_course
            for c in degree_course.templates:
                if contracts.get(c.studiengang_ref) is None:
                    contracts.update({c.studiengang_ref: []})
                contracts.get(c.studiengang_ref).append(c)

        leads = []
        lead_rt = RecordType.objects.get(sobject_type='Lead', developer_name='UGVStudents').id

        appsByLead = {}

        for row in data:
            if not (any(row) and all(row)):
                return False

            lead = Lead()
            lead.record_type_id = lead_rt
            lead.first_name = row.get('Vorname')
            lead.last_name = row.get('Nachname')
            lead.biological_sex = sex.get(row.get('Biologisches Geschlecht'))
            lead.street = row.get('Straße und Hausnummer')
            lead.postal_code = row.get('PLZ')
            lead.city = row.get('Stadt')
            lead.country_0 = row.get('Land')
            lead.country = row.get('Land')
            lead.date_of_birth = row.get('Geburtsdatum')
            lead.place_of_birth = row.get('Geburtsort')
            lead.citizenship_new = row.get('Staatsbürgerschaft')
            lead.no_oecdpassport = boolean_answer.get(row.get('Kein OECD Ausweis'), False)

            lead.postal_street = row.get('Aktuelle Straße und Hausnummer')
            lead.postal_code_0 = row.get('Aktuelle PLZ ')
            lead.postal_city = row.get('Aktuelle Stadt')
            lead.postal_country = row.get('Aktuelles Land')
            lead.kommunicationssprache = languages.get(row.get('Kommunikationssprache'))
            lead.phone = row.get('Handynummer')
            lead.email = row.get('private E-Mail-Adresse').lower() \
                if row.get('private E-Mail-Adresse') is not None else None
            lead.university_status = row.get('Hochschulstatus')
            lead.status = 'Applicant'

            lead.risk_not_with_chancen = boolean_answer.get(row.get('Risiko nicht bei CHANCEN eG'), False)
            lead.link_to_further_documents = row.get('Link zu weiteren Dokumenten')

            lead.confirmed_by_university = True
            lead.uploaded_via_portal_trig = True
            leads.append(lead)

            app = Application()
            app.hochschule_ref = university
            app.studiengang_ref = courses.get(row.get('Studiengang'), None)
            rep = {
                'Januar': 'January',
                'Februar': 'February',
                'März': 'March',
                'April': 'April',
                'Mai': 'May',
                'Juni': 'June',
                'Juli': 'July',
                'August': 'August',
                'September': 'September',
                'Oktober': 'October',
                'November': 'November',
                'Dezember': 'December'
            }

            rep = dict((re.escape(k), v) for k, v in rep.items())
            pattern = re.compile("|".join(rep.keys()))
            app.start_of_study_trig = pattern.sub(lambda m: rep[re.escape(m.group(0))], row.get('Studienbeginn'))
            start_of_study = dateutil.parser.parse('1st ' + app.start_of_study_trig).date()
            candidates = [
                c for c in contracts.get(app.studiengang_ref)
                if c.application_form_display_name == row.get('Vertrag') and c.valid_from < start_of_study
            ]
            if candidates:
                app.contract_ref = candidates[len(candidates) - 1]
            if app.studiengang_ref is not None and app.contract_ref is None:
                raise Exception(_('No valid contract found. Please check the spelling.'))

            app.confirmed_by_university = True
            appsByLead.update({lead.email: app})

        Lead.objects.bulk_create(leads)
        leads = Lead.ugv_students.filter(email__in=appsByLead.keys())

        for lead in leads:
            appsByLead.get(lead.email).lead_ref = lead
        Application.objects.bulk_create(appsByLead.values())

        return True

    # def _create_courses(self):
    #     if not self.user.is_unistaff:
    #         raise exceptions.PermissionDenied()
    #
    #     if not self.content:
    #         raise exceptions.ObjectDoesNotExist()
    #
    #     university = self.user.get_srecord().account
    #     courses = []
    #     courses_names = []
    #     courses_fees = {}
    #     data = self.parse_data()
    #     for row in data:
    #         if not (any(row) and all(row)):
    #             return False
    #
    #         course = DegreeCourse()
    #         course.university = university
    #         course.name = row.get('Name des Studiengangs')
    #         course.start_of_studies = row.get(
    #             'Startdatum des Studiengangs'
    #         )  # datetime.strptime(row.get('Startdatum des Studiengangs'), '%d.%m.%Y')
    #         course.standard_period_of_study = row.get('Regelstudienzeit (in Semestern)')
    #
    #         courses.append(course)
    #         courses_names.append(course.name)
    #
    #         fees = DegreeCourseFees()
    #         fees.valid_from = timezone.now()
    #         fees.cost_per_semester = row.get('Kosten pro Semester')
    #         fees.cost_per_month = row.get('Kosten pro Monat')
    #         fees.cost_per_month_beyond_standard = row.get('Kosten pro Monat über der Regelstudienzeit')
    #         fees.matriculation_fee = row.get('Immatrikulationsgebühr (einmalig)')
    #         fees.fee_semester_abroad = row.get('Auslandssemestergebühr pro Monat')
    #         fees.fee_semester_off = row.get('Urlaubssemestergebühr pro Monat')
    #
    #         courses_fees.update({course.unique_name: fees})
    #
    #     DegreeCourse.objects.bulk_create(courses)
    #
    #     sf_courses = DegreeCourse.objects.filter(university=university, name__in=courses_names)
    #     linked = 0
    #     for course in sf_courses:
    #         fee = courses_fees.get(course.unique_name)
    #         if fee is None:
    #             continue
    #         fee.degree_course_ref = course
    #         linked += 1
    #
    #     if linked != len(courses_fees):
    #         print("Mismatch .. caution")
    #
    #     DegreeCourseFees.objects.bulk_create(courses_fees.values())
    #
    #     return True
