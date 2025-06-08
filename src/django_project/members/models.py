from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from handyhelpers.models import HandyHelperBaseModel


class MemberManager(BaseUserManager):
    def create_user(self, email: str, password: str | None = None, **extra_fields: dict) -> "Member":
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields) -> "Member":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class Member(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    career_level = models.ForeignKey("members.CareerLevel", blank=True, null=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=64, blank=True)
    first_name = models.CharField(max_length=16, blank=True)
    last_name = models.CharField(max_length=16, blank=True)
    zip_code = models.CharField(max_length=9, blank=True)
    city = models.CharField(max_length=32, blank=True)
    state = models.CharField(max_length=2, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = MemberManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    def __str__(self) -> str:
        return self.email


class CareerLevel(HandyHelperBaseModel):
    name = models.CharField(max_length=16, unique=True)
    description = models.CharField(max_length=128, blank=True, null=True)
    enabled = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name


class MemberInterest(HandyHelperBaseModel):
    member = models.ForeignKey("members.Member", on_delete=models.CASCADE)
    interest = models.ForeignKey("members.TechnicalArea", on_delete=models.CASCADE)
    interest_level = models.IntegerField(default=1, help_text="1 to 5")

    def __str__(self) -> str:
        return f"{self.member} interested in {self.interest.name}"


class MemberLink(HandyHelperBaseModel):
    member = models.ForeignKey("members.Member", on_delete=models.CASCADE)
    name = models.CharField(max_length=32)
    description = models.TextField(blank=True, null=True)
    url = models.URLField()
    is_public = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.name} ({'public' if self.is_public else 'private'})"


class MemberSkill(HandyHelperBaseModel):
    member = models.ForeignKey("members.Member", on_delete=models.CASCADE)
    skill = models.ForeignKey("members.TechnicalArea", on_delete=models.CASCADE)
    level = models.ForeignKey("members.SkillLevel", blank=True, null=True, on_delete=models.SET_NULL)
    yoe = models.IntegerField(blank=True, null=True, help_text="Years of Experience")

    def __str__(self) -> str:
        return f"{self.member} skilled in {self.skill.name}"


class SkillLevel(HandyHelperBaseModel):
    name = models.CharField(max_length=16, unique=True)
    description = models.CharField(max_length=128, blank=True, null=True)
    enabled = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name


class TechnicalArea(HandyHelperBaseModel):
    name = models.CharField(max_length=32, unique=True)
    description = models.CharField(max_length=128, blank=True, null=True)

    def __str__(self) -> str:
        return self.name
