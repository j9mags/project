from __future__ import unicode_literals

from django.db import connections
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from salesforce import models
from salesforce.backend.driver import handle_api_exceptions

from decimal import Decimal

from . import managers


class PerishableTokenMixin:
    @property
    def cs_token(self):
        # return self.cspassword_token_pc if self.is_person_account else self.cspassword_token
        return self.cspassword_token

    def is_token_expired(self):
        token = self.cs_token
        if not token:
            return True

        # time = self.cspassword_time_pc if self.is_person_account else self.cspassword_time
        time = self.cspassword_time
        if not time:
            return True

        if time < timezone.now():
            return True

        return False

    def request_new_password(self):
        self.password_change_requested = True
        self.save()

    def clear_token(self):
        self.cspassword_time = None
        self.cspassword_token = None

        # if self.is_person_account:
        #     self.cspassword_time_pc = None
        #     self.cspassword_token_pc = None

    @property
    def update_fields(self):
        rc = ['cspassword_token', 'cspassword_time', 'recordcreated']
        # if self.is_person_account:
        #     rc.extend(['cspassword_token_pc', 'cspassword_time_pc'])


class Choices:
    Country = [('Abchasien', _('Abchasien')), ('Afghanistan', _('Afghanistan')), ('Ägypten', _('Ägypten')),
               ('Albanien', _('Albanien')), ('Algerien', _('Algerien')), ('Andorra', _('Andorra')),
               ('Angola', _('Angola')), ('Antigua und Barbuda', _('Antigua und Barbuda')),
               ('Äquatorialguinea', _('Äquatorialguinea')), ('Argentinien', _('Argentinien')),
               ('Armenien', _('Armenien')), ('Aserbaidschan', _('Aserbaidschan')), ('Äthiopien', _('Äthiopien')),
               ('Australien', _('Australien')), ('Bahamas', _('Bahamas')), ('Bahrain', _('Bahrain')),
               ('Bangladesch', _('Bangladesch')), ('Barbados', _('Barbados')), ('Belgien', _('Belgien')),
               ('Belize', _('Belize')), ('Benin', _('Benin')), ('Bergkarabach', _('Bergkarabach')),
               ('Bhutan', _('Bhutan')), ('Bolivien', _('Bolivien')),
               ('Bosnien und Herzegowina', _('Bosnien und Herzegowina')), ('Botswana', _('Botswana')),
               ('Brasilien', _('Brasilien')), ('Brunei', _('Brunei')), ('Bulgarien', _('Bulgarien')),
               ('Burkina Faso', _('Burkina Faso')), ('Burundi', _('Burundi')), ('Chile', _('Chile')),
               ('Republik China', _('Republik China')), ('Volksrepublik China', _('Volksrepublik China')),
               ('Cookinseln', _('Cookinseln')), ('Costa Rica', _('Costa Rica')), ('Dänemark', _('Dänemark')),
               ('Deutschland', _('Deutschland')), ('Dominica', _('Dominica')),
               ('Dominikanische Republik', _('Dominikanische Republik')), ('Dschibuti', _('Dschibuti')),
               ('Ecuador', _('Ecuador')), ('El Salvador', _('El Salvador')), ('Elfenbeinküste', _('Elfenbeinküste')),
               ('Eritrea', _('Eritrea')), ('Estland', _('Estland')), ('Fidschi', _('Fidschi')),
               ('Finnland', _('Finnland')), ('Frankreich', _('Frankreich')), ('Gabun', _('Gabun')),
               ('Gambia', _('Gambia')), ('Georgien', _('Georgien')), ('Ghana', _('Ghana')), ('Grenada', _('Grenada')),
               ('Griechenland', _('Griechenland')), ('Guatemala', _('Guatemala')), ('Guinea', _('Guinea')),
               ('Guinea-Bissau', _('Guinea-Bissau')), ('Guyana', _('Guyana')), ('Haiti', _('Haiti')),
               ('Honduras', _('Honduras')), ('Indien', _('Indien')), ('Indonesien', _('Indonesien')),
               ('Irak', _('Irak')), ('Iran', _('Iran')), ('Irland', _('Irland')), ('Island', _('Island')),
               ('Israel', _('Israel')), ('Italien', _('Italien')), ('Jamaika', _('Jamaika')), ('Japan', _('Japan')),
               ('Jemen', _('Jemen')), ('Jordanien', _('Jordanien')), ('Kambodscha', _('Kambodscha')),
               ('Kamerun', _('Kamerun')), ('Kanada', _('Kanada')), ('Kap Verde', _('Kap Verde')),
               ('Kasachstan', _('Kasachstan')), ('Katar', _('Katar')), ('Kenia', _('Kenia')),
               ('Kirgisistan', _('Kirgisistan')), ('Kiribati', _('Kiribati')), ('Kolumbien', _('Kolumbien')),
               ('Komoren', _('Komoren')), ('Kongo, Demokratische Republik', _('Kongo, Demokratische Republik')),
               ('Kongo, Republik', _('Kongo, Republik')), ('Korea, Nord', _('Korea, Nord')),
               ('Korea, Süd', _('Korea, Süd')), ('Kosovo', _('Kosovo')), ('Kroatien', _('Kroatien')),
               ('Kuba', _('Kuba')), ('Kuwait', _('Kuwait')), ('Laos', _('Laos')), ('Lesotho', _('Lesotho')),
               ('Lettland', _('Lettland')), ('Libanon', _('Libanon')), ('Liberia', _('Liberia')),
               ('Libyen', _('Libyen')), ('Liechtenstein', _('Liechtenstein')), ('Litauen', _('Litauen')),
               ('Luxemburg', _('Luxemburg')), ('Madagaskar', _('Madagaskar')), ('Malawi', _('Malawi')),
               ('Malaysia', _('Malaysia')), ('Malediven', _('Malediven')), ('Mali', _('Mali')), ('Malta', _('Malta')),
               ('Marokko', _('Marokko')), ('Marshallinseln', _('Marshallinseln')), ('Mauretanien', _('Mauretanien')),
               ('Mauritius', _('Mauritius')), ('Mazedonien', _('Mazedonien')), ('Mexiko', _('Mexiko')),
               ('Mikronesien', _('Mikronesien')), ('Moldawien', _('Moldawien')), ('Monaco', _('Monaco')),
               ('Mongolei', _('Mongolei')), ('Montenegro', _('Montenegro')), ('Mosambik', _('Mosambik')),
               ('Myanmar', _('Myanmar')), ('Namibia', _('Namibia')), ('Nauru', _('Nauru')), ('Nepal', _('Nepal')),
               ('Neuseeland', _('Neuseeland')), ('Nicaragua', _('Nicaragua')), ('Niederlande', _('Niederlande')),
               ('Niger', _('Niger')), ('Nigeria', _('Nigeria')), ('Niue', _('Niue')), ('Nordzypern', _('Nordzypern')),
               ('Norwegen', _('Norwegen')), ('Oman', _('Oman')), ('Österreich', _('Österreich')),
               ('Osttimor / Timor-Leste', _('Osttimor / Timor-Leste')), ('Pakistan', _('Pakistan')),
               ('Palästina', _('Palästina')), ('Palau', _('Palau')), ('Panama', _('Panama')),
               ('Papua-Neuguinea', _('Papua-Neuguinea')), ('Paraguay', _('Paraguay')), ('Peru', _('Peru')),
               ('Philippinen', _('Philippinen')), ('Polen', _('Polen')), ('Portugal', _('Portugal')),
               ('Ruanda', _('Ruanda')), ('Rumänien', _('Rumänien')), ('Russland', _('Russland')),
               ('Salomonen', _('Salomonen')), ('Sambia', _('Sambia')), ('Samoa', _('Samoa')),
               ('San Marino', _('San Marino')), ('São Tomé und Príncipe', _('São Tomé und Príncipe')),
               ('Saudi-Arabien', _('Saudi-Arabien')), ('Schweden', _('Schweden')), ('Schweiz', _('Schweiz')),
               ('Senegal', _('Senegal')), ('Serbien', _('Serbien')), ('Seychellen', _('Seychellen')),
               ('Sierra Leone', _('Sierra Leone')), ('Simbabwe', _('Simbabwe')), ('Singapur', _('Singapur')),
               ('Slowakei', _('Slowakei')), ('Slowenien', _('Slowenien')), ('Somalia', _('Somalia')),
               ('Somaliland', _('Somaliland')), ('Spanien', _('Spanien')), ('Sri Lanka', _('Sri Lanka')),
               ('St. Kitts und Nevis', _('St. Kitts und Nevis')), ('St. Lucia', _('St. Lucia')),
               ('St. Vincent und die Grenadinen', _('St. Vincent und die Grenadinen')), ('Südafrika', _('Südafrika')),
               ('Sudan', _('Sudan')), ('Südossetien', _('Südossetien')), ('Südsudan', _('Südsudan')),
               ('Suriname', _('Suriname')), ('Swasiland', _('Swasiland')), ('Syrien', _('Syrien')),
               ('Tadschikistan', _('Tadschikistan')), ('Tansania', _('Tansania')), ('Thailand', _('Thailand')),
               ('Togo', _('Togo')), ('Tonga', _('Tonga')), ('Transnistrien', _('Transnistrien')),
               ('Trinidad und Tobago', _('Trinidad und Tobago')), ('Tschad', _('Tschad')),
               ('Tschechien', _('Tschechien')), ('Tunesien', _('Tunesien')), ('Türkei', _('Türkei')),
               ('Turkmenistan', _('Turkmenistan')), ('Tuvalu', _('Tuvalu')), ('Uganda', _('Uganda')),
               ('Ukraine', _('Ukraine')), ('Ungarn', _('Ungarn')), ('Uruguay', _('Uruguay')),
               ('Usbekistan', _('Usbekistan')), ('Vanuatu', _('Vanuatu')), ('Vatikanstadt', _('Vatikanstadt')),
               ('Venezuela', _('Venezuela')), ('Vereinigte Arabische Emirate', _('Vereinigte Arabische Emirate')),
               ('Vereinigte Staaten', _('Vereinigte Staaten')), ('Vereinigtes Königreich', _('Vereinigtes Königreich')),
               ('Vietnam', _('Vietnam')), ('Weißrussland', _('Weißrussland')), ('Westsahara', _('Westsahara')),
               ('Zentralafrikanische Republik', _('Zentralafrikanische Republik')), ('Zypern', _('Zypern')),
               ('Grönland', _('Grönland')), ('Macua', _('Macua')), ('St. Helena', _('St. Helena')),
               ('Turks- und Caicosinseln', _('Turks- und Caicosinseln')), ('Gibralta', _('Gibralta')),
               ('Jersey', _('Jersey')), ('Guernsey', _('Guernsey')), ('Faröer', _('Faröer')),
               ('Hongkong', _('Hongkong')), ('Bermuda', _('Bermuda')), ('(Französisch-) Guayana', _('(Französisch-) Guayana')),
               ('Britische Jungferninseln', _('Britische Jungferninseln')), ('Gebiet Taiwan', _('Gebiet Taiwan'))]
    Gender = [('weiblich', _('female')), ('männlich', _('male')), ('geschlechtsneutral', _('non-binary'))]
    Biological_Sex = [('Female', _('female')), ('Male', _('male')), ('Third gender', _('non-binary'))]
    Nationality = [('afghanisch', _('afghanisch')), ('ägyptisch', _('ägyptisch')), ('albanisch', _('albanisch')),
                   ('algerisch', _('algerisch')), ('andorranisch', _('andorranisch')),
                   ('angolanisch', _('angolanisch')),
                   ('antiguanisch', _('antiguanisch')), ('äquatorialguineisch', _('äquatorialguineisch')),
                   ('argentinisch', _('argentinisch')), ('armenisch', _('armenisch')),
                   ('aserbaidschanisch', _('aserbaidschanisch')), ('äthiopisch', _('äthiopisch')),
                   ('australisch', _('australisch')), ('bahamaisch', _('bahamaisch')),
                   ('bahrainisch', _('bahrainisch')),
                   ('bangladeschisch', _('bangladeschisch')), ('barbadisch', _('barbadisch')),
                   ('belgisch', _('belgisch')),
                   ('belizisch', _('belizisch')), ('beninisch', _('beninisch')), ('bhutanisch', _('bhutanisch')),
                   ('bolivianisch', _('bolivianisch')), ('bosnisch-herzegowinisch', _('bosnisch-herzegowinisch')),
                   ('botsuanisch', _('botsuanisch')), ('brasilianisch', _('brasilianisch')),
                   ('bruneiisch', _('bruneiisch')),
                   ('bulgarisch', _('bulgarisch')), ('burkinisch', _('burkinisch')), ('burundisch', _('burundisch')),
                   ('cabo-verdisch', _('cabo-verdisch')), ('chilenisch', _('chilenisch')),
                   ('chinesisch', _('chinesisch')),
                   ('costa-ricanisch', _('costa-ricanisch')), ('ivorisch', _('ivorisch')), ('dänisch', _('dänisch')),
                   ('deutsch', _('deutsch')), ('dominikanisch', _('dominikanisch')),
                   ('dschibutisch', _('dschibutisch')),
                   ('ecuadorianisch', _('ecuadorianisch')), ('salvadorianisch', _('salvadorianisch')),
                   ('eritreisch', _('eritreisch')), ('estnisch', _('estnisch')), ('fidschianisch', _('fidschianisch')),
                   ('finnisch', _('finnisch')), ('französisch', _('französisch')), ('gabunisch', _('gabunisch')),
                   ('gambisch', _('gambisch')), ('georgisch', _('georgisch')), ('ghanaisch', _('ghanaisch')),
                   ('grenadisch', _('grenadisch')), ('griechisch', _('griechisch')),
                   ('guatemaltekisch', _('guatemaltekisch')),
                   ('guineisch', _('guineisch')), ('guinea-bissauisch', _('guinea-bissauisch')),
                   ('guyanisch', _('guyanisch')),
                   ('haitianisch', _('haitianisch')), ('honduranisch', _('honduranisch')), ('indisch', _('indisch')),
                   ('indonesisch', _('indonesisch')), ('irakisch', _('irakisch')), ('iranisch', _('iranisch')),
                   ('irisch', _('irisch')), ('isländisch', _('isländisch')), ('israelisch', _('israelisch')),
                   ('italienisch', _('italienisch')), ('jamaikanisch', _('jamaikanisch')),
                   ('japanisch', _('japanisch')),
                   ('jemenitisch', _('jemenitisch')), ('jordanisch', _('jordanisch')),
                   ('kambodschanisch', _('kambodschanisch')),
                   ('kamerunisch', _('kamerunisch')), ('kanadisch', _('kanadisch')), ('kasachisch', _('kasachisch')),
                   ('katarisch', _('katarisch')), ('kenianisch', _('kenianisch')), ('kirgisisch', _('kirgisisch')),
                   ('kiribatisch', _('kiribatisch')), ('kolumbianisch', _('kolumbianisch')),
                   ('komorisch', _('komorisch')),
                   ('kongolesisch', _('kongolesisch')),
                   ('der Demokratischen Republik Kongo', _('der Demokratischen Republik Kongo')),
                   ('der Demokratischen Volksrepublik Korea', _('der Demokratischen Volksrepublik Korea')),
                   ('der Republik Korea', _('der Republik Korea')), ('kosovarisch', _('kosovarisch')),
                   ('kroatisch', _('kroatisch')), ('kubanisch', _('kubanisch')), ('kuwaitisch', _('kuwaitisch')),
                   ('laotisch', _('laotisch')), ('lesothisch', _('lesothisch')), ('lettisch', _('lettisch')),
                   ('libanesisch', _('libanesisch')), ('liberianisch', _('liberianisch')), ('libysch', _('libysch')),
                   ('liechtensteinisch', _('liechtensteinisch')), ('litauisch', _('litauisch')),
                   ('luxemburgisch', _('luxemburgisch')), ('madagassisch', _('madagassisch')),
                   ('malawisch', _('malawisch')),
                   ('malaysisch', _('malaysisch')), ('maledivisch', _('maledivisch')), ('malisch', _('malisch')),
                   ('maltesisch', _('maltesisch')), ('marokkanisch', _('marokkanisch')),
                   ('marshallisch', _('marshallisch')),
                   ('mauretanisch', _('mauretanisch')), ('mauritisch', _('mauritisch')),
                   ('mazedonisch', _('mazedonisch')),
                   ('mexikanisch', _('mexikanisch')), ('mikronesisch', _('mikronesisch')),
                   ('moldauisch', _('moldauisch')),
                   ('monegassisch', _('monegassisch')), ('mongolisch', _('mongolisch')),
                   ('montenegrinisch', _('montenegrinisch')), ('mosambikanisch', _('mosambikanisch')),
                   ('myanmarisch', _('myanmarisch')), ('namibisch', _('namibisch')), ('nauruisch', _('nauruisch')),
                   ('nepalesisch', _('nepalesisch')), ('neuseeländisch', _('neuseeländisch')),
                   ('nicaraguanisch', _('nicaraguanisch')), ('niederländisch', _('niederländisch')),
                   ('nigrisch', _('nigrisch')),
                   ('nigerianisch', _('nigerianisch')), ('norwegisch', _('norwegisch')), ('omanisch', _('omanisch')),
                   ('österreichisch', _('österreichisch')), ('pakistanisch', _('pakistanisch')),
                   ('palauisch', _('palauisch')),
                   ('panamaisch', _('panamaisch')), ('papua-neuguineisch', _('papua-neuguineisch')),
                   ('paraguayisch', _('paraguayisch')), ('peruanisch', _('peruanisch')),
                   ('philippinisch', _('philippinisch')),
                   ('polnisch', _('polnisch')), ('portugiesisch', _('portugiesisch')), ('ruandisch', _('ruandisch')),
                   ('rumänisch', _('rumänisch')), ('russisch', _('russisch')), ('salomonisch', _('salomonisch')),
                   ('sambisch', _('sambisch')), ('samoanisch', _('samoanisch')),
                   ('san-marinesisch', _('san-marinesisch')),
                   ('são-toméisch', _('são-toméisch')), ('saudi-arabisch', _('saudi-arabisch')),
                   ('schwedisch', _('schwedisch')),
                   ('schweizerisch', _('schweizerisch')), ('senegalesisch', _('senegalesisch')),
                   ('serbisch', _('serbisch')),
                   ('seychellisch', _('seychellisch')), ('sierra-leonisch', _('sierra-leonisch')),
                   ('simbabwisch', _('simbabwisch')), ('singapurisch', _('singapurisch')),
                   ('slowakisch', _('slowakisch')),
                   ('slowenisch', _('slowenisch')), ('somalisch', _('somalisch')), ('spanisch', _('spanisch')),
                   ('sri-lankisch', _('sri-lankisch')), ('von St. Kitts und Nevis', _('von St. Kitts und Nevis')),
                   ('lucianisch', _('lucianisch')), ('vincentisch', _('vincentisch')),
                   ('südafrikanisch', _('südafrikanisch')),
                   ('sudanesisch', _('sudanesisch')), ('südsudanesisch', _('südsudanesisch')),
                   ('surinamisch', _('surinamisch')),
                   ('swasiländisch', _('swasiländisch')), ('syrisch', _('syrisch')),
                   ('tadschikisch', _('tadschikisch')),
                   ('tansanisch', _('tansanisch')), ('thailändisch', _('thailändisch')),
                   ('von Timor-Leste', _('von Timor-Leste')), ('togoisch', _('togoisch')),
                   ('tongaisch', _('tongaisch')),
                   ('von Trinidad und Tobago', _('von Trinidad und Tobago')), ('tschadisch', _('tschadisch')),
                   ('tschechisch', _('tschechisch')), ('tunesisch', _('tunesisch')), ('türkisch', _('türkisch')),
                   ('turkmenisch', _('turkmenisch')), ('tuvaluisch', _('tuvaluisch')), ('ugandisch', _('ugandisch')),
                   ('ukrainisch', _('ukrainisch')), ('ungarisch', _('ungarisch')), ('uruguayisch', _('uruguayisch')),
                   ('usbekisch', _('usbekisch')), ('vanuatuisch', _('vanuatuisch')), ('vatikanisch', _('vatikanisch')),
                   ('venezolanisch', _('venezolanisch')),
                   ('der Vereinigten Arabischen Emirate', _('der Vereinigten Arabischen Emirate')),
                   ('amerikanisch', _('amerikanisch')), ('britisch', _('britisch')),
                   ('vietnamesisch', _('vietnamesisch')),
                   ('weißrussisch', _('weißrussisch')), ('zentralafrikanisch', _('zentralafrikanisch')),
                   ('zyprisch', _('zyprisch')),
                   ('grönländisch', _('grönländisch')), ('macuanisch', _('macuanisch')),
                   ('von St. Helena', _('von St. Helena')),
                   ('von Turks- und Caicosinseln', _('von Turks- und Caicosinseln')), ('gibraltisch', _('gibraltisch')),
                   ('von Jersey', _('von Jersey')), ('guernseyer', _('guernseyer')), ('faröisch', _('faröisch')),
                   ('honkonger', _('honkonger')), ('bermudisch', _('bermudisch')),
                   ('von den britischen Jungferninseln', _('von den britischen Jungferninseln')),
                   ('taiwanesisch', _('taiwanesisch')), ('(französisch-) guayanisch', _('(französisch-) guayanisch'))]
    Language = [('German', _('Deutsch')), ('English', _('English'))]
    LanguageCode = [('German', 'DE'), ('English', 'EN')]
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
                  ('Pending', _('Pending')), ('Qualified', _('Qualifiziert')), ('Unqualified', _('Unqualifiziert')),
                  ('ISA Application Withdrawal', _('ISA Application Withdrawal'))]
    UGVStatus = [('Not applied yet', _('Not applied yet')), ('Confirmed applicant', _('Confirmed applicant')),
                 ('Rejected applicant', _('Rejected applicant')), ('Accepted applicant', _('Accepted applicant')),
                 ('Already student', _('Already student')), ('Application Withdrawal', _('Application Withdrawal'))]
    CustomerType = [('CS', 'CS'), ('CeG', 'CeG'), ('CS+CeG', 'CS+CeG')]
    ContractPeriod = [('Semester', _('Semester')), ('All Upfront', _('All Upfront')),
                      ('One year Upfront', _('One year Upfront'))]
    CaseType = [('Income Changed', _('Communicate change in income')),
                ('Personal Situation Changed', _('Communicate change of personal situation')),
                ('Provisional Exemption', _('Request temporary exemption from interim payments'))]
    CaseApproval = [('Pending', _('Pending')), ('Approved', _('Approved')), ('Not Approved', _('Not Approved'))]
    CaseStatus = [('New', _('New')), ('In Review', _('In Review')), ('Clarification Needed', _('Clarification Needed')),
                  ('Decision Reached', _('Decision Reached')), ('Closed', _('Closed'))]
    ClarifyingQuestions = [('Question 1', 'Question 1'), ('Question 2', 'Question 2'), ('Question 3', 'Question 3')]


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
    country = models.CharField(max_length=80, blank=True, null=True)
    country_0 = models.CharField(db_column='Country__c', custom=True, max_length=255, choices=Choices.Country,
                                 blank=True, null=True)

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

    link_to_further_documents = models.URLField(custom=True, verbose_name=_('Link to further Documents'), blank=True,
                                                null=True)
    risk_not_with_chancen = models.BooleanField(custom=True, db_column='RiskNotWithCHANCENeG__c',
                                                verbose_name=_('Risk not with CHANCEN eG'),
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

    shipping_street = models.TextField(blank=True, null=True, verbose_name=_('Street and House number'))
    shipping_city = models.CharField(max_length=40, blank=True, null=True, verbose_name=_('City'))
    shipping_postal_code = models.CharField(max_length=20, verbose_name=_('Zip/Postal Code'), blank=True, null=True)
    shipping_country = models.CharField(max_length=80, choices=Choices.Country, verbose_name=_('Country'), blank=True,
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
    person_mobile_phone = models.CharField(max_length=40, verbose_name='Mobile Phone', blank=True, null=True)
    phone = models.CharField(max_length=40, verbose_name='Phone', blank=True, null=True)

    person_mailing_street = models.TextField(blank=True, null=True, verbose_name=_('Street and House number'))
    person_mailing_city = models.CharField(max_length=40, blank=True, null=True, verbose_name=_('City'))
    person_mailing_postal_code = models.CharField(max_length=20, verbose_name=_('Zip/Postal Code'), blank=True,
                                                  null=True)
    person_mailing_country = models.CharField(max_length=80, choices=Choices.Country, verbose_name=_('Country'),
                                              blank=True, null=True)

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
    active_payment_helper = models.BooleanField(custom=True, default=models.DEFAULTED_ON_CREATE)
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

    # cspassword_time_pc = models.DateTimeField(db_column='CSPasswordTime__pc', verbose_name='CS Password Time',
    #                                           default=None, blank=True, null=True)
    # cspassword_token_pc = models.CharField(db_column='CSPasswordToken__pc', max_length=100,
    #                                        default='', verbose_name='CS Password Token', blank=True, null=True)
    cancel_bank_account_pc = models.BooleanField(db_column='CancelBankAccount__pc', verbose_name='Cancel Bank Account',
                                                 default=models.DEFAULTED_ON_CREATE)

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
    repayers = managers.RepayerManager()

    class Meta(models.Model.Meta):
        db_table = 'Account'
        verbose_name = _('Account')
        verbose_name_plural = _('Accounts')
        # keyPrefix = '001'

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        update_fields = update_fields or [x.attname for x in self._meta.fields if not x.primary_key]

        to_skip = []
        if self.is_person_account:
            to_skip.extend(['name'])
        else:
            to_skip.extend(['cancel_bank_account_pc'])

        for field_name in to_skip:
            update_fields.remove(field_name)

        return super(Account, self).save(force_insert=force_insert, force_update=force_update, using=using,
                                         update_fields=update_fields)

    def __str__(self):
        return self.name

    @property
    def is_student(self):
        return self.record_type.developer_name == 'Sofortzahler' or (
            self.record_type.developer_name == 'UGVStudents' and self.has_sofortzahler_contract_auto
        )

    @property
    def is_ugv_student(self):
        return self.record_type.developer_name == 'UGVStudents' and not self.has_sofortzahler_contract_auto

    @property
    def is_ugv(self):
        return self.record_type.developer_name == 'UGVStudents'

    @property
    def is_repayer(self):
        return self.record_type.developer_name == 'Ruckzahler'

    @property
    def is_repayer_or_ugv(self):
        return self.record_type.developer_name in ('Ruckzahler', 'UGVStudents')

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
    def has_payment_contact(self):
        return self.sepalastschriftmandat_erteilt_auto if self.is_repayer_or_ugv else (self.active_payment_helper or self.zahlungskontakt_ref is not None)

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
        if self.is_repayer:
            return self.initial_review_completed
        return self.initial_review_completed or self.master_contact.zahlungskontakt_auto

    def get_student_contact(self):
        if self.is_student or self.is_ugv_student or self.is_repayer:
            return self.person_contact if self.is_person_account else self.student_contact
        return None

    def get_repayer_contact(self):
        if self.is_repayer:
            return self.person_contact
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

    def get_open_cases(self):
        return self.case_set.filter(is_closed=False)

    def get_closed_cases(self):
        return self.case_set.filter(is_closed=True)


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
    phone = models.CharField(max_length=40, verbose_name='Phone', blank=True, null=True)
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
        if not self.account.is_person_account and not self._is_staff:
            rc = self.customerbankaccount_set.filter(enabled=True)
            if rc.exists():
                return rc.first()
        elif self.account.is_person_account and self.account.is_repayer_or_ugv:
            rc = self.customerbankaccount_set.filter(enabled=True)
            if rc.exists():
                return rc.first()

    @property
    def address_html(self):
        return '{self.mailing_street}<br>{self.mailing_city}, {self.mailing_postal_code}<br>{self.mailing_country}'.format(
            self=self
        )

    @property
    def is_person_account(self):
        return False


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
            translated_months = [dict(Choices.Month).get(study_month, study_month) for study_month in
                                 self.start_of_study.split(';') if study_month]
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

    # Ruckzahler

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
    period = models.CharField(custom=True, max_length=255, choices=Choices.ContractPeriod, blank=True, null=True)
    factor = models.DecimalField(custom=True, max_digits=4, decimal_places=0, blank=True, null=True)
    notice_to_quit = models.DateField(custom=True, verbose_name=_('Notice to quit'), blank=True, null=True)
    emergence = models.DateField(custom=True, blank=True, null=True)

    # Membership
    membershipnumber = models.CharField(custom=True, max_length=30, verbose_name=_('Membership number'),
                                        sf_read_only=models.READ_ONLY)
    credit_balances_account_number = models.CharField(custom=True, max_length=1300,
                                                      verbose_name=_('Credit balances account number'),
                                                      sf_read_only=models.READ_ONLY, blank=True, null=True)
    amount_of_cooperative_shares = models.DecimalField(custom=True, max_digits=10, decimal_places=0,
                                                       verbose_name=_('Amount of cooperative shares'), blank=True,
                                                       null=True)
    entry_date = models.DateField(custom=True, verbose_name=_('Entry date'), blank=True, null=True)
    nominal_value_cooperative_share = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                                          verbose_name=_('Nominal value of a cooperative share'),
                                                          default=models.DEFAULTED_ON_CREATE, blank=True, null=True)

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

    @property
    def display_name(self):
        rc = self.contract_number
        if self.is_ruckzahler:
            rc += " {} [{}]".format(self.studiengang_ref.name, self.application_form_display_name)
        return rc

    @property
    def attachment(self):
        return Attachment.objects.filter(parent_id=self.pk).last()

    @property
    def relevant_income(self):
        return self.annual_minimal_income_indexed or self.minimal_relevant_income

    @property
    def gross_income(self):
        return 28000  # self.relevant_income / Decimal('.91') / Decimal('.788')


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


class Case(models.Model):
    is_deleted = models.BooleanField(verbose_name='Deleted', sf_read_only=models.READ_ONLY, default=False)
    case_number = models.CharField(max_length=30, verbose_name=_('Case number'), sf_read_only=models.READ_ONLY)
    contact = models.ForeignKey('Contact', models.DO_NOTHING, blank=True, null=True)
    account = models.ForeignKey(Account, models.DO_NOTHING, blank=True, null=True)
    type = models.CharField(max_length=40, verbose_name=_('Case Type'), choices=Choices.CaseType, blank=False, null=True)
    record_type = models.ForeignKey('RecordType', models.DO_NOTHING, blank=True, null=True)
    status = models.CharField(max_length=40, default=models.DEFAULTED_ON_CREATE, choices=Choices.CaseStatus,
                              blank=True, null=True)
    subject = models.CharField(max_length=255, blank=False, null=True, verbose_name=_('Subject'))
    description = models.TextField(blank=True, null=True, verbose_name=_('Description'))
    is_closed = models.BooleanField(verbose_name='Closed', sf_read_only=models.READ_ONLY, default=False)
    closed_date = models.DateTimeField(sf_read_only=models.READ_ONLY, blank=True, null=True)
    is_escalated = models.BooleanField(verbose_name='Escalated', default=models.DEFAULTED_ON_CREATE)
    created_date = models.DateTimeField(sf_read_only=models.READ_ONLY)
    approval_status = models.CharField(custom=True, max_length=255, choices=Choices.CaseApproval, blank=True, null=True)

    effective_start_trig = models.DateField(custom=True, verbose_name=_('Effective Start'), blank=False, null=True)
    effective_end = models.DateField(custom=True, verbose_name=_('Effective End'), blank=True, null=True)
    relevant_income_trig = models.DecimalField(custom=True, max_digits=18, decimal_places=2,
                                               verbose_name=_('Relevant Income'), blank=True, null=True,
                                               help_text=_('Required when the Type is change of income.'))

    clarification_questions = models.CharField(custom=True, max_length=4099, choices=Choices.ClarifyingQuestions,
                                               blank=True, null=True)
    clarification_question = models.TextField(custom=True, blank=True, null=True)

    class Meta(models.Model.Meta):
        db_table = 'Case'
        verbose_name = 'Case'
        verbose_name_plural = 'Cases'
        # keyPrefix = '500'

    @property
    def is_locked(self):
        return self.status in ('In Review', 'Decision Reached', 'Closed')

    @property
    def all_questions(self):
        rc = []

        if self.clarification_questions:
            rc.extend([x for x in self.clarification_questions.split(";")])

        if self.clarification_question:
            rc.append(self.clarification_question)

        return rc


class ContentVersion(models.Model):
    content_url = models.URLField(verbose_name='Content URL', blank=True, null=True)
    version_number = models.CharField(max_length=20, sf_read_only=models.READ_ONLY, blank=True, null=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    sharing_option = models.CharField(max_length=40, verbose_name='Prevent others from sharing and unsharing', default=models.DEFAULTED_ON_CREATE, choices=[('A', 'Freeze Sharing Off'), ('R', 'Freeze Sharing On')])
    path_on_client = models.CharField(max_length=500, sf_read_only=models.NOT_UPDATEABLE, blank=True, null=True)
    rating_count = models.IntegerField(sf_read_only=models.READ_ONLY, blank=True, null=True)
    is_deleted = models.BooleanField(sf_read_only=models.READ_ONLY, default=False)
    positive_rating_count = models.IntegerField(sf_read_only=models.READ_ONLY, blank=True, null=True)
    negative_rating_count = models.IntegerField(sf_read_only=models.READ_ONLY, blank=True, null=True)
    featured_content_boost = models.IntegerField(sf_read_only=models.READ_ONLY, blank=True, null=True)
    featured_content_date = models.DateField(sf_read_only=models.READ_ONLY, blank=True, null=True)
    created_date = models.DateTimeField(sf_read_only=models.READ_ONLY)
    last_modified_date = models.DateTimeField(sf_read_only=models.READ_ONLY)
    system_modstamp = models.DateTimeField(sf_read_only=models.READ_ONLY)
    tag_csv = models.TextField(verbose_name='Tags', blank=True, null=True)
    file_type = models.CharField(max_length=20, sf_read_only=models.READ_ONLY)
    publish_status = models.CharField(max_length=40, sf_read_only=models.READ_ONLY, default='U', choices=[('U', 'Upload Interrupted'), ('P', 'Public'), ('R', 'Private Library')])
    version_data = models.TextField(blank=True, null=True)
    content_size = models.IntegerField(verbose_name='Size', sf_read_only=models.READ_ONLY, blank=True, null=True)
    file_extension = models.CharField(max_length=40, sf_read_only=models.READ_ONLY, blank=True, null=True)
    first_publish_location = models.ForeignKey(Case, models.DO_NOTHING, sf_read_only=models.NOT_UPDATEABLE, blank=True, null=True)  # Reference to tables [Account, AmazonS3Parameters__c, ApplicationUpload__c, Application__c, Asset, CalendlyWebhook__c, Campaign, Case, ChancenError__c, CollaborationGroup, Contact, ContentWorkspace, Contract, CustomerBankAccount__c, Dashboard, DashboardComponent, DegreeCourseFees__c, DegreeCourse__c, EmailMessage, EmailTemplate, ErrorLoggerEmails__c, Event, Forecast_Item__c, Forecast__c, GoCardlessAPI__c, GoCardlessEvent__c, IndexationTreshold__c, InflationValues__c, InfoRequest__c, Interview__c, InvoiceLineItem__c, Invoice__c, Lead, Log__c, Mandate__c, Opportunity, Order, OrderItem, Organization, OutgoingEmail, PandaDocParameters__c, Payment__c, Product2, ProfileSkill, ProfileSkillEndorsement, ProfileSkillUser, QandA__c, Rabatt__c, RepaymentYear__c, Report, RequestItems__c, Site, SocialPost, Solution, SystemSettings__c, Task, Topic, UGVSampleCalculation__c, User, WorkBadgeDefinition, dlrs__DeclarativeLookupRollupSummaries__c, dlrs__LookupChildAReallyReallyReallyBigBigName__c, dlrs__LookupChild__c, dlrs__LookupParent__c, dlrs__LookupRollupCalculateJob__c, dlrs__LookupRollupSummaryLog__c, dlrs__LookupRollupSummaryScheduleItems__c, dlrs__LookupRollupSummary__c, reCAPTCHAParameters__c]
    origin = models.CharField(max_length=40, verbose_name='Content Origin', sf_read_only=models.NOT_UPDATEABLE, default=models.DEFAULTED_ON_CREATE, choices=[('C', 'Content'), ('H', 'Chatter')])
    content_location = models.CharField(max_length=40, sf_read_only=models.NOT_UPDATEABLE, default=models.DEFAULTED_ON_CREATE, choices=[('S', 'Salesforce'), ('E', 'External'), ('L', 'Social Customer Service')])
    text_preview = models.CharField(max_length=255, sf_read_only=models.READ_ONLY, blank=True, null=True)
    external_document_info1 = models.CharField(max_length=1000, blank=True, null=True)
    external_document_info2 = models.CharField(max_length=1000, blank=True, null=True)
    # external_data_source = models.ForeignKey('ExternalDataSource', models.DO_NOTHING, blank=True, null=True)
    checksum = models.CharField(max_length=50, sf_read_only=models.READ_ONLY, blank=True, null=True)
    is_major_version = models.BooleanField(verbose_name='Major Version', sf_read_only=models.NOT_UPDATEABLE, default=models.DEFAULTED_ON_CREATE)
    is_asset_enabled = models.BooleanField(verbose_name='Asset File Enabled', sf_read_only=models.NOT_UPDATEABLE, default=models.DEFAULTED_ON_CREATE)
    class Meta(models.Model.Meta):
        db_table = 'ContentVersion'
        verbose_name = 'Content Version'
        verbose_name_plural = 'Content Versions'
        # keyPrefix = '068'

    @property
    def meta(self):
        return self._meta

    def fetch_content(self):
        session = connections['salesforce'].sf_session
        url = session.auth.instance_url + self.version_data
        rc = handle_api_exceptions(url, session.get)

        return rc.content



class FeedItem(models.Model):
    parent = models.ForeignKey(Case, models.DO_NOTHING, sf_read_only=models.NOT_UPDATEABLE)
    type = models.CharField(max_length=40, verbose_name='Feed Item Type', sf_read_only=models.NOT_UPDATEABLE, default="ContentPost" , blank=True, null=True)
    is_deleted = models.BooleanField(verbose_name='Deleted', sf_read_only=models.READ_ONLY, default=False)
    comment_count = models.IntegerField(sf_read_only=models.READ_ONLY)
    like_count = models.IntegerField(sf_read_only=models.READ_ONLY)
    title = models.CharField(max_length=255, blank=True, null=True)
    body = models.TextField(blank=True, null=True)
    link_url = models.URLField(sf_read_only=models.NOT_UPDATEABLE, blank=True, null=True)
    is_rich_text = models.BooleanField(default=models.DEFAULTED_ON_CREATE)
    related_record = models.ForeignKey(ContentVersion, models.DO_NOTHING, sf_read_only=models.NOT_UPDATEABLE, blank=True, null=True)
    has_content = models.BooleanField(sf_read_only=models.READ_ONLY, default=False)
    has_feed_entity = models.BooleanField(verbose_name='Has Feed Entity Attachment', sf_read_only=models.READ_ONLY, default=False)
    status = models.CharField(max_length=40, choices=[('Published', 'Published'), ('PendingReview', 'PendingReview'), ('Draft', 'Draft')], 
                              default=models.DEFAULTED_ON_CREATE, blank=True, null=True)
    class Meta(models.Model.Meta):
        db_table = 'FeedItem'
        verbose_name = 'Feed Item'
        verbose_name_plural = 'Feed Items'
        # keyPrefix = '0D5'
