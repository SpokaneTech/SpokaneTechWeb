import json
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


class EditModalView(BuildBootstrapModalView):
    """ """

    form = None  # type: ignore
    form_display: str = "bs5"
    modal_button_submit: str = "Update"
    modal_title: str | None = None
    model = Member
    toast_message_fail: str | None = None
    toast_message_success: str | None = None

    def get(self, request, *args, **kwargs) -> HttpResponse | Any:
        instance = self.model.objects.get(pk=kwargs["pk"])
        if not self.is_htmx():
            return HttpResponse("Invalid request", status=400)
        if not self.form:
            return HttpResponse("Invalid request", status=400)

        form_errors: Any = request.session.get(f"{self.form.__name__}__errors")
        if self.form and form_errors:
            data: Any = request.session.get(f"{self.form.__name__}__data")
            form: Never = self.form()
            form.data = data
            for field, error_message in form_errors.items():
                try:
                    form.add_error(field, error_message)
                except KeyError:
                    pass
        else:
            # Fetch related TechnicalArea pks for member skills and interests
            skills_qs = MemberSkill.objects.filter(member=instance).values_list("skill__pk", flat=True)
            interests_qs = MemberInterest.objects.filter(member=instance).values_list("interest__pk", flat=True)

            form = self.form(
                initial={
                    "first_name": instance.first_name,
                    "last_name": instance.last_name,
                    "title": getattr(instance, "title", ""),
                    "zip_code": instance.zip_code,
                    "memberskills": list(skills_qs),
                    "interests": list(interests_qs),
                }
            )

        self.form.hx_post = f"/members/{instance.pk}/update/"
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
                member = self.model.objects.get(pk=kwargs["pk"])

                # Update Member fields
                for field in ["title", "first_name", "last_name", "zip_code"]:
                    setattr(member, field, form.cleaned_data[field])
                member.save()

                # Handle MemberSkill relationship
                member.memberskill_set.all().delete()
                for skill in form.cleaned_data.get("memberskills", []):
                    MemberSkill.objects.create(member=member, skill=skill)

                # Handle MemberInterest relationship
                member.memberinterest_set.all().delete()
                for interest in form.cleaned_data.get("interests", []):
                    MemberInterest.objects.create(member=member, interest=interest)

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
            form_error_dict = {k: str(v[0].messages[0]) for k, v in form.errors.as_data().items()}
            request.session[f"{self.form.__name__}__errors"] = form_error_dict
            request.session[f"{self.form.__name__}__data"] = form.data
            response = HttpResponse(status=400)
            response["X-Toast-Message"] = (
                f"""<span class="text-danger">{self.toast_message_fail}</span>"""
                or f"""<span class="text-danger">Failed to update {self.form.Meta.model._meta.object_name}</span>"""
            )
            return response


class UpdateMemberModalView(EditModalView):
    """Update an existing Member entry"""

    form = UpdateMemberForm  # type: ignore
    modal_title: str = "Update your profile"
    toast_message_success: str = "Profile updated successfully"
    toast_message_fail: str = "Failed to update profile"


def interests_partial(request, pk) -> HttpResponse:
    member: Member = get_object_or_404(Member, pk=pk)
    return render(request, "members/partials/member_interests.htm", {"object": member})


def skills_partial(request, pk) -> HttpResponse:
    member: Member = get_object_or_404(Member, pk=pk)
    return render(request, "members/partials/member_skills.htm", {"object": member})
