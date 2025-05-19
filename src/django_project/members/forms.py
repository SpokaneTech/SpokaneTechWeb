# members/forms.py
from typing import Any

from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from handyhelpers.forms import HtmxForm
from members.models import Member, MemberInterest, MemberSkill, TechnicalArea


class MemberCreationForm(forms.ModelForm):
    """Form for creating new members (in admin panel)."""

    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Password confirmation", widget=forms.PasswordInput)

    class Meta:
        model = Member
        fields: tuple[str, ...] = ("email", "first_name", "last_name", "zip_code")

    def clean_password2(self) -> Any | None:
        password1: Any | None = self.cleaned_data.get("password1")
        password2: Any | None = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True) -> Any:
        member: Any = super().save(commit=False)
        member.set_password(self.cleaned_data["password1"])
        if commit:
            member.save()
        return member


class MemberChangeForm(forms.ModelForm):
    """Form for updating members (in admin panel)."""

    password = ReadOnlyPasswordHashField()

    class Meta:
        model = Member
        fields: tuple[str, ...] = (
            "email",
            "first_name",
            "last_name",
            "zip_code",
            "password",
            "is_active",
            "is_staff",
            "is_superuser",
        )

    def clean_password(self):  # -> Any:
        return self.initial["password"]


class FormUtilsMixin:
    def get_non_model_multiple_choice_fields(form_class) -> list:
        return [
            name
            for name, field in form_class.base_fields.items()
            if not isinstance(field, forms.ModelMultipleChoiceField)
        ]

    def get_model_multiple_choice_fields(form_class) -> list:
        return [
            name for name, field in form_class.base_fields.items() if isinstance(field, forms.ModelMultipleChoiceField)
        ]


class UpdateMemberForm(FormUtilsMixin, HtmxForm):
    hx_target: str = "member-form"
    submit_button_text: str = "update"

    class Meta:
        fields: list[str] = ["title", "first_name", "last_name", "zip_code"]
        model: type[Member] = Member

    first_name = forms.CharField(max_length=16, required=True, label="First Name")
    last_name = forms.CharField(max_length=16, required=True, label="Last Name")
    title = forms.CharField(max_length=64, required=False, label="Title")
    zip_code = forms.CharField(max_length=9, required=True, label="Zip Code")

    skills = forms.ModelMultipleChoiceField(
        queryset=TechnicalArea.objects.all().order_by("name"),
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-control", "size": "2"}),
        required=False,
        label="Skills",
    )

    interests = forms.ModelMultipleChoiceField(
        queryset=TechnicalArea.objects.all().order_by("name"),
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-control", "size": "3"}),
        required=False,
        label="Interests",
    )

    related_fields_list: list = [
        {
            "model": MemberInterest,
            "model_field": "interest",
            "form_field": "interests",
        },
        {
            "model": MemberSkill,
            "model_field": "skill",
            "form_field": "skills",
        },
    ]

    # def __init__(self, *args, **kwargs) -> None:
    #     super().__init__(*args, **kwargs)
    #     self.fields["interests"].model_field = "interest"
    #     self.fields["skills"].model_field = "skill"
