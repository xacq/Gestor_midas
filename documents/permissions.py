def is_gerencia(user) -> bool:
    return user.is_authenticated and user.groups.filter(name="GERENCIA").exists()

def can_view_published(user) -> bool:
    return user.is_authenticated  # o restringir a gerencia+staff si quieres

def can_manage_documents(user) -> bool:
    return user.is_authenticated and user.is_staff
