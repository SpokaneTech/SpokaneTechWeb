from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import MemberChangeForm, MemberCreationForm
from .models import (
    Member,
    MemberInterest,
    MemberLink,
    MemberSkill,
    SkillLevel,
    TechnicalArea,
)


@admin.register(Member)
class MemberAdmin(UserAdmin):
    model = Member
    add_form = MemberCreationForm
    form = MemberChangeForm
    list_display = ("pk", "email", "first_name", "last_name", "city", "zip_code", "date_joined", "last_login")
    search_fields = ("email", "first_name", "last_name", "city", "zip_code")
    list_filter = ("is_active", "is_staff", "is_superuser", "city")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "zip_code")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important Dates", {"fields": ("last_login",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "is_staff", "is_superuser"),
            },
        ),
    )

    ordering = ("email",)


@admin.register(MemberInterest)
class MemberInterestAdmin(admin.ModelAdmin):
    list_display: list[str] = ["id", "member", "interest", "interest_level"]
    search_fields: list[str] = ["member__email", "interest__name", "interest_level__name"]
    list_filter: list[str] = ["member", "interest", "interest_level"]
    ordering: list[str] = ["member"]


@admin.register(MemberLink)
class MemberLinkAdmin(admin.ModelAdmin):
    list_display: list[str] = ["id", "member", "name", "description"]
    search_fields: list[str] = ["member__email", "link__name"]
    list_filter: list[str] = ["member__email", "name", "description"]
    ordering: list[str] = ["member"]


@admin.register(MemberSkill)
class MemberSkillAdmin(admin.ModelAdmin):
    list_display: list[str] = ["id", "member", "skill", "level", "yoe"]
    search_fields: list[str] = ["member__email", "skill__name", "skill_level__name"]
    list_filter: list[str] = ["member", "skill", "level"]
    ordering: list[str] = ["member"]


@admin.register(SkillLevel)
class SkillLevelAdmin(admin.ModelAdmin):
    list_display: list[str] = ["id", "name", "description"]
    search_fields: list[str] = ["name", "description"]
    list_filter: list[str] = ["name"]
    ordering: list[str] = ["name"]


@admin.register(TechnicalArea)
class TechnicalAreaAdmin(admin.ModelAdmin):
    list_display: list[str] = ["id", "name", "description"]
    search_fields: list[str] = ["name", "description"]
    list_filter: list[str] = ["name"]
    ordering: list[str] = ["name"]
