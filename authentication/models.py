from django.db import models
from django.utils import timezone

from datetime import timedelta
from uuid import uuid4

from authtools.models import AbstractEmailUser

from integration.models import Account, Contact


class User(AbstractEmailUser):

    class Meta:
        swappable = 'AUTH_USER_MODEL'

    def is_student(self):
        return Account.students.filter(unimailadresse=self.email).exists()

    def is_unistaff(self):
        # Todo: check properly
        return Contact.objects.filter(email=self.email)

    def create_token(self, token=None, hours=48):
        token = token or uuid4()
        exipiry_date = timezone.now() + timedelta(hours=hours)

        self.perishabletoken_set.create(token=token, expires_at=exipiry_date)


class PerishableToken(models.Model):
    user = models.ForeignKey(User)

    token = models.CharField(max_length=50)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return self.expires_at < timezone.now()
