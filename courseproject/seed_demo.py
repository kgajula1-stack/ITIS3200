import getpass

from werkzeug.security import generate_password_hash

from todor import create_app, db
from todor.models import Todo, User


DEMO_DATABASE_URL = 'sqlite:///courseproject_demo.db'


def derive_seed(suffixes):
    if len(suffixes) != 4 or any(
        len(value) != 2 or not value.isdigit() for value in suffixes
    ):
        raise ValueError('Enter exactly four two-digit suffixes.')
    return sum(int(value) for value in suffixes) % 11


def _ensure_user(user_id, username, email, password_hash, role):
    user = db.session.get(User, user_id)
    if user is not None and user.username != username:
        raise RuntimeError(
            f'Demo user ID {user_id} is already occupied; use a fresh demo database.'
        )

    named_user = User.query.filter_by(username=username).first()
    if named_user is not None and named_user.id != user_id:
        raise RuntimeError(
            f'Demo username {username} has a different ID; use a fresh demo database.'
        )

    if user is None:
        user = User(username, password_hash, email, role=role)
        user.id = user_id
        db.session.add(user)
    else:
        user.password_hash = password_hash
        user.role = role
    return user


def _ensure_task(task_id, owner_id, title, description):
    task = db.session.get(Todo, task_id)
    if task is not None and task.created_by != owner_id:
        raise RuntimeError(
            f'Demo task ID {task_id} is already occupied; use a fresh demo database.'
        )

    if task is None:
        task = Todo(owner_id, title, description)
        task.id = task_id
        db.session.add(task)
    else:
        task.title = title
        task.desc = description
        task.state = Todo.STATE_NOT_STARTED
    return task


def seed_demo(suffixes):
    seed = derive_seed(suffixes)
    app = create_app({'DATABASE_URL': DEMO_DATABASE_URL})
    password = f'CourseDemo-{seed:02d}!'
    password_hash = generate_password_hash(password)

    user_a_id = 100 + seed
    user_b_id = 200 + seed
    admin_id = 300 + seed
    task_a_id = 1000 + 2 * seed
    task_b_id = task_a_id + 1

    with app.app_context():
        user_a = _ensure_user(
            user_a_id, f'demo_a_{seed:02d}', f'demo-a-{seed:02d}@example.test',
            password_hash, 'user',
        )
        user_b = _ensure_user(
            user_b_id, f'demo_b_{seed:02d}', f'demo-b-{seed:02d}@example.test',
            password_hash, 'user',
        )
        admin = _ensure_user(
            admin_id, f'demo_admin_{seed:02d}', f'demo-admin-{seed:02d}@example.test',
            password_hash, 'admin',
        )
        task_a = _ensure_task(
            task_a_id, user_a.id, f'User A private task {seed}',
            'Synthetic local-demo task owned by User A.',
        )
        task_b = _ensure_task(
            task_b_id, user_b.id, f'User B private task {seed}',
            'Synthetic local-demo task owned by User B.',
        )
        db.session.commit()
        demo_accounts = (
            (user_a.username, task_a.id),
            (user_b.username, task_b.id),
            (admin.username, None),
        )

    print(f'Derived seed: {seed}')
    print(f'User A: {demo_accounts[0][0]} / {password} (task ID {demo_accounts[0][1]})')
    print(f'User B: {demo_accounts[1][0]} / {password} (task ID {demo_accounts[1][1]})')
    print(f'Admin: {demo_accounts[2][0]} / {password}')
    return seed


def main():
    print('Enter the four members’ last two student-ID digits; inputs are hidden.')
    suffixes = [
        getpass.getpass(f'Member {member} suffix: ')
        for member in range(1, 5)
    ]
    try:
        seed_demo(suffixes)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == '__main__':
    main()
