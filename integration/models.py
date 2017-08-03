from __future__ import unicode_literals

from django.contrib.auth import get_user_model

from salesforce import models
from . import managers


class RecordType(models.Model):
    name = models.CharField(max_length=80)
    developer_name = models.CharField(
        max_length=80,
        verbose_name='Record Type Name')
    sobject_type = models.CharField(
        max_length=40,
        verbose_name='Sobject Type Name',
        sf_read_only=models.NOT_UPDATEABLE,
        choices=[('Account', None), ('Announcement', None), ('Asset', None), ('AssetRelationship', None), ('AssistantProgress', None), ('Campaign', None), ('CampaignMember', None), ('Case', None), ('CollaborationGroup', None), ('CollaborationGroupRecord', None), ('ComponentResponseCache', None), ('Contact', None), ('ContentVersion', None), ('Contract', None), ('CustomerBankAccount__c', None), ('DegreeCourse__c', None), ('dlrs__LookupChild__c', None), ('dlrs__LookupChildAReallyReallyReallyBigBigName__c', None), ('dlrs__LookupParent__c', None), ('dlrs__LookupRollupCalculateJob__c', None), ('dlrs__LookupRollupSummary__c', None), ('dlrs__LookupRollupSummaryLog__c', None), ('dlrs__LookupRollupSummaryScheduleItems__c', None), ('DuplicateErrorLog', None), ('DuplicateRecordItem', None), ('DuplicateRecordSet', None), ('Event', None), ('FileSearchActivity', None), ('GoCardlessEvent__c', None), ('Idea', None), ('InboundSocialPost', None), ('Invoice__c', None), ('InvoiceLineItem__c', None), ('Lead', None), ('Macro', None), ('MacroAction', None), ('MacroInstruction', None), ('ManagedContentBlock', None), ('ManagedContentBlockVersion', None), ('Mandate__c', None), ('Opportunity', None), ('Order', None), ('Payment__c', None), ('Pricebook2', None), ('Product2', None), ('ProfileSkill', None), ('ProfileSkillEndorsement', None), ('ProfileSkillUser', None), ('RecordOrigin', None), ('SearchActivity', None), ('SearchPromotionRule', None), ('SetupAssistantAnswer', None), ('SetupAssistantProgress', None), ('SocialPost', None), ('Solution', None), ('SyncTransactionLog', None), ('Task', None), ('UserMetrics', None), ('WorkAccess', None), ('WorkBadge', None), ('WorkBadgeDefinition', None), ('WorkThanks', None)])
    is_active = models.BooleanField(
        verbose_name='Active',
        sf_read_only=models.NOT_CREATEABLE,
        default=False)

    class Meta(models.Model.Meta):
        db_table = 'RecordType'
        verbose_name = 'Record Type'
        verbose_name_plural = 'Record Types'
        # keyPrefix = '012'

    def __str__(self):
        return self.name


class Account(models.Model):
    record_type = models.ForeignKey(
        RecordType,
        models.DO_NOTHING,
        blank=True,
        null=True,
        limit_choices_to={'sobject_type': 'Account'})

    is_deleted = models.BooleanField(
        verbose_name='Deleted',
        sf_read_only=models.READ_ONLY,
        default=False)
    master_record = models.ForeignKey(
        'self',
        models.DO_NOTHING,
        related_name='account_masterrecord_set',
        sf_read_only=models.READ_ONLY,
        blank=True,
        null=True)
    parent = models.ForeignKey(
        'self',
        models.DO_NOTHING,
        related_name='account_parent_set',
        blank=True,
        null=True)

    name = models.CharField(
        max_length=255,
        verbose_name='Account Name')

    hochschule_ref = models.ForeignKey(
        'self',
        models.DO_NOTHING,
        custom=True,
        related_name='account_hochschuleref_set',
        blank=True,
        null=True)
    immatrikulationsnummer = models.CharField(
        custom=True,
        max_length=255,
        blank=True,
        null=True)
    unimailadresse = models.EmailField(
        custom=True,
        blank=True,
        null=True)
    studiengebuehren_gesamt = models.DecimalField(
        custom=True,
        max_digits=18,
        decimal_places=2,
        verbose_name='Studiengebühren gesamt',
        blank=True,
        null=True)
    geschlecht = models.CharField(
        custom=True,
        max_length=255,
        choices=[('weiblich', 'weiblich'), ('männlich', 'männlich'), ('geschlechtsneutral', 'geschlechtsneutral')],
        blank=True,
        null=True)
    geburtsort = models.CharField(
        custom=True,
        max_length=255,
        blank=True,
        null=True)
    geburtsdatum = models.DateField(
        custom=True,
        blank=True,
        null=True)
    geburtsland = models.CharField(
        custom=True,
        max_length=255,
        choices=[('Abchasien', 'Abchasien'), ('Afghanistan', 'Afghanistan'), ('Ägypten', 'Ägypten'), ('Albanien', 'Albanien'), ('Algerien', 'Algerien'), ('Andorra', 'Andorra'), ('Angola', 'Angola'), ('Antigua und Barbuda', 'Antigua und Barbuda'), ('Äquatorialguinea', 'Äquatorialguinea'), ('Argentinien', 'Argentinien'), ('Armenien', 'Armenien'), ('Aserbaidschan', 'Aserbaidschan'), ('Äthiopien', 'Äthiopien'), ('Australien', 'Australien'), ('Bahamas', 'Bahamas'), ('Bahrain', 'Bahrain'), ('Bangladesch', 'Bangladesch'), ('Barbados', 'Barbados'), ('Belgien', 'Belgien'), ('Belize', 'Belize'), ('Benin', 'Benin'), ('Bergkarabach', 'Bergkarabach'), ('Bhutan', 'Bhutan'), ('Bolivien', 'Bolivien'), ('Bosnien und Herzegowina', 'Bosnien und Herzegowina'), ('Botswana', 'Botswana'), ('Brasilien', 'Brasilien'), ('Brunei', 'Brunei'), ('Bulgarien', 'Bulgarien'), ('Burkina Faso', 'Burkina Faso'), ('Burundi', 'Burundi'), ('Chile', 'Chile'), ('Republik China', 'Republik China'), ('Volksrepublik China', 'Volksrepublik China'), ('Cookinseln', 'Cookinseln'), ('Costa Rica', 'Costa Rica'), ('Dänemark', 'Dänemark'), ('Deutschland', 'Deutschland'), ('Dominica', 'Dominica'), ('Dominikanische Republik', 'Dominikanische Republik'), ('Dschibuti', 'Dschibuti'), ('Ecuador', 'Ecuador'), ('El Salvador', 'El Salvador'), ('Elfenbeinküste', 'Elfenbeinküste'), ('Eritrea', 'Eritrea'), ('Estland', 'Estland'), ('Fidschi', 'Fidschi'), ('Finnland', 'Finnland'), ('Frankreich', 'Frankreich'), ('Gabun', 'Gabun'), ('Gambia', 'Gambia'), ('Georgien', 'Georgien'), ('Ghana', 'Ghana'), ('Grenada', 'Grenada'), ('Griechenland', 'Griechenland'), ('Guatemala', 'Guatemala'), ('Guinea', 'Guinea'), ('Guinea-Bissau', 'Guinea-Bissau'), ('Guyana', 'Guyana'), ('Haiti', 'Haiti'), ('Honduras', 'Honduras'), ('Indien', 'Indien'), ('Indonesien', 'Indonesien'), ('Irak', 'Irak'), ('Iran', 'Iran'), ('Irland', 'Irland'), ('Island', 'Island'), ('Israel', 'Israel'), ('Italien', 'Italien'), ('Jamaika', 'Jamaika'), ('Japan', 'Japan'), ('Jemen', 'Jemen'), ('Jordanien', 'Jordanien'), ('Kambodscha', 'Kambodscha'), ('Kamerun', 'Kamerun'), ('Kanada', 'Kanada'), ('Kap Verde', 'Kap Verde'), ('Kasachstan', 'Kasachstan'), ('Katar', 'Katar'), ('Kenia', 'Kenia'), ('Kirgisistan', 'Kirgisistan'), ('Kiribati', 'Kiribati'), ('Kolumbien', 'Kolumbien'), ('Komoren', 'Komoren'), ('Kongo, Demokratische Republik', 'Kongo, Demokratische Republik'), ('Kongo, Republik', 'Kongo, Republik'), ('Korea, Nord', 'Korea, Nord'), ('Korea, Süd', 'Korea, Süd'), ('Kosovo', 'Kosovo'), ('Kroatien', 'Kroatien'), ('Kuba', 'Kuba'), ('Kuwait', 'Kuwait'), ('Laos', 'Laos'), ('Lesotho', 'Lesotho'), ('Lettland', 'Lettland'), ('Libanon', 'Libanon'), ('Liberia', 'Liberia'), ('Libyen', 'Libyen'), ('Liechtenstein', 'Liechtenstein'), ('Litauen', 'Litauen'), ('Luxemburg', 'Luxemburg'), ('Madagaskar', 'Madagaskar'), ('Malawi', 'Malawi'), ('Malaysia', 'Malaysia'), ('Malediven', 'Malediven'), ('Mali', 'Mali'), ('Malta', 'Malta'), ('Marokko', 'Marokko'), ('Marshallinseln', 'Marshallinseln'), ('Mauretanien', 'Mauretanien'), ('Mauritius', 'Mauritius'), ('Mazedonien', 'Mazedonien'), ('Mexiko', 'Mexiko'), ('Mikronesien', 'Mikronesien'), ('Moldawien', 'Moldawien'), ('Monaco', 'Monaco'), ('Mongolei', 'Mongolei'), ('Montenegro', 'Montenegro'), ('Mosambik', 'Mosambik'), ('Myanmar', 'Myanmar'), ('Namibia', 'Namibia'), ('Nauru', 'Nauru'), ('Nepal', 'Nepal'), ('Neuseeland', 'Neuseeland'), ('Nicaragua', 'Nicaragua'), ('Niederlande', 'Niederlande'), ('Niger', 'Niger'), ('Nigeria', 'Nigeria'), ('Niue', 'Niue'), ('Nordzypern', 'Nordzypern'), ('Norwegen', 'Norwegen'), ('Oman', 'Oman'), ('Österreich', 'Österreich'), ('Osttimor / Timor-Leste', 'Osttimor / Timor-Leste'), ('Pakistan', 'Pakistan'), ('Palästina', 'Palästina'), ('Palau', 'Palau'), ('Panama', 'Panama'), ('Papua-Neuguinea', 'Papua-Neuguinea'), ('Paraguay', 'Paraguay'), ('Peru', 'Peru'), ('Philippinen', 'Philippinen'), ('Polen', 'Polen'), ('Portugal', 'Portugal'), ('Ruanda', 'Ruanda'), ('Rumänien', 'Rumänien'), ('Russland', 'Russland'), ('Salomonen', 'Salomonen'), ('Sambia', 'Sambia'), ('Samoa', 'Samoa'), ('San Marino', 'San Marino'), ('São Tomé und Príncipe', 'São Tomé und Príncipe'), ('Saudi-Arabien', 'Saudi-Arabien'), ('Schweden', 'Schweden'), ('Schweiz', 'Schweiz'), ('Senegal', 'Senegal'), ('Serbien', 'Serbien'), ('Seychellen', 'Seychellen'), ('Sierra Leone', 'Sierra Leone'), ('Simbabwe', 'Simbabwe'), ('Singapur', 'Singapur'), ('Slowakei', 'Slowakei'), ('Slowenien', 'Slowenien'), ('Somalia', 'Somalia'), ('Somaliland', 'Somaliland'), ('Spanien', 'Spanien'), ('Sri Lanka', 'Sri Lanka'), ('St. Kitts und Nevis', 'St. Kitts und Nevis'), ('St. Lucia', 'St. Lucia'), ('St. Vincent und die Grenadinen', 'St. Vincent und die Grenadinen'), ('Südafrika', 'Südafrika'), ('Sudan', 'Sudan'), ('Südossetien', 'Südossetien'), ('Südsudan', 'Südsudan'), ('Suriname', 'Suriname'), ('Swasiland', 'Swasiland'), ('Syrien', 'Syrien'), ('Tadschikistan', 'Tadschikistan'), ('Tansania', 'Tansania'), ('Thailand', 'Thailand'), ('Togo', 'Togo'), ('Tonga', 'Tonga'), ('Transnistrien', 'Transnistrien'), ('Trinidad und Tobago', 'Trinidad und Tobago'), ('Tschad', 'Tschad'), ('Tschechien', 'Tschechien'), ('Tunesien', 'Tunesien'), ('Türkei', 'Türkei'), ('Turkmenistan', 'Turkmenistan'), ('Tuvalu', 'Tuvalu'), ('Uganda', 'Uganda'), ('Ukraine', 'Ukraine'), ('Ungarn', 'Ungarn'), ('Uruguay', 'Uruguay'), ('Usbekistan', 'Usbekistan'), ('Vanuatu', 'Vanuatu'), ('Vatikanstadt', 'Vatikanstadt'), ('Venezuela', 'Venezuela'), ('Vereinigte Arabische Emirate', 'Vereinigte Arabische Emirate'), ('Vereinigte Staaten', 'Vereinigte Staaten'), ('Vereinigtes Königreich', 'Vereinigtes Königreich'), ('Vietnam', 'Vietnam'), ('Weißrussland', 'Weißrussland'), ('Westsahara', 'Westsahara'), ('Zentral\xadafrikanische Republik', 'Zentral\xadafrikanische Republik'), ('Zypern', 'Zypern')],
        blank=True,
        null=True)
    staatsangehoerigkeit = models.CharField(
        custom=True,
        max_length=255,
        verbose_name='Staatsangehörigkeit',
        choices=[('afghanisch', 'afghanisch'), ('ägyptisch', 'ägyptisch'), ('albanisch', 'albanisch'), ('algerisch', 'algerisch'), ('andorranisch', 'andorranisch'), ('angolanisch', 'angolanisch'), ('antiguanisch', 'antiguanisch'), ('äquatorialguineisch', 'äquatorialguineisch'), ('argentinisch', 'argentinisch'), ('armenisch', 'armenisch'), ('aserbaidschanisch', 'aserbaidschanisch'), ('äthiopisch', 'äthiopisch'), ('australisch', 'australisch'), ('bahamaisch', 'bahamaisch'), ('bahrainisch', 'bahrainisch'), ('bangladeschisch', 'bangladeschisch'), ('barbadisch', 'barbadisch'), ('belgisch', 'belgisch'), ('belizisch', 'belizisch'), ('beninisch', 'beninisch'), ('bhutanisch', 'bhutanisch'), ('bolivianisch', 'bolivianisch'), ('bosnisch-herzegowinisch', 'bosnisch-herzegowinisch'), ('botsuanisch', 'botsuanisch'), ('brasilianisch', 'brasilianisch'), ('bruneiisch', 'bruneiisch'), ('bulgarisch', 'bulgarisch'), ('burkinisch', 'burkinisch'), ('burundisch', 'burundisch'), ('cabo-verdisch', 'cabo-verdisch'), ('chilenisch', 'chilenisch'), ('chinesisch', 'chinesisch'), ('costa-ricanisch', 'costa-ricanisch'), ('ivorisch', 'ivorisch'), ('dänisch', 'dänisch'), ('deutsch', 'deutsch'), ('dominikanisch', 'dominikanisch'), ('dschibutisch', 'dschibutisch'), ('ecuadorianisch', 'ecuadorianisch'), ('salvadorianisch', 'salvadorianisch'), ('eritreisch', 'eritreisch'), ('estnisch', 'estnisch'), ('fidschianisch', 'fidschianisch'), ('finnisch', 'finnisch'), ('französisch', 'französisch'), ('gabunisch', 'gabunisch'), ('gambisch', 'gambisch'), ('georgisch', 'georgisch'), ('ghanaisch', 'ghanaisch'), ('grenadisch', 'grenadisch'), ('griechisch', 'griechisch'), ('guatemaltekisch', 'guatemaltekisch'), ('guineisch', 'guineisch'), ('guinea-bissauisch', 'guinea-bissauisch'), ('guyanisch', 'guyanisch'), ('haitianisch', 'haitianisch'), ('honduranisch', 'honduranisch'), ('indisch', 'indisch'), ('indonesisch', 'indonesisch'), ('irakisch', 'irakisch'), ('iranisch', 'iranisch'), ('irisch', 'irisch'), ('isländisch', 'isländisch'), ('israelisch', 'israelisch'), ('italienisch', 'italienisch'), ('jamaikanisch', 'jamaikanisch'), ('japanisch', 'japanisch'), ('jemenitisch', 'jemenitisch'), ('jordanisch', 'jordanisch'), ('kambodschanisch', 'kambodschanisch'), ('kamerunisch', 'kamerunisch'), ('kanadisch', 'kanadisch'), ('kasachisch', 'kasachisch'), ('katarisch', 'katarisch'), ('kenianisch', 'kenianisch'), ('kirgisisch', 'kirgisisch'), ('kiribatisch', 'kiribatisch'), ('kolumbianisch', 'kolumbianisch'), ('komorisch', 'komorisch'), ('kongolesisch', 'kongolesisch'), ('der Demokratischen Republik Kongo', 'der Demokratischen Republik Kongo'), ('der Demokratischen Volksrepublik Korea', 'der Demokratischen Volksrepublik Korea'), ('der Republik Korea', 'der Republik Korea'), ('kosovarisch', 'kosovarisch'), ('kroatisch', 'kroatisch'), ('kubanisch', 'kubanisch'), ('kuwaitisch', 'kuwaitisch'), ('laotisch', 'laotisch'), ('lesothisch', 'lesothisch'), ('lettisch', 'lettisch'), ('libanesisch', 'libanesisch'), ('liberianisch', 'liberianisch'), ('libysch', 'libysch'), ('liechtensteinisch', 'liechtensteinisch'), ('litauisch', 'litauisch'), ('luxemburgisch', 'luxemburgisch'), ('madagassisch', 'madagassisch'), ('malawisch', 'malawisch'), ('malaysisch', 'malaysisch'), ('maledivisch', 'maledivisch'), ('malisch', 'malisch'), ('maltesisch', 'maltesisch'), ('marokkanisch', 'marokkanisch'), ('marshallisch', 'marshallisch'), ('mauretanisch', 'mauretanisch'), ('mauritisch', 'mauritisch'), ('mazedonisch', 'mazedonisch'), ('mexikanisch', 'mexikanisch'), ('mikronesisch', 'mikronesisch'), ('moldauisch', 'moldauisch'), ('monegassisch', 'monegassisch'), ('mongolisch', 'mongolisch'), ('montenegrinisch', 'montenegrinisch'), ('mosambikanisch', 'mosambikanisch'), ('myanmarisch', 'myanmarisch'), ('namibisch', 'namibisch'), ('nauruisch', 'nauruisch'), ('nepalesisch', 'nepalesisch'), ('neuseeländisch', 'neuseeländisch'), ('nicaraguanisch', 'nicaraguanisch'), ('niederländisch', 'niederländisch'), ('nigrisch', 'nigrisch'), ('nigerianisch', 'nigerianisch'), ('norwegisch', 'norwegisch'), ('omanisch', 'omanisch'), ('österreichisch', 'österreichisch'), ('pakistanisch', 'pakistanisch'), ('palauisch', 'palauisch'), ('panamaisch', 'panamaisch'), ('papua-neuguineisch', 'papua-neuguineisch'), ('paraguayisch', 'paraguayisch'), ('peruanisch', 'peruanisch'), ('philippinisch', 'philippinisch'), ('polnisch', 'polnisch'), ('portugiesisch', 'portugiesisch'), ('ruandisch', 'ruandisch'), ('rumänisch', 'rumänisch'), ('russisch', 'russisch'), ('salomonisch', 'salomonisch'), ('sambisch', 'sambisch'), ('samoanisch', 'samoanisch'), ('san-marinesisch', 'san-marinesisch'), ('são-toméisch', 'são-toméisch'), ('saudi-arabisch', 'saudi-arabisch'), ('schwedisch', 'schwedisch'), ('schweizerisch', 'schweizerisch'), ('senegalesisch', 'senegalesisch'), ('serbisch', 'serbisch'), ('seychellisch', 'seychellisch'), ('sierra-leonisch', 'sierra-leonisch'), ('simbabwisch', 'simbabwisch'), ('singapurisch', 'singapurisch'), ('slowakisch', 'slowakisch'), ('slowenisch', 'slowenisch'), ('somalisch', 'somalisch'), ('spanisch', 'spanisch'), ('sri-lankisch', 'sri-lankisch'), ('von St. Kitts und Nevis', 'von St. Kitts und Nevis'), ('lucianisch', 'lucianisch'), ('vincentisch', 'vincentisch'), ('südafrikanisch', 'südafrikanisch'), ('sudanesisch', 'sudanesisch'), ('südsudanesisch', 'südsudanesisch'), ('surinamisch', 'surinamisch'), ('swasiländisch', 'swasiländisch'), ('syrisch', 'syrisch'), ('tadschikisch', 'tadschikisch'), ('tansanisch', 'tansanisch'), ('thailändisch', 'thailändisch'), ('von Timor-Leste', 'von Timor-Leste'), ('togoisch', 'togoisch'), ('tongaisch', 'tongaisch'), ('von Trinidad und Tobago', 'von Trinidad und Tobago'), ('tschadisch', 'tschadisch'), ('tschechisch', 'tschechisch'), ('tunesisch', 'tunesisch'), ('türkisch', 'türkisch'), ('turkmenisch', 'turkmenisch'), ('tuvaluisch', 'tuvaluisch'), ('ugandisch', 'ugandisch'), ('ukrainisch', 'ukrainisch'), ('ungarisch', 'ungarisch'), ('uruguayisch', 'uruguayisch'), ('usbekisch', 'usbekisch'), ('vanuatuisch', 'vanuatuisch'), ('vatikanisch', 'vatikanisch'), ('venezolanisch', 'venezolanisch'), ('der Vereinigten Arabischen Emirate', 'der Vereinigten Arabischen Emirate'), ('amerikanisch', 'amerikanisch'), ('britisch', 'britisch'), ('vietnamesisch', 'vietnamesisch'), ('weißrussisch', 'weißrussisch'), ('zentralafrikanisch', 'zentralafrikanisch'), ('zyprisch', 'zyprisch')],
        blank=True,
        null=True)
    kommunikationssprache = models.CharField(
        custom=True,
        max_length=255,
        choices=[('deutsch', 'deutsch'), ('englisch', 'englisch')],
        blank=True,
        null=True)

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


class Contact(models.Model):
    record_type = models.ForeignKey(
        RecordType,
        models.DO_NOTHING,
        blank=True,
        null=True,
        limit_choices_to={'sobject_type': 'Contact'})
    is_deleted = models.BooleanField(
        verbose_name='Deleted',
        sf_read_only=models.READ_ONLY,
        default=False)
    master_record = models.ForeignKey(
        'self', models.DO_NOTHING,
        related_name='contact_masterrecord_set',
        sf_read_only=models.READ_ONLY,
        blank=True,
        null=True)

    account = models.ForeignKey(
        Account,
        models.DO_NOTHING,
        blank=True,
        null=True)  # Master Detail Relationship *

    last_name = models.CharField(max_length=80)
    first_name = models.CharField(max_length=40, blank=True, null=True)
    salutation = models.CharField(
        max_length=40,
        choices=[('Mr.', 'Herr'), ('Ms.', 'Frau'), ('Mrs.', 'Frau'), ('Dr.', 'Dr.'), ('Prof.', 'Prof.')],
        blank=True,
        null=True)
    name = models.CharField(
        max_length=121,
        verbose_name='Full Name',
        sf_read_only=models.READ_ONLY)

    title = models.CharField(
        max_length=128,
        blank=True,
        null=True)
    email = models.EmailField(
        blank=True,
        null=True)
    mobile_phone = models.CharField(
        max_length=40,
        blank=True,
        null=True)
    home_phone = models.CharField(
        max_length=40,
        blank=True,
        null=True)
    other_phone = models.CharField(
        max_length=40,
        blank=True,
        null=True)

    bic = models.CharField(
        custom=True,
        db_column='BIC__c',
        max_length=255,
        verbose_name='BIC',
        blank=True,
        null=True)
    iban = models.CharField(
        custom=True,
        db_column='IBAN__c',
        max_length=255,
        verbose_name='IBAN',
        blank=True,
        null=True)
    kontoinhaber = models.CharField(
        custom=True,
        max_length=255,
        blank=True,
        null=True)

    cspassword_token = models.CharField(
        custom=True,
        db_column='CSPasswordToken__c',
        max_length=50,
        verbose_name='CS Password Token',
        blank=True,
        null=True)

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
        super(Contact, self).save(*args, **kwargs)
        if Contact.university_staff.filter(email=self.email).exists():
            new_user = get_user_model()(email=self.email, is_active=False)
            new_user.save()
            new_user.create_token()
            # newpass_token = UserToken(user=new_user, expires_at=timezone.now())


class Contract(models.Model):
    record_type = models.ForeignKey(
        RecordType,
        models.DO_NOTHING,
        blank=True,
        null=True,
        limit_choices_to={'sobject_type': 'Contract'})
    is_deleted = models.BooleanField(
        verbose_name='Deleted',
        sf_read_only=models.READ_ONLY,
        default=False)

    account = models.ForeignKey(
        Account,
        models.DO_NOTHING,
        related_name='contract_account_set')  # Master Detail Relationship *

    university_ref = models.ForeignKey(
        Account,
        models.DO_NOTHING,
        custom=True,
        related_name='contract_universityref_set',
        blank=True,
        null=True)
    #studiengang_ref = models.ForeignKey(
    #    'DegreeCourse',
    #    models.DO_NOTHING,
    #    custom=True,
    #    blank=True,
    #    null=True)
    payment_interval = models.CharField(
        custom=True,
        max_length=255,
        verbose_name='Zahlungsfrequenz',
        choices=[('Zu Beginn jeden Monats', 'Zu Beginn jeden Monats'), ('Zu Beginn jeden Semesters', 'Zu Beginn jeden Semesters')],
        blank=True,
        null=True)

    class Meta(models.Model.Meta):
        db_table = 'Contract'
        verbose_name = 'Contract'
        verbose_name_plural = 'Contracts'
        # keyPrefix = '800'


class Rabatt(models.Model):
    is_deleted = models.BooleanField(
        verbose_name='Deleted',
        sf_read_only=models.READ_ONLY,
        default=False)
    name = models.CharField(
        max_length=80,
        verbose_name='Rabatt',
        sf_read_only=models.READ_ONLY)
    contract = models.ForeignKey(
        Contract,
        models.DO_NOTHING,
        custom=True,
        sf_read_only=models.NOT_UPDATEABLE)  # Master Detail Relationship 0
    discount_type = models.CharField(
        custom=True,
        max_length=255,
        choices=[('Discount Tuition Fee', 'Discount Tuition Fee'), ('Discount Semester Fee', 'Discount Semester Fee')],
        blank=True,
        null=True)
    discount_tuition_fee = models.DecimalField(
        custom=True,
        max_digits=18,
        decimal_places=2,
        verbose_name='Rabatt auf Studiengang',
        blank=True,
        null=True)
    discount_semester_fee = models.DecimalField(
        custom=True,
        max_digits=18,
        decimal_places=0,
        verbose_name='Rabatt auf Semesterbeitrag',
        blank=True,
        null=True)
    applicable_months = models.DecimalField(
        custom=True,
        max_digits=3,
        decimal_places=0,
        verbose_name='Anzahl anwendbarer Monate',
        blank=True,
        null=True)
    utilization = models.DecimalField(
        custom=True,
        max_digits=18,
        decimal_places=0,
        verbose_name='Anzahl Anwendungen',
        blank=True,
        null=True)
    active = models.BooleanField(
        custom=True,
        verbose_name='Aktiv',
        default=models.DEFAULTED_ON_CREATE)

    class Meta(models.Model.Meta):
        db_table = 'Rabatt__c'
        verbose_name = 'Rabatt'
        verbose_name_plural = 'Rabatte'
        # keyPrefix = 'a0H'


