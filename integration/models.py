from __future__ import unicode_literals
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from datetime import date, timedelta

from salesforce import models
from salesforce.backend.driver import handle_api_exceptions
from django.db import connections, models as django_models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from . import managers


class PerishableTokenMixin:
    def is_token_expired(self):
        if not self.cspassword_token:
            return True
        if not self.cspassword_time:
            return False
        if self.cspassword_time < timezone.now():
            return True

        return False

    def request_new_password(self):
        self.password_change_requested = True
        self.save()


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
    Gender = [('weiblich', _('female')), ('männlich', _('male')), ('geschlechtsneutral', _('non-binary'))]
    Biological_Sex = [('Female', _('female')), ('Male', _('male')), ('Third gender', _('non-binary'))]
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
    Language = [('German', _('Deutsch')), ('English', _('English'))]
    Salutation = [('Mr.', _('Mr.')), ('Ms.', _('Ms.')), ('Mrs.', _('Mrs.')), ('Dr.', _('Dr.')), ('Prof.', _('Prof.'))]
    Month = [('January', _('January')), ('February', _('February')), ('March', _('March')), ('April', _('April')),
             ('May', _('May')), ('June', _('June')), ('July', _('July')), ('August', _('August')),
             ('September', _('September')), ('October', _('October')), ('November', _('November')),
             ('Dezember', _('December'))]
    Payment = [('Zu Beginn jeden Monats', _('Beginning of each Month')),
               ('Zu Beginn jeden Semesters', _('Beginning of each Semester'))]
    PaymentOptions = [('Suspend payments', _('Suspend payments')),
                      ('Continue regular payments', _('Continue regular payments')),
                      ('Partial payments', _('Partial payments'))]
    AccountStatus = [('Immatrikuliert', _('Enrolled')), ('Abgebrochen', _('Aborted')), ('Beurlaubt', _('Semester Off')),
                     ('Auslandssemester', _('Semester abroad')), ('Exmatrikuliert', _('Exmatriculated'))]
    InvoiceStatus = [('Draft', _('Draft')), ('Sent', _('Sent')), ('Paid', _('Paid')), ('Cancelled', _('Cancelled'))]
    InvoiceLIType = [('TuitionFee', _('Tuition Fee')), ('SemesterFee', _('Semester Fee')),
                     ('SemesterDiscount', _('Semester Discount')), ('OverdueFee', _('Overdue Fee')),
                     ('MatriculationFee', _('Matriculation Fee')), ('Dunning Fee', _('Dunning Fee')),
                     ('Fee Semester abroad', _('Fee Semester abroad')), ('Fee Semester off', _('Fee Semester off'))]
    ContractStatus = [('In Approval Process', _('In Approval Process')), ('Activated', _('Activated')),
                      ('Draft', _('Draft')), ('Deaktiviert', _('Deactivated')), ('Active', _('Active'))]
    DiscountType = [('Discount Tuition Fee', _('Discount Tuition Fee')),
                    ('Discount Semester Fee', _('Discount Semester Fee'))]
    LeadStatus = [('Prospect', _('Prospect')), ('Applicant', _('Applicant')), ('Nurturing', _('Nurturing')),
                  ('Pending', _('Pending')), ('Qualified', _('Qualifiziert')), ('Unqualified', _('Unqualifiziert'))]
    UGVStatus = [('Not applied yet', _('Not applied yet')), ('Confirmed applicant', _('Confirmed applicant')),
                 ('Rejected applicant', _('Rejected applicant')), ('Accepted applicant', _('Accepted applicant')),
                 ('Already student', _('Already student'))]
    CustomerType = [('CS', 'CS'), ('CeG', 'CeG'), ('CS+CeG', 'CS+CeG')]
    ContractPeriod = [('Semester', _('Semester')), ('All Upfront', _('All Upfront')),
                      ('One year Upfront', _('One year Upfront'))]


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


class Lead(models.Model):
    is_deleted = models.BooleanField(verbose_name='Deleted', sf_read_only=models.READ_ONLY, default=False)
    created_date = models.DateTimeField(sf_read_only=models.READ_ONLY)
    master_record = models.ForeignKey('self', models.DO_NOTHING, sf_read_only=models.READ_ONLY, blank=True, null=True)
    last_name = models.CharField(max_length=80)
    first_name = models.CharField(max_length=40, blank=True, null=True)
    name = models.CharField(max_length=121, verbose_name=_('Full Name'), sf_read_only=models.READ_ONLY)
    record_type = models.ForeignKey('RecordType', models.DO_NOTHING, blank=True, null=True)

    street = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=40, blank=True, null=True)
    state = models.CharField(max_length=80, verbose_name=_('State/Province'), blank=True, null=True)
    postal_code = models.CharField(max_length=20, verbose_name=_('Zip/Postal Code'), blank=True, null=True)
    citizenship_new = models.CharField(custom=True, max_length=255, verbose_name=_('Citizenship'),
                                       choices=Choices.Nationality, blank=True, null=True)

    phone = models.CharField(max_length=40, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    date_of_birth = models.DateField(custom=True, verbose_name=_('Date of birth'), blank=True, null=True)
    place_of_birth = models.CharField(custom=True, max_length=255, verbose_name=_('Place of Birth'), blank=True,
                                      null=True)
    no_oecdpassport = models.BooleanField(custom=True, db_column='NoOECDPassport__c',
                                          verbose_name=_('No OECD Passport'), default=models.DEFAULTED_ON_CREATE)
    kommunicationssprache = models.CharField(custom=True, max_length=255, verbose_name=_('Communication Language'),
                                             choices=Choices.Language, blank=True,
                                             null=True)
    start_semester = models.DateField(custom=True, verbose_name=_('Start semester'), blank=True, null=True)
    university_status = models.CharField(custom=True, max_length=255, choices=Choices.UGVStatus, blank=True,
                                         null=True)

    status = models.CharField(max_length=40, default=models.DEFAULTED_ON_CREATE, choices=Choices.LeadStatus)
    confirmed_by_university = models.BooleanField(custom=True, verbose_name='Confirmed by University',
                                                  default=models.DEFAULTED_ON_CREATE)

    is_converted = models.BooleanField(verbose_name='Converted', sf_read_only=models.NOT_UPDATEABLE,
                                       default=models.DEFAULTED_ON_CREATE)
    converted_date = models.DateField(sf_read_only=models.READ_ONLY, blank=True, null=True)
    converted_account = models.ForeignKey('Account', models.DO_NOTHING, sf_read_only=models.READ_ONLY, blank=True,
                                          null=True)
    converted_contact = models.ForeignKey('Contact', models.DO_NOTHING, sf_read_only=models.READ_ONLY, blank=True,
                                          null=True)

    active_application = models.ForeignKey('Application', models.DO_NOTHING, custom=True, blank=True, null=True)
    uploaded_via_portal_trig = models.BooleanField(custom=True, verbose_name='Uploaded via Portal',
                                                   default=models.DEFAULTED_ON_CREATE)
    biological_sex = models.CharField(custom=True, max_length=255, verbose_name='Biological sex',
                                      choices=Choices.Biological_Sex, blank=True, null=True)
    postal_street = models.CharField(custom=True, max_length=255, blank=True, null=True)
    postal_code_0 = models.CharField(db_column='PostalCode__c', custom=True, max_length=20, blank=True,
                                     null=True)  # Field renamed because of name conflict.
    postal_city = models.CharField(custom=True, max_length=255, blank=True, null=True)
    postal_country = models.CharField(custom=True, max_length=255, choices=Choices.Country, blank=True, null=True)
    link_zu_weiteren_dokumenten = models.URLField(custom=True, verbose_name='Link zu weiteren Dokumenten', blank=True,
                                                  null=True)
    risiko_nicht_bei_chancen = models.BooleanField(custom=True, db_column='RisikoNichtBeiCHANCENeG__c',
                                                      verbose_name='Risiko nicht bei CHANCEN eG',
                                                      default=models.DEFAULTED_ON_CREATE)


    objects = managers.DefaultManager()
    ugv_students = managers.UGVLeadManager()

    class Meta(models.Model.Meta):
        db_table = 'Lead'
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'
        # keyPrefix = '00Q'

    @property
    def application(self):
        return self.active_application


class Application(models.Model):
    is_deleted = models.BooleanField(verbose_name='Deleted', sf_read_only=models.READ_ONLY, default=False)
    name = models.CharField(max_length=80, verbose_name='Application Name', default=models.DEFAULTED_ON_CREATE,
                            blank=True, null=True)
    lead_ref = models.ForeignKey('Lead', models.DO_NOTHING, custom=True, blank=True, null=True)
    hochschule_ref = models.ForeignKey('Account', models.DO_NOTHING, custom=True,
                                       sf_read_only=models.NOT_UPDATEABLE)  # Master Detail Relationship 0
    studiengang_ref = models.ForeignKey('DegreeCourse', models.DO_NOTHING, custom=True,
                                        sf_read_only=models.NOT_UPDATEABLE)  # Master Detail Relationship 1
    studienstart = models.DateField(custom=True, verbose_name=_('Start Semester'), blank=True, null=True)
    start_of_study_trig = models.CharField(custom=True, max_length=255, verbose_name=_('Start of Study'),
                                           blank=True, null=True)
    already_student = models.BooleanField(custom=True, verbose_name='Already student',
                                          default=models.DEFAULTED_ON_CREATE)
    confirmed_by_university = models.BooleanField(custom=True, verbose_name='Confirmed by university',
                                                  default=models.DEFAULTED_ON_CREATE)
    contract_ref = models.ForeignKey('Contract', models.DO_NOTHING, custom=True, blank=True, null=True)

    class Meta(models.Model.Meta):
        db_table = 'Application__c'
        verbose_name = 'Application'
        verbose_name_plural = 'Applications'
        # keyPrefix = 'a0N'


class Account(models.Model, PerishableTokenMixin):
    record_type = models.ForeignKey(RecordType, models.DO_NOTHING, blank=True, null=True,
                                    limit_choices_to={'sobject_type': 'Account'})

    last_modified_date = models.DateTimeField(sf_read_only=models.READ_ONLY)
    is_deleted = models.BooleanField(verbose_name='Deleted', sf_read_only=models.READ_ONLY, default=False)
    master_record = models.ForeignKey('self', models.DO_NOTHING, related_name='account_masterrecord_set',
                                      sf_read_only=models.READ_ONLY, blank=True, null=True)
    parent = models.ForeignKey('self', models.DO_NOTHING, related_name='account_parent_set', blank=True, null=True)

    billing_street = models.TextField(blank=True, null=True, verbose_name=_('Street and House number'))
    billing_city = models.CharField(max_length=40, blank=True, null=True, verbose_name=_('City'))
    billing_postal_code = models.CharField(max_length=20, verbose_name=_('Zip/Postal Code'), blank=True, null=True)
    billing_country = models.CharField(max_length=80, choices=Choices.Country, verbose_name=_('Country'), blank=True,
                                       null=True)

    name = models.CharField(max_length=255, verbose_name=_('Name'))
    status = models.CharField(custom=True, max_length=255, choices=Choices.AccountStatus, verbose_name=_('Status'),
                              blank=True, null=True)
    customer_type = models.CharField(custom=True, max_length=255, verbose_name=_('Customer type'),
                                     choices=Choices.CustomerType, blank=True, null=True)

    # Person Account
    person_contact = models.ForeignKey('Contact', models.DO_NOTHING, related_name='account_personcontact_set',
                                       sf_read_only=models.READ_ONLY, blank=True, null=True)
    is_person_account = models.BooleanField(sf_read_only=models.READ_ONLY, default=False)
    person_email = models.EmailField(verbose_name='Email', blank=True, null=True)
    phone = models.CharField(max_length=40, verbose_name='Phone', blank=True, null=True)

    abwicklungsgebuhr_pro_einzug_pro_student = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                                                   verbose_name=_(
                                                                       'Execution Fee / Direct Debit / Student'),
                                                                   help_text='in Euro', blank=True, null=True)
    ibanhsauto = models.CharField(custom=True, db_column='IBANHSAuto__c', max_length=255, verbose_name='IBAN',
                                  blank=True, null=True)
    bichsauto = models.CharField(custom=True, db_column='BICHSAuto__c', max_length=255, verbose_name='BIC', blank=True,
                                 null=True)

    hochschule_ref = models.ForeignKey('self', models.DO_NOTHING, custom=True, related_name='account_hochschuleref_set',
                                       blank=True, null=True, verbose_name=_('University'))
    immatrikulationsnummer = models.CharField(custom=True, max_length=255, verbose_name=_('Matriculation Number'),
                                              blank=True, null=True)
    studiengebuehren_gesamt = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                                  verbose_name=_('Tuition Fee Total'), blank=True, null=True)
    geschlecht = models.CharField(custom=True, max_length=255, verbose_name=_('Gender'), choices=Choices.Gender,
                                  blank=True, null=True)
    geburtsort = models.CharField(custom=True, max_length=255, verbose_name=_('Place of Birth'), blank=True, null=True)
    geburtsdatum = models.DateField(custom=True, verbose_name=_('Date of Birth'), blank=True, null=True)
    geburtsland = models.CharField(custom=True, max_length=255, verbose_name=_('Country of Birth'),
                                   choices=Choices.Country, blank=True, null=True)
    staatsangehoerigkeit = models.CharField(custom=True, max_length=255, verbose_name=_('Nationality'),
                                            choices=Choices.Nationality, blank=True, null=True)
    kommunikationssprache = models.CharField(custom=True, max_length=255, verbose_name=_('Communication Language'),
                                             choices=Choices.Language, null=True)
    unimailadresse = models.EmailField(custom=True, verbose_name=_('University Email Address'), blank=True, null=True)

    zahlungskontakt_ref = models.ForeignKey('Contact', models.DO_NOTHING, custom=True,
                                            related_name='account_zahlungskontaktref_set', blank=True, null=True)
    student_contact = models.ForeignKey('Contact', models.DO_NOTHING, custom=True,
                                        related_name='account_studentcontact_set', blank=True, null=True)

    sepalastschriftmandat_erteilt_auto = models.BooleanField(custom=True,
                                                             db_column='SEPALastschriftmandatErteiltAuto__c',
                                                             verbose_name='SEPA Direct Debit Mandate Granted?',
                                                             sf_read_only=models.READ_ONLY)
    traegergesellschaft = models.CharField(custom=True, max_length=255, verbose_name='Private Sponsorship', blank=True,
                                           null=True)

    cspassword_token = models.CharField(custom=True, db_column='CSPasswordToken__c', max_length=50,
                                        verbose_name='CS Password Token', blank=True, null=True)
    cspassword_time = models.DateTimeField(custom=True, db_column='CSPasswordTime__c', verbose_name='CS Password Time',
                                           blank=True, null=True)
    password_change_requested = models.BooleanField(custom=True, default=models.DEFAULTED_ON_CREATE)

    initial_review_completed_auto = models.BooleanField(custom=True, verbose_name='Initial review completed',
                                                        sf_read_only=models.READ_ONLY)
    semester_fee_new = models.DecimalField(custom=True, max_digits=18, decimal_places=2, verbose_name=_('Semester Fee'),
                                           blank=True, null=True,
                                           help_text=_('Modify this value to update all Courses.'))
    semester_fee_ref = models.DecimalField(custom=True, max_digits=18, decimal_places=2, verbose_name=_('Semester Fee'),
                                           sf_read_only=models.READ_ONLY, blank=True, null=True)
    payment_options = models.CharField(custom=True, max_length=255, choices=Choices.PaymentOptions, blank=True,
                                       null=True, verbose_name=_('Payment options'))
    recordcreated = models.BooleanField(custom=True, verbose_name='Record created', default=models.DEFAULTED_ON_CREATE)
    student_approved = models.BooleanField(custom=True, verbose_name='Student Approved',
                                           default=models.DEFAULTED_ON_CREATE)
    initial_review_completed = models.BooleanField(custom=True, verbose_name='Initial Review Completed',
                                                   default=models.DEFAULTED_ON_CREATE)
    zahlungskontakt_auto = models.BooleanField(db_column='ZahlungskontaktAuto__pc', verbose_name='Payment Contact',
                                                  sf_read_only=models.READ_ONLY)
    has_sofortzahler_contract_auto = models.BooleanField(custom=True, verbose_name='Has Sofortzahler Contract',
                                                         sf_read_only=models.READ_ONLY)
    student_template_id = models.CharField(custom=True, max_length=18, blank=True, null=True)
    applicant_template_id = models.CharField(custom=True, max_length=18, blank=True, null=True)
    applicant_upload_functionality_enabled = models.BooleanField(custom=True, default=models.DEFAULTED_ON_CREATE)
    citizenship = models.CharField(custom=True, max_length=255, choices=Choices.Nationality, blank=True, null=True)

    objects = managers.DefaultManager()
    universities = managers.UniversityManager()
    students = managers.StudentManager()
    ugv_students = managers.UGVStudentManager()

    class Meta(models.Model.Meta):
        db_table = 'Account'
        verbose_name = _('Account')
        verbose_name_plural = _('Accounts')
        # keyPrefix = '001'

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        update_fields = update_fields or [x.attname for x in self._meta.fields if not x.primary_key]
        if self.is_person_account and ('name' in update_fields):
            update_fields.remove('name')
        return super(Account, self).save(force_insert=force_insert, force_update=force_update, using=using,
                                         update_fields=update_fields)

    def __str__(self):
        return self.name

    @property
    def is_student(self):
        return self.record_type.developer_name == 'Sofortzahler' or \
               (self.record_type.developer_name == 'UGVStudents' and self.has_sofortzahler_contract_auto)

    @property
    def is_ugv_student(self):
        return self.record_type.developer_name == 'UGVStudents' and not self.has_sofortzahler_contract_auto

    @property
    def is_ugv(self):
        return self.record_type.developer_name == 'UGVStudents'

    @property
    def is_eg_customer(self):
        return (not self.is_student) and ('CeG' in self.customer_type)

    @property
    def is_uploader(self):
        return self.is_eg_customer and self.applicant_upload_functionality_enabled

    @property
    def is_drawer_enabled(self):
        return self.is_uploader or self.is_services_customer

    @property
    def is_services_customer(self):
        return (not self.is_student) and ('CS' in self.customer_type)

    @property
    def user_email(self):
        return self.person_email if self.is_person_account else self.unimailadresse

    @property
    def master_contact(self):
        return self.get_student_contact()

    @property
    def payment_contact(self):
        if self.is_student or self.is_ugv_student:
            return self.zahlungskontakt_ref
        return None

    @property
    def active_contract(self):
        if self.is_student:
            return self.contract_account_set.filter(record_type__developer_name='Sofortzahler').first()
        elif self.is_ugv_student:
            return self.contract_account_set.filter(record_type__developer_name='Ruckzahler').first()
        return None

    @property
    def ruckzahler_contract(self):
        if self.is_student or self.is_ugv_student:
            return self.contract_account_set.filter(record_type__developer_name='Ruckzahler').first()
        return None

    @property
    def course(self):
        if self.is_student or self.is_ugv_student:
            return self.active_contract.studiengang_ref if self.active_contract else None
        return None

    @property
    def review_completed(self):
        return self.initial_review_completed or self.master_contact.zahlungskontakt_auto

    def get_student_contact(self):
        if self.is_student or self.is_ugv_student:
            return self.person_contact if self.is_person_account else self.student_contact
        return None

    def get_all_invoices(self, order='-invoice_date'):
        # if self.is_student:
        return Invoice.objects.filter(contract__account__pk=self.pk).order_by(order)
        # return None

    def get_active_courses(self):
        if not self.is_student and not self.is_ugv_student:
            # min_date = date.today() - timedelta(31)
            return self.degreecourse_set.all()  # filter(start_of_studies__gte=min_date)
        return None


class Contact(models.Model, PerishableTokenMixin):
    record_type = models.ForeignKey(RecordType, models.DO_NOTHING, blank=True, null=True,
                                    limit_choices_to={'sobject_type': 'Contact'})
    last_modified_date = models.DateTimeField(sf_read_only=models.READ_ONLY)
    is_deleted = models.BooleanField(verbose_name='Deleted', sf_read_only=models.READ_ONLY, default=False)
    master_record = models.ForeignKey('self', models.DO_NOTHING, related_name='contact_masterrecord_set',
                                      sf_read_only=models.READ_ONLY, blank=True, null=True)

    account = models.ForeignKey(Account, models.DO_NOTHING, blank=True, null=True)  # Master Detail Relationship *

    last_name = models.CharField(max_length=80, verbose_name=_('Last name'))
    first_name = models.CharField(max_length=40, blank=True, null=True, verbose_name=_('First name'))
    salutation = models.CharField(max_length=40, choices=Choices.Salutation, blank=True, null=True,
                                  verbose_name=_('Salutation'))
    name = models.CharField(max_length=121, verbose_name=_('Full Name'), sf_read_only=models.READ_ONLY)

    title = models.CharField(max_length=128, blank=True, null=True, verbose_name=_('title'))
    email = models.EmailField(verbose_name=_('Private email address'))
    mobile_phone = models.CharField(max_length=40, blank=True, null=True, verbose_name=_('Mobile phone'))
    home_phone = models.CharField(max_length=40, blank=True, null=True, verbose_name=_('Home phone'))
    other_phone = models.CharField(max_length=40, blank=True, null=True, verbose_name=_('Other phone'))

    mailing_street = models.TextField(blank=True, null=True, verbose_name=_('Street and House number'))
    mailing_city = models.CharField(max_length=40, blank=True, null=True, verbose_name=_('City'))
    mailing_postal_code = models.CharField(max_length=20, verbose_name=_('Zip/Postal Code'), blank=True, null=True)
    mailing_country = models.CharField(max_length=80, blank=True, null=True, verbose_name=_('Country'),
                                       choices=Choices.Country)
    zahlungskontakt_auto = models.BooleanField(custom=True, verbose_name='Payment Contact',
                                               sf_read_only=models.READ_ONLY)

    recordcreated = models.BooleanField(custom=True, verbose_name='Record created', default=models.DEFAULTED_ON_CREATE)
    cspassword_token = models.CharField(custom=True, db_column='CSPasswordToken__c', max_length=50,
                                        verbose_name='CS Password Token', blank=True, null=True)
    cspassword_time = models.DateTimeField(custom=True, db_column='CSPasswordTime__c', verbose_name='CS Password Time',
                                           blank=True, null=True)
    password_change_requested = models.BooleanField(custom=True, default=models.DEFAULTED_ON_CREATE)

    invoice_contact = models.BooleanField(custom=True, default=models.DEFAULTED_ON_CREATE)
    sepalastschriftmandat_erteilt = models.BooleanField(custom=True, db_column='SEPALastschriftmandatErteilt__c',
                                                        verbose_name='SEPA Direct Debit Mandate Granted?',
                                                        default=models.DEFAULTED_ON_CREATE)
    sepamandate_form_auto = models.CharField(custom=True, db_column='SEPAMandateFormAuto__c', max_length=1300,
                                             verbose_name='SEPA Mandate Form', sf_read_only=models.READ_ONLY,
                                             blank=True, null=True)
    sepamandate_url_auto = models.CharField(custom=True, db_column='SEPAMandateUrlAuto__c', max_length=1300,
                                            verbose_name='SEPA Mandate Url', sf_read_only=models.READ_ONLY,
                                            blank=True, null=True)
    student_contact = models.BooleanField(custom=True, verbose_name='StudentContact',
                                          default=models.DEFAULTED_ON_CREATE)
    cancel_bank_account = models.BooleanField(custom=True, verbose_name='CancelBankAccount',
                                              default=models.DEFAULTED_ON_CREATE)
    biological_sex = models.CharField(custom=True, max_length=255, verbose_name='Biological sex',
                                      choices=Choices.Biological_Sex, blank=True, null=True)

    mandate_open_payments = models.DecimalField(custom=True, max_digits=4, decimal_places=0, blank=True, null=True)

    objects = managers.DefaultManager()
    university_staff = managers.UniversityManager()
    students = managers.StudentManager()

    class Meta(models.Model.Meta):
        db_table = 'Contact'
        verbose_name = _('Contact')
        verbose_name_plural = _('Contacts')
        # keyPrefix = '003'

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        update_fields = update_fields or [x.attname for x in self._meta.fields if not x.primary_key]
        if self.account.is_person_account:
            update_fields.remove('account_id')
        return super(Contact, self).save(force_insert=force_insert, force_update=force_update, using=using,
                                         update_fields=update_fields)

    def __str__(self):
        return self.name

    @property
    def _is_staff(self):
        return self.record_type.developer_name == 'Hochschule'

    @property
    def user_email(self):
        return self.email

    @property
    def bank_account(self):
        if not self._is_staff:
            rc = self.customerbankaccount_set.filter(enabled=True)
            if rc.exists():
                return rc.first()

    @property
    def address_html(self):
        return '{self.mailing_street}<br>{self.mailing_city}, {self.mailing_postal_code}<br>{self.mailing_country}'.format(
            self=self)


class CustomerBankAccount(models.Model):
    is_deleted = models.BooleanField(verbose_name='Deleted', sf_read_only=models.READ_ONLY, default=False)
    name = models.CharField(max_length=80, verbose_name='Customer Bank Account Name', sf_read_only=models.READ_ONLY)

    customer_ref = models.ForeignKey(Contact, models.DO_NOTHING, custom=True,
                                     sf_read_only=models.NOT_UPDATEABLE)  # Master Detail Relationship 0
    account_holder_name = models.CharField(custom=True, max_length=255, blank=True, null=True,
                                           verbose_name=_('Account Holder Name'))
    account_number = models.CharField(custom=True, max_length=20, verbose_name=_('Account Number(last 2 digits)'),
                                      blank=True, null=True)
    bank_name = models.CharField(custom=True, max_length=255, blank=True, null=True, verbose_name=_('Bank Name'))
    country_code = models.CharField(custom=True, max_length=4, blank=True, null=True, verbose_name=_('Country Code'))
    enabled = models.BooleanField(custom=True, default=models.DEFAULTED_ON_CREATE, verbose_name=_('Enabled'))

    class Meta(models.Model.Meta):
        db_table = 'CustomerBankAccount__c'
        verbose_name = 'Customer Bank Account'
        verbose_name_plural = 'Customer Bank Accounts'
        # keyPrefix = 'a0D'

    def short(self):
        return '{self.country_code} **** {self.account_number}'.format(self=self)


class DegreeCourse(models.Model):
    is_deleted = models.BooleanField(verbose_name='Deleted', sf_read_only=models.READ_ONLY, default=False)
    name = models.CharField(max_length=80, verbose_name=_('Name'), default=models.DEFAULTED_ON_CREATE,
                            blank=True, null=True)
    created_date = models.DateTimeField(sf_read_only=models.READ_ONLY)
    university = models.ForeignKey(Account, models.DO_NOTHING, custom=True,
                                   sf_read_only=models.NOT_UPDATEABLE)  # Master Detail Relationship 0
    course_id = models.CharField(custom=True, max_length=1300, sf_read_only=models.READ_ONLY, blank=True, null=True)
    name_studiengang_auto = models.CharField(custom=True, max_length=1300, sf_read_only=models.READ_ONLY, blank=True,
                                             null=True)

    standard_period_of_study = models.DecimalField(custom=True, max_digits=3, decimal_places=0,
                                                   verbose_name=_('Standard Study Period (No. of Semesters)'),
                                                   blank=True,
                                                   null=True)
    start_of_study = models.CharField(custom=True, max_length=4099, verbose_name='Start of Study',
                                      choices=Choices.Month, blank=True,
                                      null=True)
    standard_period_of_study = models.DecimalField(custom=True, max_digits=3, decimal_places=0,
                                                   verbose_name='Standard Study Period (No. of Semesters)', blank=True,
                                                   null=True)
    start_of_studies_month = models.CharField(custom=True, max_length=255, verbose_name=_('Starting Month of Studies'),
                                              choices=Choices.Month, blank=True, null=True)

    matriculation_fee = models.DecimalField(custom=True, max_digits=18, decimal_places=2, blank=True, null=True,
                                            verbose_name=_('Matriculation Fee'))
    semester_fee = models.DecimalField(custom=True, max_digits=18, decimal_places=2, blank=True, null=True,
                                       verbose_name=_('Semester Fee'))
    cost_per_month = models.DecimalField(custom=True, max_digits=18, decimal_places=2, verbose_name=_('Cost per Month'),
                                         blank=True, null=True)
    cost_per_semester = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                            verbose_name=_('Cost per Semester'), blank=True, null=True)
    fee_semester_abroad = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                              verbose_name=_('Fee Semester abroad'), blank=True, null=True)
    fee_semester_off = models.DecimalField(custom=True, max_digits=18, decimal_places=0,
                                           verbose_name=_('Fee Semester off'), blank=True, null=True)
    cost_per_month_beyond_standard = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                                         verbose_name=_('Cost per Month>Standard Study Period'),
                                                         blank=True, null=True)

    total_tuition_fees_auto = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                                  verbose_name=_('Tuition Fees Total'), sf_read_only=models.READ_ONLY,
                                                  blank=True, null=True)
    number_of_sofortzahler_trig = models.DecimalField(custom=True, max_digits=18, decimal_places=0,
                                                      verbose_name=_('Number of Sofortzahler'), blank=True, null=True)

    @property
    def translated_start_of_study(self):
        if self.start_of_study:
            translated_months = [dict(Choices.Month).get(study_month, study_month) for study_month in self.start_of_study.split(';') if study_month]
            return ';'.join(map(str, translated_months))
        else:
            return ''

    class Meta(models.Model.Meta):
        db_table = 'DegreeCourse__c'
        verbose_name = _('Degree Course')
        verbose_name_plural = _('Degree Courses')
        # keyPrefix = 'a00'

    @property
    def unique_name(self):
        return "{self.university.id}-{self.name}".format(self=self)

    @property
    def active_fees(self):
        return self.degreecoursefees_set.filter(valid_from__lte=timezone.now()).order_by('-valid_from').first()

    @property
    def past_fees(self):
        if self.active_fees:
            return self.degreecoursefees_set.filter(valid_from__lt=self.active_fees.valid_from).order_by('-valid_from')
        return None

    @property
    def ugv_contracts(self):
        return self.contract_set.filter(template=True, record_type__developer_name='Ruckzahler')

    @property
    def templates(self):
        return self.contract_set.filter(template=True).order_by('valid_from')

    def __str__(self):
        return "[{self.university.name}] {self.name}".format(self=self)


class DegreeCourseFees(models.Model):
    is_deleted = models.BooleanField(verbose_name='Deleted', sf_read_only=models.READ_ONLY, default=False)
    name = models.CharField(max_length=80, verbose_name='Auto Number', sf_read_only=models.READ_ONLY)
    degree_course_ref = models.ForeignKey('DegreeCourse', models.DO_NOTHING, custom=True,
                                          sf_read_only=models.NOT_UPDATEABLE)  # Master Detail Relationship 0
    valid_from = models.DateField(custom=True, verbose_name=_('Valid from'))
    cost_per_month = models.DecimalField(custom=True, max_digits=18, decimal_places=2, verbose_name=_('Cost per Month'),
                                         blank=True, null=True)
    cost_per_month_beyond_standard = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                                         verbose_name=_('Cost per Month > Standard Study Period'),
                                                         blank=True, null=True)
    cost_per_semester = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                            verbose_name=_('Cost per Semester'), blank=True, null=True)
    fee_semester_abroad = models.DecimalField(custom=True, max_digits=18, decimal_places=2, blank=True, null=True)
    fee_semester_off = models.DecimalField(custom=True, max_digits=18, decimal_places=2, blank=True, null=True)
    matriculation_fee = models.DecimalField(custom=True, max_digits=18, decimal_places=2, blank=True, null=True)
    semester_fee = models.DecimalField(custom=True, max_digits=18, decimal_places=2, blank=True, null=True)
    total_tuition_fees_auto = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                                  verbose_name=_('Tuition Fees Total'), sf_read_only=models.READ_ONLY,
                                                  blank=True, null=True)

    class Meta(models.Model.Meta):
        db_table = 'DegreeCourseFees__c'
        verbose_name = 'Degree Course Fees'
        verbose_name_plural = 'Degree Courses Fees'
        # keyPrefix = 'a0P'

    def __str__(self):
        return "{self.degree_course_ref.name} from {self.valid_from}".format(self=self)


class Contract(models.Model):
    record_type = models.ForeignKey(RecordType, models.DO_NOTHING, blank=True, null=True,
                                    limit_choices_to={'sobject_type': 'Contract'})
    is_deleted = models.BooleanField(verbose_name='Deleted', sf_read_only=models.READ_ONLY, default=False)

    account = models.ForeignKey(Account, models.DO_NOTHING,
                                related_name='contract_account_set')  # Master Detail Relationship *
    contract_number = models.CharField(max_length=30, sf_read_only=models.READ_ONLY, verbose_name=_('Number'))

    university_ref = models.ForeignKey(Account, models.DO_NOTHING, custom=True, verbose_name=_('University'),
                                       related_name='contract_universityref_set', blank=True, null=True)
    studiengang_ref = models.ForeignKey('DegreeCourse', models.DO_NOTHING, custom=True, blank=True, null=True,
                                        verbose_name=_('Degree Course'))
    degree_course_fees_ref = models.ForeignKey('DegreeCourseFees', models.DO_NOTHING, custom=True, blank=True,
                                               null=True)
    payment_interval = models.CharField(custom=True, max_length=255, choices=Choices.Payment, blank=True, null=True,
                                        verbose_name=_('Payment Interval'))
    first_payment = models.BooleanField(custom=True, default=models.DEFAULTED_ON_CREATE)
    cost_per_month = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                         verbose_name=_('Cost per Month>Standard Study Period'),
                                         sf_read_only=models.READ_ONLY, blank=True, null=True)
    total_tuition_fees_ref = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                                 verbose_name=_('Tuition Fees Total'), sf_read_only=models.READ_ONLY,
                                                 blank=True, null=True)
    standard_period_of_study_ref = models.DecimalField(custom=True, max_digits=18, decimal_places=0,
                                                       verbose_name=_('Standard Study Period (No. of Semesters)'),
                                                       sf_read_only=models.READ_ONLY, blank=True, null=True)
    payment_terms_auto = models.CharField(custom=True, max_length=1300, verbose_name=_('Payment Terms'),
                                          sf_read_only=models.READ_ONLY, blank=True, null=True)
    matriculation_fee_ref = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                                verbose_name=_('Matriculation Fee'), sf_read_only=models.READ_ONLY,
                                                blank=True, null=True)
    #    start_summer_semester_ref = models.CharField(custom=True, max_length=1300,
    #                                                 verbose_name=_('Starting Month Summer Semester'),
    #                                                 sf_read_only=models.READ_ONLY, blank=True, null=True)
    semester_fee_ref = models.DecimalField(custom=True, max_digits=18, decimal_places=2, verbose_name=_('Semester Fee'),
                                           sf_read_only=models.READ_ONLY, blank=True, null=True)
    total_amount_of_rates_auto = models.DecimalField(custom=True, max_digits=18, decimal_places=0,
                                                     verbose_name=_('Number of Rates Total'),
                                                     sf_read_only=models.READ_ONLY, blank=True, null=True)
    student_id_ref = models.CharField(custom=True, max_length=1300, verbose_name=_('Student ID'),
                                      sf_read_only=models.READ_ONLY, blank=True, null=True)
    cost_per_month2 = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                          verbose_name=_('Cost per Month'),
                                          sf_read_only=models.READ_ONLY, blank=True, null=True)
    cost_per_semester = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                            verbose_name=_('Cost per Semester'), sf_read_only=models.READ_ONLY,
                                            blank=True,
                                            null=True)
    count_invoices = models.DecimalField(custom=True, max_digits=18, decimal_places=0,
                                         verbose_name=_('Count of Invoices'),
                                         sf_read_only=models.READ_ONLY, blank=True, null=True)
    #    start_of_studies_month_ref = models.CharField(custom=True, max_length=1300,
    #                                                  verbose_name=_('Start of Studies Month'),
    #                                                  sf_read_only=models.READ_ONLY, blank=True, null=True)
    #    start_winter_semester_ref = models.CharField(custom=True, max_length=1300,
    #                                                 verbose_name=_('Starting Month Winter Semester'),
    #                                                 sf_read_only=models.READ_ONLY, blank=True, null=True)

    start_of_studies_auto = models.DateField(custom=True, verbose_name=_('Start of Studies'),
                                             sf_read_only=models.READ_ONLY, blank=True, null=True)
    discount_helper_auto = models.DecimalField(custom=True, max_digits=3, decimal_places=0,
                                               verbose_name=_('Discount Helper'), sf_read_only=models.READ_ONLY,
                                               blank=True, null=True)
    active_discounts = models.BooleanField(custom=True, verbose_name=_('Active Discounts'),
                                           sf_read_only=models.READ_ONLY)
    active_payment = models.BooleanField(custom=True, default=models.DEFAULTED_ON_CREATE)
    include_in_invoice_creation_process_auto = models.BooleanField(custom=True,
                                                                   verbose_name=_(
                                                                       'Include In Invoice Creation Process'),
                                                                   sf_read_only=models.READ_ONLY)
    number_of_invoices_auto = models.DecimalField(custom=True, max_digits=18, decimal_places=0,
                                                  verbose_name=_('Number of Invoices'), sf_read_only=models.READ_ONLY,
                                                  blank=True, null=True)
    payment_contact_trig = models.ForeignKey(Contact, models.DO_NOTHING, custom=True,
                                             related_name='contract_paymentcontacttrig_set', blank=True, null=True)
    special_fee_auto = models.DecimalField(custom=True, max_digits=18, decimal_places=2, verbose_name=_('Special Fee'),
                                           sf_read_only=models.READ_ONLY, blank=True, null=True)

    status = models.CharField(max_length=40, choices=Choices.ContractStatus, default=models.DEFAULTED_ON_CREATE,
                              verbose_name=_('Status'))

    net_funding_amount = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                             verbose_name=_('Net funding amount'), blank=True, null=True)
    repayment_period = models.DecimalField(custom=True, max_digits=18, decimal_places=0,
                                           verbose_name=_('Repayment period'), default=models.DEFAULTED_ON_CREATE,
                                           blank=True, null=True)
    relevant_repayment_period = models.DecimalField(custom=True, max_digits=18, decimal_places=0,
                                                    verbose_name=_('Relevant repayment period'),
                                                    default=models.DEFAULTED_ON_CREATE, blank=True, null=True)
    maximum_repayment = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                            verbose_name=_('Maximum repayment'), sf_read_only=models.READ_ONLY,
                                            blank=True, null=True)
    repayment_amount = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                           verbose_name=_('Repayment amount'), blank=True, null=True)
    minimal_monthly_instalments = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                                      verbose_name=_('Minimal monthly instalments'),
                                                      sf_read_only=models.READ_ONLY, blank=True, null=True)
    annual_maximum_repayment = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                                   verbose_name=_('Annual maximum repayment'),
                                                   sf_read_only=models.READ_ONLY, blank=True, null=True)
    annual_minimum_limit = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                               verbose_name=_('Annual minimum limit'), sf_read_only=models.READ_ONLY,
                                               blank=True, null=True)
    annual_minimal_income_indexed = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                                        verbose_name=_('Annual minimal income indexed'), blank=True,
                                                        null=True)
    valid_from = models.DateField(custom=True, verbose_name=_('Valid from'), blank=True, null=True)
    years_of_payment = models.DecimalField(custom=True, max_digits=2, decimal_places=0,
                                           verbose_name=_('Years of payment'), blank=True, null=True)
    start_of_repayment = models.DecimalField(custom=True, max_digits=2, decimal_places=0,
                                             verbose_name=_('Start of repayment'), default=models.DEFAULTED_ON_CREATE,
                                             blank=True, null=True)

    template = models.BooleanField(custom=True, default=models.DEFAULTED_ON_CREATE)
    application_form_display_name = models.CharField(custom=True, max_length=255, blank=True, null=True)
    minimal_relevant_income = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                                  verbose_name=_('Minimal relevant income'),
                                                  default=models.DEFAULTED_ON_CREATE, blank=True, null=True)
    full_finanzing = models.BooleanField(custom=True, verbose_name=_('Full Finanzing'),
                                         default=models.DEFAULTED_ON_CREATE)
    counterpart = models.ForeignKey('self', models.DO_NOTHING, custom=True, blank=True, null=True)
    credit_balances_account_number = models.CharField(custom=True, max_length=1300,
                                                      verbose_name=_('Credit balances account number'),
                                                      sf_read_only=models.READ_ONLY, blank=True, null=True)
    period = models.CharField(custom=True, max_length=255, choices=Choices.ContractPeriod, blank=True, null=True)
    factor = models.DecimalField(custom=True, max_digits=4, decimal_places=0, blank=True, null=True)
    notice_to_quit = models.DateField(custom=True, verbose_name=_('Notice to quit'), blank=True, null=True)
    emergence = models.DateField(custom=True, blank=True, null=True)

    class Meta(models.Model.Meta):
        db_table = 'Contract'
        verbose_name = _('Contract')
        verbose_name_plural = _('Contracts')
        # keyPrefix = '800'

    @property
    def is_ruckzahler(self):
        return self.record_type.developer_name == 'Ruckzahler'

    @property
    def current_invoice(self):
        return self.invoice_set.last()

    @property
    def all_invoices(self):
        return self.invoice_set.exclude(status='Draft').order_by('-invoice_date')

    @property
    def semester_discount(self):
        rc = self.rabatt_set.filter(active=True, discount_type=Choices.DiscountType[1][0]).first()
        if rc is None:
            rc = Rabatt(contract=self, discount_type=Choices.DiscountType[1][0])
        return rc

    @property
    def tuition_discount(self):
        rc = self.rabatt_set.filter(active=True, discount_type=Choices.DiscountType[0][0]).first()
        if rc is None:
            rc = Rabatt(contract=self, discount_type=Choices.DiscountType[0][0])
        return rc

    @property
    def ugv_semester_fee(self):
        return self.net_funding_amount / self.standard_period_of_study_ref


class Rabatt(models.Model):
    is_deleted = models.BooleanField(verbose_name='Deleted', sf_read_only=models.READ_ONLY, default=False)
    name = models.CharField(max_length=80, verbose_name=_('Name'), sf_read_only=models.READ_ONLY)
    contract = models.ForeignKey(Contract, models.DO_NOTHING, custom=True,
                                 sf_read_only=models.NOT_UPDATEABLE)  # Master Detail Relationship 0
    discount_type = models.CharField(custom=True, max_length=255, choices=Choices.DiscountType,
                                     verbose_name=_('Discount Type'))
    discount_tuition_fee = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                               verbose_name=_('Discount on Tuition Fee'), blank=True, null=True)
    discount_semester_fee = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                                verbose_name=_('Discount on Semester Fee'), blank=True, null=True)
    applicable_months = models.DecimalField(custom=True, max_digits=3, decimal_places=0,
                                            verbose_name=_('Number of Applicable Months'), blank=True, null=True)
    utilization = models.DecimalField(custom=True, max_digits=18, decimal_places=0,
                                      verbose_name=_('Number of Utilizations'), blank=True, null=True)
    active = models.BooleanField(custom=True, default=models.DEFAULTED_ON_CREATE, verbose_name=_('Active'))

    class Meta(models.Model.Meta):
        db_table = 'Rabatt__c'
        verbose_name = _('Discount')
        verbose_name_plural = _('Discounts')
        # keyPrefix = 'a0H'


class Invoice(models.Model):
    is_deleted = models.BooleanField(verbose_name='Deleted', sf_read_only=models.READ_ONLY, default=False)
    name = models.CharField(max_length=80, verbose_name=_('Name'), default=models.DEFAULTED_ON_CREATE, blank=True,
                            null=True)

    last_modified_date = models.DateTimeField(sf_read_only=models.READ_ONLY)

    contract = models.ForeignKey(Contract, models.DO_NOTHING, custom=True,
                                 sf_read_only=models.NOT_UPDATEABLE)  # Master Detail Relationship 0
    university_ref = models.CharField(custom=True, max_length=1300, verbose_name=_('University'),
                                      sf_read_only=models.READ_ONLY, blank=True, null=True)
    contact = models.ForeignKey(Contact, models.DO_NOTHING, custom=True, blank=True, null=True,
                                verbose_name=_('Contact'))
    # mandate_ref = models.ForeignKey('Mandate', models.DO_NOTHING, custom=True, blank=True, null=True)
    student_id_ref = models.CharField(custom=True, max_length=1300, verbose_name=_('Student ID'),
                                      sf_read_only=models.READ_ONLY, blank=True, null=True)
    period = models.CharField(custom=True, max_length=10, blank=True, null=True, verbose_name=_('Period'))
    total = models.DecimalField(custom=True, max_digits=18, decimal_places=2, verbose_name=_('Invoice Amount'),
                                sf_read_only=models.READ_ONLY, blank=True, null=True)

    studiengang_ref = models.CharField(custom=True, max_length=1300, verbose_name=_('Degree Course'),
                                       sf_read_only=models.READ_ONLY, blank=True, null=True)
    payment_terms_ref = models.CharField(custom=True, max_length=1300, verbose_name=_('Payment Terms'),
                                         sf_read_only=models.READ_ONLY, blank=True, null=True)
    invoice_date = models.DateField(custom=True, blank=True, null=True, verbose_name=_('Invoice Date'))

    status = models.CharField(custom=True, max_length=255, choices=Choices.InvoiceStatus, blank=True, null=True,
                              verbose_name=_('Status'))

    class Meta(models.Model.Meta):
        db_table = 'Invoice__c'
        verbose_name = _('Invoice')
        verbose_name_plural = _('Invoices')
        # keyPrefix = 'a09'

    def get_current_attachment(self):
        return Attachment.objects.filter(parent_id=self.pk).last()


class Attachment(models.Model):
    is_deleted = models.BooleanField(
        verbose_name='Deleted',
        sf_read_only=models.READ_ONLY,
        default=False)

    parent_id = models.CharField(max_length=18)
    parent_type = models.CharField(max_length=50, db_column='Parent.Type', sf_read_only=models.READ_ONLY)

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
    created_date = models.DateTimeField(sf_read_only=models.READ_ONLY)

    def fetch_content(self):
        session = connections['salesforce'].sf_session
        url = session.auth.instance_url + self.body
        blob = handle_api_exceptions(url, session.get)

        return blob
