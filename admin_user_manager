# admin_api.py
class UserAdminView:
    @router.post("/users")
    def create_user(self, email: str, role: str):
        # Validate role against ROLE_CHOICES
        user = User.objects.create(email=email, role=role)
        return user

    @router.patch("/users/{user_id}/permissions")
    def update_permissions(self, user_id: str, permissions: List[str]):
        user = get_user(user_id)
        user.set_permissions(permissions)
        return {"status": "updated"}
