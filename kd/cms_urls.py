from django.urls import path

from . import cms

app_name = "cms"
urlpatterns = [
    path("", cms.dashboard, name="dashboard"),
    path("login/", cms.login_view, name="login"),
    path("logout/", cms.logout_view, name="logout"),
    path("posts/", cms.post_list, name="posts"),
    path("posts/new/", cms.post_edit, name="post_new"),
    path("posts/<int:pk>/", cms.post_edit, name="post_edit"),
    path("posts/<int:pk>/delete/", cms.post_delete, name="post_delete"),
    path("preview/", cms.preview, name="preview"),
    path("upload/", cms.upload, name="upload"),
    path("messages/", cms.inbox, name="messages"),
    path("messages/<int:pk>/", cms.message_action, name="message_action"),
    path("settings/", cms.site_settings, name="settings"),
    path("profile/", cms.profile, name="profile"),
    path("users/", cms.users, name="users"),
    path("users/<int:pk>/toggle/", cms.user_toggle, name="user_toggle"),
]
