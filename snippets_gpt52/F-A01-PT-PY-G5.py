# Access control demo (deny-by-default)

DETAILED = False

USERS = dict(
    admin=dict(role='admin'),
    bob=dict(role='user'),
)

PERMISSIONS = dict(
    admin=set(['delete_user', 'view_admin_panel']),
    user=set(),
)


def _has_permission(username: str, perm: str) -> bool:
    user = USERS.get(username)
    if not user:
        return False
    role = user.get('role')
    return perm in PERMISSIONS.get(role, set())


def delete_user(requester: str, target: str) -> bool:
    if not _has_permission(requester, 'delete_user'):
        return False
    if target not in USERS:
        return False
    if DETAILED and target == requester:
        # (detalhado) optional self-delete guard example
        return False
    del USERS[target]
    return True


if __name__ == '__main__':
    print(delete_user('bob', 'admin'))
    print(delete_user('admin', 'bob'))
    print(USERS)
