from __future__ import unicode_literals

from datetime import date

from django.contrib.auth import get_user_model
from salesforce import models
from salesforce.backend.driver import handle_api_exceptions
from django.db import connections

from . import managers


class Choices:
    Country = [('Abchasien', 'Abchasien'), ('Afghanistan', 'Afghanistan'), ('Ägypten', 'Ägypten'),
               ('Albanien', 'Albanien'), ('Algerien', 'Algerien'), ('Andorra', 'Andorra'), ('Angola', 'Angola'),
               ('Antigua und Barbuda', 'Antigua und Barbuda'), ('Äquatorialguinea', 'Äquatorialguinea'),
               ('Argentinien', 'Argentinien'), ('Armenien', 'Armenien'), ('Aserbaidschan', 'Aserbaidschan'),
               ('Äthiopien', 'Äthiopien'), ('Australien', 'Australien'), ('Bahamas', 'Bahamas'), ('Bahrain', 'Bahrain'),
               ('Bangladesch', 'Bangladesch'), ('Barbados', 'Barbados'), ('Belgien', 'Belgien'), ('Belize', 'Belize'),
               ('Benin', 'Benin'), ('Bergkarabach', 'Bergkarabach'), ('Bhutan', 'Bhutan'), ('Bolivien', 'Bolivien'),
               ('Bosnien und Herzegowina', 'Bosnien und Herzegowina'), ('Botswana', 'Botswana'),
               ('Brasilien', 'Brasilien'), ('Brunei', 'Brunei'), ('Bulgarien', 'Bulgarien'),
               ('Burkina Faso', 'Burkina Faso'), ('Burundi', 'Burundi'), ('Chile', 'Chile'),
               ('Republik China', 'Republik China'), ('Volksrepublik China', 'Volksrepublik China'),
               ('Cookinseln', 'Cookinseln'), ('Costa Rica', 'Costa Rica'), ('Dänemark', 'Dänemark'),
               ('Deutschland', 'Deutschland'), ('Dominica', 'Dominica'),
               ('Dominikanische Republik', 'Dominikanische Republik'), ('Dschibuti', 'Dschibuti'),
               ('Ecuador', 'Ecuador'), ('El Salvador', 'El Salvador'), ('Elfenbeinküste', 'Elfenbeinküste'),
               ('Eritrea', 'Eritrea'), ('Estland', 'Estland'), ('Fidschi', 'Fidschi'), ('Finnland', 'Finnland'),
               ('Frankreich', 'Frankreich'), ('Gabun', 'Gabun'), ('Gambia', 'Gambia'), ('Georgien', 'Georgien'),
               ('Ghana', 'Ghana'), ('Grenada', 'Grenada'), ('Griechenland', 'Griechenland'), ('Guatemala', 'Guatemala'),
               ('Guinea', 'Guinea'), ('Guinea-Bissau', 'Guinea-Bissau'), ('Guyana', 'Guyana'), ('Haiti', 'Haiti'),
               ('Honduras', 'Honduras'), ('Indien', 'Indien'), ('Indonesien', 'Indonesien'), ('Irak', 'Irak'),
               ('Iran', 'Iran'), ('Irland', 'Irland'), ('Island', 'Island'), ('Israel', 'Israel'),
               ('Italien', 'Italien'), ('Jamaika', 'Jamaika'), ('Japan', 'Japan'), ('Jemen', 'Jemen'),
               ('Jordanien', 'Jordanien'), ('Kambodscha', 'Kambodscha'), ('Kamerun', 'Kamerun'), ('Kanada', 'Kanada'),
               ('Kap Verde', 'Kap Verde'), ('Kasachstan', 'Kasachstan'), ('Katar', 'Katar'), ('Kenia', 'Kenia'),
               ('Kirgisistan', 'Kirgisistan'), ('Kiribati', 'Kiribati'), ('Kolumbien', 'Kolumbien'),
               ('Komoren', 'Komoren'), ('Kongo, Demokratische Republik', 'Kongo, Demokratische Republik'),
               ('Kongo, Republik', 'Kongo, Republik'), ('Korea, Nord', 'Korea, Nord'), ('Korea, Süd', 'Korea, Süd'),
               ('Kosovo', 'Kosovo'), ('Kroatien', 'Kroatien'), ('Kuba', 'Kuba'), ('Kuwait', 'Kuwait'), ('Laos', 'Laos'),
               ('Lesotho', 'Lesotho'), ('Lettland', 'Lettland'), ('Libanon', 'Libanon'), ('Liberia', 'Liberia'),
               ('Libyen', 'Libyen'), ('Liechtenstein', 'Liechtenstein'), ('Litauen', 'Litauen'),
               ('Luxemburg', 'Luxemburg'), ('Madagaskar', 'Madagaskar'), ('Malawi', 'Malawi'), ('Malaysia', 'Malaysia'),
               ('Malediven', 'Malediven'), ('Mali', 'Mali'), ('Malta', 'Malta'), ('Marokko', 'Marokko'),
               ('Marshallinseln', 'Marshallinseln'), ('Mauretanien', 'Mauretanien'), ('Mauritius', 'Mauritius'),
               ('Mazedonien', 'Mazedonien'), ('Mexiko', 'Mexiko'), ('Mikronesien', 'Mikronesien'),
               ('Moldawien', 'Moldawien'), ('Monaco', 'Monaco'), ('Mongolei', 'Mongolei'), ('Montenegro', 'Montenegro'),
               ('Mosambik', 'Mosambik'), ('Myanmar', 'Myanmar'), ('Namibia', 'Namibia'), ('Nauru', 'Nauru'),
               ('Nepal', 'Nepal'), ('Neuseeland', 'Neuseeland'), ('Nicaragua', 'Nicaragua'),
               ('Niederlande', 'Niederlande'), ('Niger', 'Niger'), ('Nigeria', 'Nigeria'), ('Niue', 'Niue'),
               ('Nordzypern', 'Nordzypern'), ('Norwegen', 'Norwegen'), ('Oman', 'Oman'), ('Österreich', 'Österreich'),
               ('Osttimor / Timor-Leste', 'Osttimor / Timor-Leste'), ('Pakistan', 'Pakistan'),
               ('Palästina', 'Palästina'), ('Palau', 'Palau'), ('Panama', 'Panama'),
               ('Papua-Neuguinea', 'Papua-Neuguinea'), ('Paraguay', 'Paraguay'), ('Peru', 'Peru'),
               ('Philippinen', 'Philippinen'), ('Polen', 'Polen'), ('Portugal', 'Portugal'), ('Ruanda', 'Ruanda'),
               ('Rumänien', 'Rumänien'), ('Russland', 'Russland'), ('Salomonen', 'Salomonen'), ('Sambia', 'Sambia'),
               ('Samoa', 'Samoa'), ('San Marino', 'San Marino'), ('São Tomé und Príncipe', 'São Tomé und Príncipe'),
               ('Saudi-Arabien', 'Saudi-Arabien'), ('Schweden', 'Schweden'), ('Schweiz', 'Schweiz'),
               ('Senegal', 'Senegal'), ('Serbien', 'Serbien'), ('Seychellen', 'Seychellen'),
               ('Sierra Leone', 'Sierra Leone'), ('Simbabwe', 'Simbabwe'), ('Singapur', 'Singapur'),
               ('Slowakei', 'Slowakei'), ('Slowenien', 'Slowenien'), ('Somalia', 'Somalia'),
               ('Somaliland', 'Somaliland'), ('Spanien', 'Spanien'), ('Sri Lanka', 'Sri Lanka'),
               ('St. Kitts und Nevis', 'St. Kitts und Nevis'), ('St. Lucia', 'St. Lucia'),
               ('St. Vincent und die Grenadinen', 'St. Vincent und die Grenadinen'), ('Südafrika', 'Südafrika'),
               ('Sudan', 'Sudan'), ('Südossetien', 'Südossetien'), ('Südsudan', 'Südsudan'), ('Suriname', 'Suriname'),
               ('Swasiland', 'Swasiland'), ('Syrien', 'Syrien'), ('Tadschikistan', 'Tadschikistan'),
               ('Tansania', 'Tansania'), ('Thailand', 'Thailand'), ('Togo', 'Togo'), ('Tonga', 'Tonga'),
               ('Transnistrien', 'Transnistrien'), ('Trinidad und Tobago', 'Trinidad und Tobago'), ('Tschad', 'Tschad'),
               ('Tschechien', 'Tschechien'), ('Tunesien', 'Tunesien'), ('Türkei', 'Türkei'),
               ('Turkmenistan', 'Turkmenistan'), ('Tuvalu', 'Tuvalu'), ('Uganda', 'Uganda'), ('Ukraine', 'Ukraine'),
               ('Ungarn', 'Ungarn'), ('Uruguay', 'Uruguay'), ('Usbekistan', 'Usbekistan'), ('Vanuatu', 'Vanuatu'),
               ('Vatikanstadt', 'Vatikanstadt'), ('Venezuela', 'Venezuela'),
               ('Vereinigte Arabische Emirate', 'Vereinigte Arabische Emirate'),
               ('Vereinigte Staaten', 'Vereinigte Staaten'), ('Vereinigtes Königreich', 'Vereinigtes Königreich'),
               ('Vietnam', 'Vietnam'), ('Weißrussland', 'Weißrussland'), ('Westsahara', 'Westsahara'),
               ('Zentral\xadafrikanische Republik', 'Zentral\xadafrikanische Republik'), ('Zypern', 'Zypern')]
    Gender = [('weiblich', 'weiblich'), ('männlich', 'männlich'), ('geschlechtsneutral', 'geschlechtsneutral')]
    Nationality = [('afghanisch', 'afghanisch'), ('ägyptisch', 'ägyptisch'), ('albanisch', 'albanisch'),
                   ('algerisch', 'algerisch'), ('andorranisch', 'andorranisch'), ('angolanisch', 'angolanisch'),
                   ('antiguanisch', 'antiguanisch'), ('äquatorialguineisch', 'äquatorialguineisch'),
                   ('argentinisch', 'argentinisch'), ('armenisch', 'armenisch'),
                   ('aserbaidschanisch', 'aserbaidschanisch'), ('äthiopisch', 'äthiopisch'),
                   ('australisch', 'australisch'), ('bahamaisch', 'bahamaisch'), ('bahrainisch', 'bahrainisch'),
                   ('bangladeschisch', 'bangladeschisch'), ('barbadisch', 'barbadisch'), ('belgisch', 'belgisch'),
                   ('belizisch', 'belizisch'), ('beninisch', 'beninisch'), ('bhutanisch', 'bhutanisch'),
                   ('bolivianisch', 'bolivianisch'), ('bosnisch-herzegowinisch', 'bosnisch-herzegowinisch'),
                   ('botsuanisch', 'botsuanisch'), ('brasilianisch', 'brasilianisch'), ('bruneiisch', 'bruneiisch'),
                   ('bulgarisch', 'bulgarisch'), ('burkinisch', 'burkinisch'), ('burundisch', 'burundisch'),
                   ('cabo-verdisch', 'cabo-verdisch'), ('chilenisch', 'chilenisch'), ('chinesisch', 'chinesisch'),
                   ('costa-ricanisch', 'costa-ricanisch'), ('ivorisch', 'ivorisch'), ('dänisch', 'dänisch'),
                   ('deutsch', 'deutsch'), ('dominikanisch', 'dominikanisch'), ('dschibutisch', 'dschibutisch'),
                   ('ecuadorianisch', 'ecuadorianisch'), ('salvadorianisch', 'salvadorianisch'),
                   ('eritreisch', 'eritreisch'), ('estnisch', 'estnisch'), ('fidschianisch', 'fidschianisch'),
                   ('finnisch', 'finnisch'), ('französisch', 'französisch'), ('gabunisch', 'gabunisch'),
                   ('gambisch', 'gambisch'), ('georgisch', 'georgisch'), ('ghanaisch', 'ghanaisch'),
                   ('grenadisch', 'grenadisch'), ('griechisch', 'griechisch'), ('guatemaltekisch', 'guatemaltekisch'),
                   ('guineisch', 'guineisch'), ('guinea-bissauisch', 'guinea-bissauisch'), ('guyanisch', 'guyanisch'),
                   ('haitianisch', 'haitianisch'), ('honduranisch', 'honduranisch'), ('indisch', 'indisch'),
                   ('indonesisch', 'indonesisch'), ('irakisch', 'irakisch'), ('iranisch', 'iranisch'),
                   ('irisch', 'irisch'), ('isländisch', 'isländisch'), ('israelisch', 'israelisch'),
                   ('italienisch', 'italienisch'), ('jamaikanisch', 'jamaikanisch'), ('japanisch', 'japanisch'),
                   ('jemenitisch', 'jemenitisch'), ('jordanisch', 'jordanisch'), ('kambodschanisch', 'kambodschanisch'),
                   ('kamerunisch', 'kamerunisch'), ('kanadisch', 'kanadisch'), ('kasachisch', 'kasachisch'),
                   ('katarisch', 'katarisch'), ('kenianisch', 'kenianisch'), ('kirgisisch', 'kirgisisch'),
                   ('kiribatisch', 'kiribatisch'), ('kolumbianisch', 'kolumbianisch'), ('komorisch', 'komorisch'),
                   ('kongolesisch', 'kongolesisch'),
                   ('der Demokratischen Republik Kongo', 'der Demokratischen Republik Kongo'),
                   ('der Demokratischen Volksrepublik Korea', 'der Demokratischen Volksrepublik Korea'),
                   ('der Republik Korea', 'der Republik Korea'), ('kosovarisch', 'kosovarisch'),
                   ('kroatisch', 'kroatisch'), ('kubanisch', 'kubanisch'), ('kuwaitisch', 'kuwaitisch'),
                   ('laotisch', 'laotisch'), ('lesothisch', 'lesothisch'), ('lettisch', 'lettisch'),
                   ('libanesisch', 'libanesisch'), ('liberianisch', 'liberianisch'), ('libysch', 'libysch'),
                   ('liechtensteinisch', 'liechtensteinisch'), ('litauisch', 'litauisch'),
                   ('luxemburgisch', 'luxemburgisch'), ('madagassisch', 'madagassisch'), ('malawisch', 'malawisch'),
                   ('malaysisch', 'malaysisch'), ('maledivisch', 'maledivisch'), ('malisch', 'malisch'),
                   ('maltesisch', 'maltesisch'), ('marokkanisch', 'marokkanisch'), ('marshallisch', 'marshallisch'),
                   ('mauretanisch', 'mauretanisch'), ('mauritisch', 'mauritisch'), ('mazedonisch', 'mazedonisch'),
                   ('mexikanisch', 'mexikanisch'), ('mikronesisch', 'mikronesisch'), ('moldauisch', 'moldauisch'),
                   ('monegassisch', 'monegassisch'), ('mongolisch', 'mongolisch'),
                   ('montenegrinisch', 'montenegrinisch'), ('mosambikanisch', 'mosambikanisch'),
                   ('myanmarisch', 'myanmarisch'), ('namibisch', 'namibisch'), ('nauruisch', 'nauruisch'),
                   ('nepalesisch', 'nepalesisch'), ('neuseeländisch', 'neuseeländisch'),
                   ('nicaraguanisch', 'nicaraguanisch'), ('niederländisch', 'niederländisch'), ('nigrisch', 'nigrisch'),
                   ('nigerianisch', 'nigerianisch'), ('norwegisch', 'norwegisch'), ('omanisch', 'omanisch'),
                   ('österreichisch', 'österreichisch'), ('pakistanisch', 'pakistanisch'), ('palauisch', 'palauisch'),
                   ('panamaisch', 'panamaisch'), ('papua-neuguineisch', 'papua-neuguineisch'),
                   ('paraguayisch', 'paraguayisch'), ('peruanisch', 'peruanisch'), ('philippinisch', 'philippinisch'),
                   ('polnisch', 'polnisch'), ('portugiesisch', 'portugiesisch'), ('ruandisch', 'ruandisch'),
                   ('rumänisch', 'rumänisch'), ('russisch', 'russisch'), ('salomonisch', 'salomonisch'),
                   ('sambisch', 'sambisch'), ('samoanisch', 'samoanisch'), ('san-marinesisch', 'san-marinesisch'),
                   ('são-toméisch', 'são-toméisch'), ('saudi-arabisch', 'saudi-arabisch'), ('schwedisch', 'schwedisch'),
                   ('schweizerisch', 'schweizerisch'), ('senegalesisch', 'senegalesisch'), ('serbisch', 'serbisch'),
                   ('seychellisch', 'seychellisch'), ('sierra-leonisch', 'sierra-leonisch'),
                   ('simbabwisch', 'simbabwisch'), ('singapurisch', 'singapurisch'), ('slowakisch', 'slowakisch'),
                   ('slowenisch', 'slowenisch'), ('somalisch', 'somalisch'), ('spanisch', 'spanisch'),
                   ('sri-lankisch', 'sri-lankisch'), ('von St. Kitts und Nevis', 'von St. Kitts und Nevis'),
                   ('lucianisch', 'lucianisch'), ('vincentisch', 'vincentisch'), ('südafrikanisch', 'südafrikanisch'),
                   ('sudanesisch', 'sudanesisch'), ('südsudanesisch', 'südsudanesisch'), ('surinamisch', 'surinamisch'),
                   ('swasiländisch', 'swasiländisch'), ('syrisch', 'syrisch'), ('tadschikisch', 'tadschikisch'),
                   ('tansanisch', 'tansanisch'), ('thailändisch', 'thailändisch'),
                   ('von Timor-Leste', 'von Timor-Leste'), ('togoisch', 'togoisch'), ('tongaisch', 'tongaisch'),
                   ('von Trinidad und Tobago', 'von Trinidad und Tobago'), ('tschadisch', 'tschadisch'),
                   ('tschechisch', 'tschechisch'), ('tunesisch', 'tunesisch'), ('türkisch', 'türkisch'),
                   ('turkmenisch', 'turkmenisch'), ('tuvaluisch', 'tuvaluisch'), ('ugandisch', 'ugandisch'),
                   ('ukrainisch', 'ukrainisch'), ('ungarisch', 'ungarisch'), ('uruguayisch', 'uruguayisch'),
                   ('usbekisch', 'usbekisch'), ('vanuatuisch', 'vanuatuisch'), ('vatikanisch', 'vatikanisch'),
                   ('venezolanisch', 'venezolanisch'),
                   ('der Vereinigten Arabischen Emirate', 'der Vereinigten Arabischen Emirate'),
                   ('amerikanisch', 'amerikanisch'), ('britisch', 'britisch'), ('vietnamesisch', 'vietnamesisch'),
                   ('weißrussisch', 'weißrussisch'), ('zentralafrikanisch', 'zentralafrikanisch'),
                   ('zyprisch', 'zyprisch')]
    Language = [('deutsch', 'deutsch'), ('englisch', 'english')]
    Salutation = [('Mr.', 'Herr'), ('Ms.', 'Frau'), ('Mrs.', 'Frau'), ('Dr.', 'Dr.'), ('Prof.', 'Prof.')]
    Month = [('Januar', 'Januar'), ('Februar', 'Februar'), ('März', 'März'), ('April', 'April'), ('Mai', 'Mai'),
             ('Juni', 'Juni'), ('Juli', 'Juli'), ('August', 'August'), ('September', 'September'),
             ('Oktober', 'Oktober'), ('November', 'November'), ('Dezember', 'Dezember')]
    Payment = [('Zu Beginn jeden Monats', 'Beginning of each Month'),
               ('Zu Beginn jeden Semesters', 'Beginning of each Semester')]
    PaymentOptions = [('Suspend payments', 'Suspend payments'),
                      ('Continue regular payments', 'Continue regular payments'),
                      ('Partial payments', 'Partial payments')]
    AccountStatus = [('Immatrikuliert', 'Enrolled'), ('Abgebrochen', 'Aborted'), ('Beurlaubt', 'Semester Off'),
                     ('Auslandssemester', 'Semester abroad'), ('Exmatrikuliert', 'Exmatriculated')]
    InvoiceStatus = [('Draft', 'Draft'), ('Sent', 'Sent'), ('Paid', 'Paid'), ('Cancelled', 'Cancelled')]
    InvoiceLIType = [('TuitionFee', 'Studiengebühr'), ('SemesterFee', 'Semesterbeitrag'),
                     ('SemesterDiscount', 'Rabatt auf Semesterbeitrag'), ('OverdueFee', 'Mahngebühr'),
                     ('MatriculationFee', 'Immatrikulationsgebühr'), ('Dunning Fee', 'Dunning Fee'),
                     ('Fee Semester abroad', 'Fee Semester abroad'), ('Fee Semester off', 'Fee Semester off')]
    ContractStatus = [('In Approval Process', 'Genehmigungsverfahren läuft'), ('Activated', 'Aktiviert'),
                      ('Draft', 'Entwurf'), ('Deaktiviert', 'Deaktiviert')]
    DiscountType = [('Discount Tuition Fee', 'Discount Tuition Fee'),
                    ('Discount Semester Fee', 'Discount Semester Fee')]


class RecordType(models.Model):
    name = models.CharField(max_length=80)
    developer_name = models.CharField(max_length=80, verbose_name='Record Type Name')
    sobject_type = models.CharField(max_length=40, verbose_name='Sobject Type Name', sf_read_only=models.NOT_UPDATEABLE,
                                    choices=[('Account', None), ('Contact', None), ('Contract', None),
                                             ('CustomerBankAccount__c', None), ('DegreeCourse__c', None),
                                             ('GoCardlessEvent__c', None), ('Invoice__c', None),
                                             ('InvoiceLineItem__c', None), ('Mandate__c', None), ('Opportunity', None),
                                             ('Order', None), ('Payment__c', None)])
    is_active = models.BooleanField(verbose_name='Active', sf_read_only=models.NOT_CREATEABLE, default=False)

    class Meta(models.Model.Meta):
        db_table = 'RecordType'
        verbose_name = 'Record Type'
        verbose_name_plural = 'Record Types'
        # keyPrefix = '012'

    def __str__(self):
        return self.name


class Account(models.Model):
    record_type = models.ForeignKey(RecordType, models.DO_NOTHING, blank=True, null=True,
                                    limit_choices_to={'sobject_type': 'Account'})

    last_modified_date = models.DateTimeField(sf_read_only=models.READ_ONLY)
    is_deleted = models.BooleanField(verbose_name='Deleted', sf_read_only=models.READ_ONLY, default=False)
    master_record = models.ForeignKey('self', models.DO_NOTHING, related_name='account_masterrecord_set',
                                      sf_read_only=models.READ_ONLY, blank=True, null=True)
    parent = models.ForeignKey('self', models.DO_NOTHING, related_name='account_parent_set', blank=True, null=True)

    billing_street = models.TextField(blank=True, null=True)
    billing_city = models.CharField(max_length=40, blank=True, null=True)
    billing_postal_code = models.CharField(max_length=20, verbose_name='Billing Zip/Postal Code', blank=True, null=True)
    billing_country = models.CharField(max_length=80, choices=Choices.Country, blank=True, null=True)

    name = models.CharField(max_length=255, verbose_name='Account Name')
    status = models.CharField(custom=True, max_length=255, choices=Choices.AccountStatus, blank=True, null=True)

    hochschule_ref = models.ForeignKey('self', models.DO_NOTHING, custom=True, related_name='account_hochschuleref_set',
                                       blank=True, null=True)
    immatrikulationsnummer = models.CharField(custom=True, max_length=255, verbose_name='Matriculation Number',
                                              blank=True, null=True)
    studiengebuehren_gesamt = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                                  verbose_name='Tuition Fee Total', blank=True, null=True)
    geschlecht = models.CharField(custom=True, max_length=255, verbose_name='Gender', choices=Choices.Gender,
                                  blank=True, null=True)
    geburtsort = models.CharField(custom=True, max_length=255, verbose_name='Place of Birth', blank=True, null=True)
    geburtsdatum = models.DateField(custom=True, verbose_name='Date of Birth', blank=True, null=True)
    geburtsland = models.CharField(custom=True, max_length=255, verbose_name='Country of Birth',
                                   choices=Choices.Country, blank=True, null=True)
    staatsangehoerigkeit = models.CharField(custom=True, max_length=255, verbose_name='Nationality',
                                            choices=Choices.Nationality, blank=True, null=True)
    kommunikationssprache = models.CharField(custom=True, max_length=255, verbose_name='Communication Language',
                                             choices=Choices.Language, blank=True, null=True)
    unimailadresse = models.EmailField(custom=True, verbose_name='University Email Address', blank=True, null=True)
    zahlungskontakt_ref = models.ForeignKey('Contact', models.DO_NOTHING, custom=True,
                                            related_name='account_zahlungskontaktref_set', blank=True, null=True)

    sepalastschriftmandat_erteilt_auto = models.BooleanField(custom=True,
                                                             db_column='SEPALastschriftmandatErteiltAuto__c',
                                                             verbose_name='SEPA Direct Debit Mandate Granted?',
                                                             sf_read_only=models.READ_ONLY)
    traegergesellschaft = models.CharField(custom=True, max_length=255, verbose_name='Private Sponsorship', blank=True,
                                           null=True)
    abwicklungsgebuhr_pro_einzug_pro_student = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                                                   verbose_name='Execution Fee / Direct Debit / Student',
                                                                   help_text='in Euro', blank=True, null=True)

    cspassword_token = models.CharField(custom=True, db_column='CSPasswordToken__c', max_length=50,
                                        verbose_name='CS Password Token', blank=True, null=True)

    initial_review_completed_auto = models.BooleanField(custom=True, verbose_name='Initial review completed',
                                                        sf_read_only=models.READ_ONLY)
    semester_fee_new = models.DecimalField(custom=True, max_digits=18, decimal_places=2, verbose_name='Semester Fee',
                                           blank=True, null=True)
    semester_fee_ref = models.DecimalField(custom=True, max_digits=18, decimal_places=2, verbose_name='Semester Fee',
                                           sf_read_only=models.READ_ONLY, blank=True, null=True)
    payment_options = models.CharField(custom=True, max_length=255, choices=Choices.PaymentOptions, blank=True,
                                       null=True)
    recordcreated = models.BooleanField(custom=True, verbose_name='Record created', default=models.DEFAULTED_ON_CREATE)
    student_approved = models.BooleanField(custom=True, verbose_name='Student Approved',
                                           default=models.DEFAULTED_ON_CREATE)
    initial_review_completed = models.BooleanField(custom=True, verbose_name='Initial Review Completed',
                                                   default=models.DEFAULTED_ON_CREATE)

    objects = managers.DefaultManager()
    universities = managers.UniversityManager()
    students = managers.StudentManager()

    class Meta(models.Model.Meta):
        db_table = 'Account'
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'
        # keyPrefix = '001'

    def __str__(self):
        return self.name

    def _is_student(self):
        return self.record_type.developer_name == 'Sofortzahler'

    def get_master_contact(self):
        if self._is_student():
            return self.contact_set.first()
        return None

    def get_active_contract(self):
        if self._is_student():
            return self.contract_account_set.first()
        return None

    def get_course(self):
        if self._is_student():
            contract = self.get_active_contract()
            return contract.studiengang_ref if contract else None
        return None

    def get_all_invoices(self):
        if self._is_student():
            return Invoice.objects.filter(contract__account__pk=self.pk)
        return None

    def get_active_courses(self):
        if not self._is_student():
            return self.degreecourse_set.filter(start_of_studies__gte=date.today())
        return None


class Contact(models.Model):
    record_type = models.ForeignKey(RecordType, models.DO_NOTHING, blank=True, null=True,
                                    limit_choices_to={'sobject_type': 'Contact'})
    last_modified_date = models.DateTimeField(sf_read_only=models.READ_ONLY)
    is_deleted = models.BooleanField(verbose_name='Deleted', sf_read_only=models.READ_ONLY, default=False)
    master_record = models.ForeignKey('self', models.DO_NOTHING, related_name='contact_masterrecord_set',
                                      sf_read_only=models.READ_ONLY, blank=True, null=True)

    account = models.ForeignKey(Account, models.DO_NOTHING, blank=True, null=True)  # Master Detail Relationship *

    last_name = models.CharField(max_length=80)
    first_name = models.CharField(max_length=40, blank=True, null=True)
    salutation = models.CharField(max_length=40, choices=Choices.Salutation, blank=True, null=True)
    name = models.CharField(max_length=121, verbose_name='Full Name', sf_read_only=models.READ_ONLY)

    title = models.CharField(max_length=128, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    mobile_phone = models.CharField(max_length=40, blank=True, null=True)
    home_phone = models.CharField(max_length=40, blank=True, null=True)
    other_phone = models.CharField(max_length=40, blank=True, null=True)

    mailing_street = models.TextField(blank=True, null=True)
    mailing_city = models.CharField(max_length=40, blank=True, null=True)
    mailing_postal_code = models.CharField(max_length=20, verbose_name='Mailing Zip/Postal Code', blank=True, null=True)
    mailing_country = models.CharField(max_length=80, blank=True, null=True)

    sepalastschriftmandat_erteilt = models.BooleanField(custom=True, db_column='SEPALastschriftmandatErteilt__c',
                                                        verbose_name='SEPA Direct Debit Mandate Granted?',
                                                        default=models.DEFAULTED_ON_CREATE)
    zahlungskontakt_auto = models.BooleanField(custom=True, verbose_name='Payment Contact',
                                               sf_read_only=models.READ_ONLY)

    cspassword_token = models.CharField(custom=True, db_column='CSPasswordToken__c', max_length=50,
                                        verbose_name='CS Password Token', blank=True, null=True)
    invoice_contact = models.BooleanField(custom=True, default=models.DEFAULTED_ON_CREATE)
    sepamandate_form_auto = models.CharField(custom=True, db_column='SEPAMandateFormAuto__c', max_length=1300,
                                             verbose_name='SEPA Mandate Form', sf_read_only=models.READ_ONLY,
                                             blank=True, null=True)
    student_contact = models.BooleanField(custom=True, verbose_name='StudentContact',
                                          default=models.DEFAULTED_ON_CREATE)

    objects = managers.DefaultManager()
    university_staff = managers.UniversityManager()
    students = managers.StudentManager()

    class Meta(models.Model.Meta):
        db_table = 'Contact'
        verbose_name = 'Contact'
        verbose_name_plural = 'Contacts'
        # keyPrefix = '003'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if (self.pk is None) and (self.record_type.developer_name == 'Hochschule'):
            UserModel = get_user_model()
            if not UserModel.objects.filter(email=self.email).exists():
                new_user = UserModel(email=self.email, is_active=False)
                new_user.save()
                pt = new_user.create_token()
                self.cspassword_token = pt.token
            else:
                # TODO How to react to this?
                pass

        return super(Contact, self).save(*args, **kwargs)


class DegreeCourse(models.Model):
    is_deleted = models.BooleanField(verbose_name='Deleted', sf_read_only=models.READ_ONLY, default=False)
    name = models.CharField(max_length=80, verbose_name='Studiengang Name', default=models.DEFAULTED_ON_CREATE,
                            blank=True, null=True)
    university = models.ForeignKey(Account, models.DO_NOTHING, custom=True,
                                   sf_read_only=models.NOT_UPDATEABLE)  # Master Detail Relationship 0
    course_id = models.CharField(custom=True, max_length=1300, verbose_name='Course of Study ID',
                                 sf_read_only=models.READ_ONLY, blank=True, null=True)

    standard_period_of_study = models.DecimalField(custom=True, max_digits=3, decimal_places=0,
                                                   verbose_name='Standard Study Period (No. of Semesters)', blank=True,
                                                   null=True)
    start_of_studies = models.DateField(custom=True, verbose_name='Start of Studies', blank=True, null=True)
    start_summer_semester = models.CharField(custom=True, max_length=255, verbose_name='Starting Month Summer Semester',
                                             choices=Choices.Month, blank=True, null=True)
    start_winter_semester = models.CharField(custom=True, max_length=255, verbose_name='Starting Month Winter Semester',
                                             choices=Choices.Month, blank=True, null=True)
    start_of_studies_month = models.CharField(custom=True, max_length=255, verbose_name='Starting Month of Studies',
                                              choices=Choices.Month, blank=True, null=True)

    matriculation_fee = models.DecimalField(custom=True, max_digits=18, decimal_places=2, blank=True, null=True)
    semester_fee = models.DecimalField(custom=True, max_digits=18, decimal_places=2, blank=True, null=True)
    cost_per_month = models.DecimalField(custom=True, max_digits=18, decimal_places=2, verbose_name='Cost per Month',
                                         blank=True, null=True)
    cost_per_semester = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                            verbose_name='Cost per Semester', blank=True, null=True)
    fee_semester_abroad = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                              verbose_name='Fee Semester abroad', blank=True, null=True)
    fee_semester_off = models.DecimalField(custom=True, max_digits=18, decimal_places=0,
                                           verbose_name='Fee Semester off', blank=True, null=True)
    cost_per_month_beyond_standard = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                                         verbose_name='Cost per Month > Standard Study Period',
                                                         blank=True, null=True)

    total_tuition_fees_auto = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                                  verbose_name='Tuition Fees Total', sf_read_only=models.READ_ONLY,
                                                  blank=True, null=True)
    number_of_sofortzahler_trig = models.DecimalField(custom=True, max_digits=18, decimal_places=0,
                                                      verbose_name='Number of Sofortzahler', blank=True, null=True)

    class Meta(models.Model.Meta):
        db_table = 'DegreeCourse__c'
        verbose_name = 'Degree Course'
        verbose_name_plural = 'Degree Courses'
        # keyPrefix = 'a00'


class Contract(models.Model):
    record_type = models.ForeignKey(RecordType, models.DO_NOTHING, blank=True, null=True,
                                    limit_choices_to={'sobject_type': 'Contract'})
    is_deleted = models.BooleanField(verbose_name='Deleted', sf_read_only=models.READ_ONLY, default=False)

    account = models.ForeignKey(Account, models.DO_NOTHING,
                                related_name='contract_account_set')  # Master Detail Relationship *
    contract_number = models.CharField(max_length=30, sf_read_only=models.READ_ONLY)

    university_ref = models.ForeignKey(Account, models.DO_NOTHING, custom=True,
                                       related_name='contract_universityref_set', blank=True, null=True)
    studiengang_ref = models.ForeignKey('DegreeCourse', models.DO_NOTHING, custom=True, blank=True, null=True)
    active = models.BooleanField(custom=True, verbose_name='Aktiv', default=models.DEFAULTED_ON_CREATE)
    payment_interval = models.CharField(custom=True, max_length=255, choices=Choices.Payment, blank=True, null=True)
    first_payment = models.BooleanField(custom=True, default=models.DEFAULTED_ON_CREATE)
    cost_per_month = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                         verbose_name='Cost per Month>Standard Study Period',
                                         sf_read_only=models.READ_ONLY, blank=True, null=True)
    total_tuition_fees_ref = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                                 verbose_name='Tuition Fees Total', sf_read_only=models.READ_ONLY,
                                                 blank=True, null=True)
    standard_period_of_study_ref = models.DecimalField(custom=True, max_digits=18, decimal_places=0,
                                                       verbose_name='Standard Study Period (No. of Semesters)',
                                                       sf_read_only=models.READ_ONLY, blank=True, null=True)
    payment_terms_auto = models.CharField(custom=True, max_length=1300, verbose_name='Payment Terms',
                                          sf_read_only=models.READ_ONLY, blank=True, null=True)
    matriculation_fee_ref = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                                verbose_name='Matriculation Fee', sf_read_only=models.READ_ONLY,
                                                blank=True, null=True)
    start_summer_semester_ref = models.CharField(custom=True, max_length=1300,
                                                 verbose_name='Starting Month Summer Semester',
                                                 sf_read_only=models.READ_ONLY, blank=True, null=True)
    semester_fee_ref = models.DecimalField(custom=True, max_digits=18, decimal_places=2, verbose_name='Semester Fee',
                                           sf_read_only=models.READ_ONLY, blank=True, null=True)
    total_amount_of_rates_auto = models.DecimalField(custom=True, max_digits=18, decimal_places=0,
                                                     verbose_name='Number of Rates Total',
                                                     sf_read_only=models.READ_ONLY, blank=True, null=True)
    student_id_ref = models.CharField(custom=True, max_length=1300, verbose_name='Student ID',
                                      sf_read_only=models.READ_ONLY, blank=True, null=True)
    cost_per_month2 = models.DecimalField(custom=True, max_digits=18, decimal_places=2, verbose_name='Cost per Month',
                                          sf_read_only=models.READ_ONLY, blank=True, null=True)
    cost_per_semester = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                            verbose_name='Cost per Semester', sf_read_only=models.READ_ONLY, blank=True,
                                            null=True)
    count_invoices = models.DecimalField(custom=True, max_digits=18, decimal_places=0, verbose_name='Count of Invoices',
                                         sf_read_only=models.READ_ONLY, blank=True, null=True)
    start_of_studies_month_ref = models.CharField(custom=True, max_length=1300, verbose_name='Startmonat Studienbeginn',
                                                  sf_read_only=models.READ_ONLY, blank=True, null=True)
    start_winter_semester_ref = models.CharField(custom=True, max_length=1300,
                                                 verbose_name='Starting Month Winter Semester',
                                                 sf_read_only=models.READ_ONLY, blank=True, null=True)
    discount_helper_auto = models.DecimalField(custom=True, max_digits=3, decimal_places=0,
                                               verbose_name='Discount Helper', sf_read_only=models.READ_ONLY,
                                               blank=True, null=True)
    active_discounts = models.BooleanField(custom=True, verbose_name='Aktive Rabatte', sf_read_only=models.READ_ONLY)
    include_in_invoice_creation_process_auto = models.BooleanField(custom=True,
                                                                   verbose_name='Include In Invoice Creation Process',
                                                                   sf_read_only=models.READ_ONLY)
    number_of_invoices_auto = models.DecimalField(custom=True, max_digits=18, decimal_places=0,
                                                  verbose_name='Number of Invoices', sf_read_only=models.READ_ONLY,
                                                  blank=True, null=True)
    payment_contact_trig = models.ForeignKey(Contact, models.DO_NOTHING, custom=True,
                                             related_name='contract_paymentcontacttrig_set', blank=True, null=True)
    special_fee_auto = models.DecimalField(custom=True, max_digits=18, decimal_places=2, verbose_name='Special Fee',
                                           sf_read_only=models.READ_ONLY, blank=True, null=True)

    status = models.CharField(max_length=40, choices=Choices.ContractStatus, default=models.DEFAULTED_ON_CREATE)

    class Meta(models.Model.Meta):
        db_table = 'Contract'
        verbose_name = 'Contract'
        verbose_name_plural = 'Contracts'
        # keyPrefix = '800'

    def get_current_invoice(self):
        return self.invoice_set.last()

    def get_discount(self):
        rc = self.rabatt_set.first()
        if rc is None:
            rc = Rabatt(contract=self)
        return rc


class Rabatt(models.Model):
    is_deleted = models.BooleanField(verbose_name='Deleted', sf_read_only=models.READ_ONLY, default=False)
    name = models.CharField(max_length=80, verbose_name='Discounts', sf_read_only=models.READ_ONLY)
    contract = models.ForeignKey(Contract, models.DO_NOTHING, custom=True,
                                 sf_read_only=models.NOT_UPDATEABLE)  # Master Detail Relationship 0
    discount_type = models.CharField(custom=True, max_length=255, choices=Choices.DiscountType, blank=True, null=True)
    discount_tuition_fee = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                               verbose_name='Discount on Tuition Fee', blank=True, null=True)
    discount_semester_fee = models.DecimalField(custom=True, max_digits=18, decimal_places=0,
                                                verbose_name='Discount on Semester Fee', blank=True, null=True)
    applicable_months = models.DecimalField(custom=True, max_digits=3, decimal_places=0,
                                            verbose_name='Number of Applicable Months', blank=True, null=True)
    utilization = models.DecimalField(custom=True, max_digits=18, decimal_places=0,
                                      verbose_name='Number of Utilizations', blank=True, null=True)
    active = models.BooleanField(custom=True, default=models.DEFAULTED_ON_CREATE)

    class Meta(models.Model.Meta):
        db_table = 'Rabatt__c'
        verbose_name = 'Discount'
        verbose_name_plural = 'Discounts'
        # keyPrefix = 'a0H'


# class Mandate(models.Model):
#    is_deleted = models.BooleanField(verbose_name='Deleted', sf_read_only=models.READ_ONLY, default=False)
#    name = models.CharField(max_length=80, sf_read_only=models.READ_ONLY)

#    customer_ref = models.ForeignKey(Contact, models.DO_NOTHING, custom=True, blank=True, null=True)
#    mandate_id = models.CharField(custom=True, max_length=255, verbose_name='Mandate GoCardless Id', blank=True, null=True)
#    bank_account_ref = models.ForeignKey(CustomerBankAccount, models.DO_NOTHING, custom=True, sf_read_only=models.NOT_UPDATEABLE)  # Master Detail Relationship 0
#    reference = models.CharField(custom=True, max_length=255, blank=True, null=True)
#    status = models.CharField(custom=True, max_length=255, choices=[('pending_customer_approval', 'pending_customer_approval'), ('pending_submission', 'pending_submission'), ('submitted', 'submitted'), ('active', 'active'), ('failed', 'failed'), ('cancelled', 'cancelled'), ('expired', 'expired')], blank=True, null=True)
#    mandate_pdf = models.TextField(custom=True, verbose_name='Mandate Pdf Url', blank=True, null=True)
#    class Meta(models.Model.Meta):
#        db_table = 'Mandate__c'
#        verbose_name = 'Mandate'
#        verbose_name_plural = 'Mandates'
#        # keyPrefix = 'a0C'


class Invoice(models.Model):
    is_deleted = models.BooleanField(verbose_name='Deleted', sf_read_only=models.READ_ONLY, default=False)
    name = models.CharField(max_length=80, verbose_name='Invoice Name', default=models.DEFAULTED_ON_CREATE, blank=True,
                            null=True)

    last_modified_date = models.DateTimeField(sf_read_only=models.READ_ONLY)

    contract = models.ForeignKey(Contract, models.DO_NOTHING, custom=True,
                                 sf_read_only=models.NOT_UPDATEABLE)  # Master Detail Relationship 0
    university_ref = models.CharField(custom=True, max_length=1300, verbose_name='University',
                                      sf_read_only=models.READ_ONLY, blank=True, null=True)
    contact = models.ForeignKey(Contact, models.DO_NOTHING, custom=True, blank=True, null=True)
    # mandate_ref = models.ForeignKey('Mandate', models.DO_NOTHING, custom=True, blank=True, null=True)
    student_id_ref = models.CharField(custom=True, max_length=1300, verbose_name='Student ID',
                                      sf_read_only=models.READ_ONLY, blank=True, null=True)
    period = models.CharField(custom=True, max_length=10, blank=True, null=True)
    total = models.DecimalField(custom=True, max_digits=18, decimal_places=2, verbose_name='Invoice Amount',
                                sf_read_only=models.READ_ONLY, blank=True, null=True)

    etsalutation_ref = models.CharField(custom=True, db_column='ETSalutationRef__c', max_length=1300,
                                        verbose_name='ETSalutation', sf_read_only=models.READ_ONLY, blank=True,
                                        null=True)
    etfirst_name_ref = models.CharField(custom=True, db_column='ETFirstNameRef__c', max_length=1300,
                                        verbose_name='ETFirstName', sf_read_only=models.READ_ONLY, blank=True,
                                        null=True)
    etlast_name_ref = models.CharField(custom=True, db_column='ETLastNameRef__c', max_length=1300,
                                       verbose_name='ETLastName', sf_read_only=models.READ_ONLY, blank=True, null=True)
    etbilling_street_ref = models.CharField(custom=True, db_column='ETBillingStreetRef__c', max_length=1300,
                                            verbose_name='ETBillingStreet', sf_read_only=models.READ_ONLY, blank=True,
                                            null=True)
    etbilling_zip_ref = models.CharField(custom=True, db_column='ETBillingZipRef__c', max_length=1300,
                                         verbose_name='ETBillingZip', sf_read_only=models.READ_ONLY, blank=True,
                                         null=True)
    etbilling_city_ref = models.CharField(custom=True, db_column='ETBillingCityRef__c', max_length=1300,
                                          verbose_name='ETBillingCity', sf_read_only=models.READ_ONLY, blank=True,
                                          null=True)

    studiengang_ref = models.CharField(custom=True, max_length=1300, verbose_name='Degree Course',
                                       sf_read_only=models.READ_ONLY, blank=True, null=True)
    payment_terms_ref = models.CharField(custom=True, max_length=1300, verbose_name='Payment Terms',
                                         sf_read_only=models.READ_ONLY, blank=True, null=True)
    is_dunning_invoice_trig = models.BooleanField(custom=True, verbose_name='Is Dunning Invoice',
                                                  default=models.DEFAULTED_ON_CREATE)
    invoice_date = models.DateField(custom=True, blank=True, null=True)
    etsalutation_ref = models.CharField(custom=True, db_column='ETSalutationRef__c', max_length=1300,
                                        verbose_name='ETSalutation', sf_read_only=models.READ_ONLY, blank=True,
                                        null=True)
    etfirst_name_ref = models.CharField(custom=True, db_column='ETFirstNameRef__c', max_length=1300,
                                        verbose_name='ETFirstName', sf_read_only=models.READ_ONLY, blank=True,
                                        null=True)
    etlast_name_ref = models.CharField(custom=True, db_column='ETLastNameRef__c', max_length=1300,
                                       verbose_name='ETLastName', sf_read_only=models.READ_ONLY, blank=True, null=True)
    etbilling_street_ref = models.CharField(custom=True, db_column='ETBillingStreetRef__c', max_length=1300,
                                            verbose_name='ETBillingStreet', sf_read_only=models.READ_ONLY, blank=True,
                                            null=True)
    etbilling_zip_ref = models.CharField(custom=True, db_column='ETBillingZipRef__c', max_length=1300,
                                         verbose_name='ETBillingZip', sf_read_only=models.READ_ONLY, blank=True,
                                         null=True)
    etbilling_city_ref = models.CharField(custom=True, db_column='ETBillingCityRef__c', max_length=1300,
                                          verbose_name='ETBillingCity', sf_read_only=models.READ_ONLY, blank=True,
                                          null=True)
    studiengang_ref = models.CharField(custom=True, max_length=1300, verbose_name='Degree Course',
                                       sf_read_only=models.READ_ONLY, blank=True, null=True)
    payment_terms_ref = models.CharField(custom=True, max_length=1300, verbose_name='Payment Terms',
                                         sf_read_only=models.READ_ONLY, blank=True, null=True)
    is_dunning_invoice_trig = models.BooleanField(custom=True, verbose_name='Is Dunning Invoice',
                                                  default=models.DEFAULTED_ON_CREATE)
    invoice_date = models.DateField(custom=True, blank=True, null=True)
    mandate_go_cardless_id_auto = models.CharField(custom=True, max_length=1300, verbose_name='Mandate GoCardless Id',
                                                   sf_read_only=models.READ_ONLY, blank=True, null=True)
    reference_trig = models.CharField(custom=True, max_length=255, verbose_name='Reference', blank=True, null=True)

    status = models.CharField(custom=True, max_length=255, choices=Choices.InvoiceStatus, blank=True, null=True)
    dont_count_rates_trig = models.BooleanField(custom=True, verbose_name="Don't count rates",
                                                default=models.DEFAULTED_ON_CREATE)
    invoice_has_special_fees = models.BooleanField(custom=True, default=models.DEFAULTED_ON_CREATE)

    class Meta(models.Model.Meta):
        db_table = 'Invoice__c'
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'
        # keyPrefix = 'a09'


class InvoiceLineItem(models.Model):
    is_deleted = models.BooleanField(verbose_name='Deleted', sf_read_only=models.READ_ONLY, default=False)
    name = models.CharField(max_length=80, verbose_name='Invoice Line Item Name', sf_read_only=models.READ_ONLY)

    invoice = models.ForeignKey('Invoice', models.DO_NOTHING, custom=True,
                                sf_read_only=models.NOT_UPDATEABLE)  # Master Detail Relationship 0
    amount = models.DecimalField(custom=True, max_digits=18, decimal_places=2, verbose_name='Amount Total', blank=True,
                                 null=True)
    unit_price = models.DecimalField(custom=True, max_digits=18, decimal_places=2, blank=True, null=True)
    type = models.CharField(custom=True, max_length=255, verbose_name='Invoice Item', choices=Choices.InvoiceLIType,
                            blank=True, null=True)

    class Meta(models.Model.Meta):
        db_table = 'InvoiceLineItem__c'
        verbose_name = 'Invoice Line Item'
        verbose_name_plural = 'Invoice Line Items'
        # keyPrefix = 'a0G'


class Attachment(models.Model):
    is_deleted = models.BooleanField(
        verbose_name='Deleted',
        sf_read_only=models.READ_ONLY,
        default=False)
    parent = models.ForeignKey(
        Invoice,
        models.DO_NOTHING,
        sf_read_only=models.NOT_UPDATEABLE)
    name = models.CharField(
        max_length=255,
        verbose_name='File Name')
    is_private = models.BooleanField(
        verbose_name='Private',
        default=models.DEFAULTED_ON_CREATE)
    content_type = models.CharField(
        max_length=120,
        blank=True,
        null=True)
    body_length = models.IntegerField(
        sf_read_only=models.READ_ONLY,
        blank=True,
        null=True)
    body = models.TextField()

    def fetch_content(self):
        session = connections['salesforce'].sf_session
        url = session.auth.instance_url + self.body
        blob = handle_api_exceptions(url, session.get).text

        return blob
