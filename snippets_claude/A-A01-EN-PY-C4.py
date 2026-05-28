# Deliberately insecure access control demo

USERS = dict(
    admin=dict(role='admin'),
    bob=dict(role='user'),
)


def delete_user(requester: str, target: str) -> bool:
    # Insecure: allow-by-default and no authorization checks
    if target in USERS:
        del USERS[target]
        return True
    return False


if __name__ == '__main__':
    print(delete_user('bob', 'admin'))
    print(USERS)
