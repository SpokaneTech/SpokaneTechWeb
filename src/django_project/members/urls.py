from django.urls import path, re_path
from django.urls.resolvers import URLPattern
from members import views

app_name = "members"

urlpatterns: list[URLPattern] = [
    path("login/", views.LogInView.as_view(), name="login"),
    path("stats/", views.MemberStatsView.as_view(), name="stats"),
    path("members/<int:pk>", views.DetailMemberView.as_view(), name="detail_member"),
    re_path("^members/(?P<display>\w+)?/$", views.ListMembersView.as_view(), name="list_members"),
    path("members/", views.ListMembersView.as_view(), name="list_members"),
    path("members/<int:pk>/update/", views.UpdateMemberModalView.as_view(), name="update_member"),
    # statistics views
    path("stats_by_city/", views.MemberStatsByCityView.as_view(), name="stats_by_city"),
    path("stats_by_zip/", views.MemberStatsByZipCodeView.as_view(), name="stats_by_zip"),
    path("stats_by_interest/", views.MemberStatsByInterestView.as_view(), name="stats_by_interest"),
    path("stats_by_skill/", views.MemberStatsBySkillView.as_view(), name="stats_by_skill"),
    path("stats_by_career_level/", views.MemberStatsByCareerLevelView.as_view(), name="stats_by_career_level"),
    path("interests_partial/<int:pk>", views.interests_partial, name="interests_partial"),
    path("skills_partial/<int:pk>", views.skills_partial, name="skills_partial"),
]
