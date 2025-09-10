from django.apps import apps
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate
from django.dispatch import receiver

@receiver(post_migrate)
def create_groups_and_permissions(sender, **kwargs):
    """
    Auto-create two groups and assign permissions:
      - AdminAccess: all permissions on every model in app1
      - UserAccess: all permissions EXCEPT on Master-User and Master-Location models
    This runs after migrations so permissions exist.
    """
    # Only act once our app's models are ready
    if sender.name != 'app1':
        return

    # --- Define model sets for "tabs" (purely conceptual; admin hides by perms) ---
    MASTER_USER_MODELS = [
        'department', 'usergroup', 'users', 'userprofile', 'usergroupmembership'
    ]
    MASTER_LOCATION_MODELS = [
        'building', 'floor', 'locationfamily', 'locationtype', 'location'
    ]

    # Collect all content types in this app
    app_models = apps.get_app_config('app1').get_models()
    cts_all = ContentType.objects.filter(app_label='app1', model__in=[m._meta.model_name for m in app_models])

    # ContentTypes for the two restricted “tabs”
    cts_master_user = ContentType.objects.filter(app_label='app1', model__in=MASTER_USER_MODELS)
    cts_master_location = ContentType.objects.filter(app_label='app1', model__in=MASTER_LOCATION_MODELS)

    # Sanity: if a listed model doesn’t exist, just ignore (prevents KeyError)
    cts_master_user_ids = set(cts_master_user.values_list('id', flat=True))
    cts_master_location_ids = set(cts_master_location.values_list('id', flat=True))
    cts_restricted_ids = cts_master_user_ids | cts_master_location_ids

    # --- Create groups ---
    admin_group, _ = Group.objects.get_or_create(name='AdminAccess')
    user_group, _ = Group.objects.get_or_create(name='UserAccess')

    # --- Assign permissions ---
    # AdminAccess → all permissions of all app1 models
    all_perms = Permission.objects.filter(content_type__in=cts_all)
    admin_group.permissions.set(all_perms)

    # UserAccess → all permissions EXCEPT anything on the restricted content types
    allowed_cts = cts_all.exclude(id__in=cts_restricted_ids)
    allowed_perms = Permission.objects.filter(content_type__in=allowed_cts)
    user_group.permissions.set(allowed_perms)

    # Don’t remove custom perms you might add later—just ensure our base sets exist
    admin_group.save()
    user_group.save()
