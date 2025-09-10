def user_groups(request):
    if request.user.is_authenticated:
        return {
            "is_admin_access": (
                request.user.is_superuser or 
                request.user.groups.filter(name="AdminAccess").exists()
            )
        }
    return {"is_admin_access": False}
