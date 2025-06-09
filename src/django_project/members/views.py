import json
import logging
from collections import Counter
from typing import Any, Never

from django.db.models import Count
from django.db.models.manager import BaseManager
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from handyhelpers.views.htmx import (
    BuildBootstrapModalView,
    HtmxOnlyView,
    HtmxOptionDetailView,
    HtmxOptionMultiFilterView,
    HtmxOptionView,
)
from members.forms import UpdateMemberForm

# import models
from members.models import Member, MemberInterest, MemberSkill

logger = logging.getLogger(__name__)


class LogInView(HtmxOptionView):
    """Render the 'login' page"""

    htmx_template_name: str = "members/partials/custom/login.htm"
    template_name: str = "members/full/custom/login.html"


class DetailMemberView(HtmxOptionDetailView):
    """Render the member profile page"""

    model = Member
    htmx_template_name: str = "members/partials/detail/member.htm"
    template_name: str = "members/full/detail/member.html"


class ListMembersView(HtmxOptionMultiFilterView):
    """Render the member list page"""

    model = Member
    htmx_table_template_name: str = "members/partials/table/members.htm"
    template_name: str = "members/full/list/members.html"


class MemberStatsView(HtmxOptionView):
    """Render the member statistics page"""

    htmx_template_name: str = "members/partials/custom/stats.htm"
    template_name: str = "members/full/custom/stats.html"


class MemberStatsByCityView(HtmxOnlyView):
    """Render the member statistics by city page"""

    htmx_template_name: str = "members/partials/charts/stats_by_city.htm"

    def get(self, request) -> HttpResponse:
        members: BaseManager[Member] = Member.objects.exclude(city__isnull=True).exclude(city__exact="")
        data_counts = Counter(members.values_list("city", flat=True))
        labels = list(data_counts.keys())
        data = list(data_counts.values())
        self.context: dict[str, str] = {
            "chart_title": "Members by City",
            "chart_labels": json.dumps(labels),
            "chart_data": json.dumps(data),
        }
        return super().get(request)


class MemberStatsByZipCodeView(HtmxOnlyView):
    """Render the member statistics by zip code page"""

    htmx_template_name: str = "members/partials/charts/stats_by_zip.htm"

    def get(self, request) -> HttpResponse:
        members: BaseManager[Member] = Member.objects.exclude(zip_code__isnull=True).exclude(zip_code__exact="")
        data_counts = Counter(members.values_list("zip_code", flat=True))
        labels = list(data_counts.keys())
        data = list(data_counts.values())
        self.context: dict[str, str] = {
            "chart_title": "Members by Zip Code",
            "chart_labels": json.dumps(labels),
            "chart_data": json.dumps(data),
        }
        return super().get(request)


class MemberStatsByInterestView(HtmxOnlyView):
    """Render the member statistics by interest page"""

    htmx_template_name: str = "members/partials/charts/stats_by_interest.htm"

    def get(self, request) -> HttpResponse:
        data_counts = MemberInterest.objects.values("interest__name").annotate(count=Count("id")).order_by("-count")
        labels = [entry["interest__name"] for entry in data_counts]
        data = [entry["count"] for entry in data_counts]
        self.context = {
            "chart_labels": json.dumps(labels),
            "chart_data": json.dumps(data),
            "chart_title": "Members by Interests",
        }
        return super().get(request)


class MemberStatsBySkillView(HtmxOnlyView):
    """Render the member statistics by interest page"""

    htmx_template_name: str = "members/partials/charts/stats_by_skill.htm"

    def get(self, request) -> HttpResponse:
        data_counts = MemberSkill.objects.values("skill__name").annotate(count=Count("id")).order_by("-count")
        labels = [entry["skill__name"] for entry in data_counts]
        data = [entry["count"] for entry in data_counts]
        self.context = {
            "chart_labels": json.dumps(labels),
            "chart_data": json.dumps(data),
            "chart_title": "Members by Skill",
        }
        return super().get(request)


class MemberStatsByCareerLevelView(HtmxOnlyView):
    """Render a chart showing number of members per career level."""

    htmx_template_name = "members/partials/charts/stats_by_career_level.htm"

    def get(self, request, *args, **kwargs) -> HttpResponse:
        career_counts = (
            Member.objects.filter(career_level__isnull=False)
            .values("career_level__name")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        labels: list[str] = [entry["career_level__name"] for entry in career_counts]
        data: list[int] = [entry["count"] for entry in career_counts]

        self.context = {
            "chart_labels": json.dumps(labels),
            "chart_data": json.dumps(data),
            "chart_title": "Members by Career Level",
        }

        return super().get(request)


class UpdateModalView(BuildBootstrapModalView):
    """ """

    field_list: list[str] = []
    form = None  # type: ignore
    form_display: str = "bs5"
    modal_button_submit: str = "Update"
    modal_title: str | None = None
    toast_message_fail: str | None = None
    toast_message_success: str | None = None

    def _get_reverse_fk_field_names(self, instance, allowed_models) -> list:
        return [
            rel.get_accessor_name()
            for rel in instance._meta.get_fields()
            if rel.one_to_many and rel.auto_created and rel.related_model in allowed_models
        ]

    def _get_form_field_dict(self, form) -> dict:
        if self.form:
            return self.form().fields
        return {}

    def _get_field_queryset(self, field_name: str, model_instance, data) -> Any:
        pass

    def _build_initial_data(self, form, model_instance, data) -> dict:
        initial_data: dict = {}
        for field_name, field in self._get_form_field_dict(form):
            model_field: Any | None = getattr(field, "model_field", None)
            if model_field:
                continue
            elif field in self.field_list:
                initial_data[field] = data.get(field_name, model_instance.__dict__.get(field_name, None))
            else:
                initial_data[field] = data.get(field, None)
        return initial_data

    def get(self, request, *args, **kwargs) -> HttpResponse | Any:
        if self.form:
            instance: Any = self.form.Meta.model.objects.get(pk=kwargs["pk"])
        if not self.is_htmx():
            return HttpResponse("Invalid request", status=400)
        if not self.form:
            return HttpResponse("Invalid request", status=400)

        form_errors: Any = request.session.get(f"{self.form.__name__}__errors")
        data: Any = request.session.get(f"{self.form.__name__}__data")

        if data and data.get("interests", None):
            int_pks: list[int] = [int(pk) for pk in data["interests"]]
            interests_qs = (
                MemberInterest.objects.filter(interest__pk__in=int_pks)
                .distinct()
                .values_list("interest__pk", flat=True)
            )
        else:
            interests_qs = MemberInterest.objects.filter(member=instance).values_list("interest__pk", flat=True)

        if data and data.get("skills", None):
            int_pks = [int(pk) for pk in data["skills"]]
            skills_qs = MemberSkill.objects.filter(skill__pk__in=int_pks).distinct().values_list("skill__pk", flat=True)
        else:
            skills_qs = MemberSkill.objects.filter(member=instance).values_list("skill__pk", flat=True)

        if self.form and form_errors:
            form: Never = self.form()
            form.data = data

            form = self.form(
                initial={
                    "first_name": data.get("first_name", instance.first_name),
                    "last_name": data.get("last_name", instance.last_name),
                    "title": data.get("title", getattr(instance, "title", "")),
                    "zip_code": data.get("zip_code", instance.zip_code),
                    "skills": list(skills_qs),
                    "interests": list(interests_qs),
                }
            )

            for field, error_message in form_errors.items():
                try:
                    form.add_error(field, error_message)
                except Exception as err:
                    logger.error(f"Failed to add error to form field '{field}': {err}")

        else:
            form = self.form(
                initial={
                    "first_name": instance.first_name,
                    "last_name": instance.last_name,
                    "title": getattr(instance, "title", ""),
                    "zip_code": instance.zip_code,
                    "skills": list(skills_qs),
                    "interests": list(interests_qs),
                }
            )

        self.form.hx_post = self.hx_post_url.format(pk=instance.pk)
        context: dict[str, Any] = {
            "modal_title": (
                self.modal_title if self.modal_title else f"Update {self.form.Meta.model._meta.object_name}"
            ),
            "modal_subtitle": self.modal_subtitle,
            "modal_body": self.modal_body,
            "modal_size": self.modal_size,
            "modal_button_close": self.modal_button_close,
            "modal_button_submit": self.modal_button_submit,
            "data": self.data,
            "extra_data": self.extra_data,
            "form": form,
            "form_display": self.form_display,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs) -> HttpResponse:
        form = self.form(request.POST) if self.form else None
        if form:
            if form.is_valid():
                instance = self.form.Meta.model.objects.get(pk=kwargs["pk"])

                for field in form.Meta.fields:
                    setattr(instance, field, form.cleaned_data[field])
                instance.save()

                for entry in self.form.related_fields_list:
                    entry["model"].objects.filter(**{self.form.Meta.model._meta.model_name: instance}).delete()

                    for item in form.cleaned_data.get(entry["form_field"], []):
                        entry["model"].objects.create(
                            **{entry["model_field"]: item, self.form.Meta.model._meta.model_name: instance}
                        )

                response = HttpResponse(status=204)
                response["X-Toast-Message"] = (
                    self.toast_message_success or f"Updated {self.form.Meta.model._meta.object_name}"
                )
                response["X-Member-Updated"] = "true"
                # Cleanup session errors/data
                request.session.pop(f"{self.form.__name__}__errors", None)
                request.session.pop(f"{self.form.__name__}__data", None)
                return response

            # Handle invalid form
            form_error_dict: dict[Any, str] = {k: str(v[0].messages[0]) for k, v in form.errors.as_data().items()}
            post_dict = dict(request.POST.lists())
            session_form_data: dict = {}
            for field in form.Meta.fields:
                session_form_data[field] = form.data[field]

            for related_field in self.form.related_fields_list:
                if related_field["form_field"] in post_dict:
                    session_form_data[related_field["form_field"]] = post_dict[related_field["form_field"]]
                else:
                    session_form_data[related_field["form_field"]] = []

            request.session[f"{self.form.__name__}__errors"] = form_error_dict
            request.session[f"{self.form.__name__}__data"] = session_form_data

            response = HttpResponse(status=400)
            response["X-Toast-Message"] = (
                f"""<span class="text-danger">{self.toast_message_fail}</span>"""
                or f"""<span class="text-danger">Failed to update {self.form.Meta.model._meta.object_name}</span>"""
            )
            return response


class UpdateMemberModalView(UpdateModalView):
    """Update an existing Member entry"""

    form = UpdateMemberForm  # type: ignore
    hx_post_url: str = "/members/{pk}/update/"
    modal_title: str = "Update your profile"
    toast_message_success: str = "Profile updated successfully"
    toast_message_fail: str = "Failed to update profile"


def interests_partial(request, pk) -> HttpResponse:
    member: Member = get_object_or_404(Member, pk=pk)
    return render(request, "members/partials/member_interests.htm", {"object": member})


def skills_partial(request, pk) -> HttpResponse:
    member: Member = get_object_or_404(Member, pk=pk)
    return render(request, "members/partials/member_skills.htm", {"object": member})
