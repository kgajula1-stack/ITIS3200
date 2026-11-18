import unittest

from werkzeug.security import generate_password_hash

from todor import create_app, db
from todor.models import Todo, User


class AuthorizationTestSupport:
    def setUp(self):
        self.app = create_app({
            'AUTHZ_MODE': self.authz_mode,
            'DATABASE_URL': 'sqlite:///:memory:',
            'TESTING': True,
            'SECRET_KEY': 'test-only-key',
        })
        self.client = self.app.test_client()
        with self.app.app_context():
            self.user_a = User(
                'user_a', generate_password_hash('password'),
                'user-a@example.test',
            )
            self.user_b = User(
                'user_b', generate_password_hash('password'),
                'user-b@example.test',
            )
            self.admin = User(
                'admin', generate_password_hash('password'),
                'admin@example.test', role='admin',
            )
            db.session.add_all((self.user_a, self.user_b, self.admin))
            db.session.flush()
            self.task_a = Todo(self.user_a.id, 'A private title', 'A description')
            self.task_b = Todo(self.user_b.id, 'B private title', 'B description')
            db.session.add_all((self.task_a, self.task_b))
            db.session.commit()
            self.user_a_id = self.user_a.id
            self.task_a_id = self.task_a.id
            self.task_b_id = self.task_b.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

    def login(self, username):
        response = self.client.post(
            '/auth/login',
            data={'username': username, 'password': 'password'},
        )
        self.assertEqual(response.status_code, 302)

    def get_task(self, task_id):
        with self.app.app_context():
            return db.session.get(Todo, task_id)


class BaselineModeTests(AuthorizationTestSupport, unittest.TestCase):
    authz_mode = 'baseline'

    def test_authenticated_user_can_read_and_change_another_users_task(self):
        self.login('user_a')

        read_response = self.client.get(f'/todo/update/{self.task_b_id}')
        self.assertEqual(read_response.status_code, 200)
        self.assertIn(b'B private title', read_response.data)

        write_response = self.client.post(
            f'/todo/update/{self.task_b_id}',
            data={
                'title': 'Changed by user A',
                'desc': 'Unauthorized update',
                'state': 'completed',
            },
        )
        self.assertEqual(write_response.status_code, 302)
        self.assertEqual(self.get_task(self.task_b_id).title, 'Changed by user A')

        delete_response = self.client.post(f'/todo/delete/{self.task_b_id}')
        self.assertEqual(delete_response.status_code, 302)
        self.assertIsNone(self.get_task(self.task_b_id))

    def test_authenticated_standard_user_can_access_admin_view_in_baseline(self):
        self.login('user_a')
        response = self.client.get('/todo/admin/tasks')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'A private title', response.data)
        self.assertIn(b'B private title', response.data)

    def test_baseline_is_unreachable_from_non_loopback_address(self):
        response = self.client.get(
            '/todo/list',
            environ_overrides={'REMOTE_ADDR': '203.0.113.12'},
        )
        self.assertEqual(response.status_code, 404)


class HardenedModeTests(AuthorizationTestSupport, unittest.TestCase):
    authz_mode = 'rbac'

    def test_user_cannot_read_update_or_delete_another_users_task(self):
        self.login('user_a')

        responses = (
            self.client.get(f'/todo/update/{self.task_b_id}'),
            self.client.post(
                f'/todo/update/{self.task_b_id}',
                data={'title': 'Unauthorized', 'desc': 'No', 'state': 'completed'},
            ),
            self.client.post(f'/todo/delete/{self.task_b_id}'),
        )
        for response in responses:
            self.assertEqual(response.status_code, 403)

        self.assertEqual(self.get_task(self.task_b_id).title, 'B private title')

    def test_user_sees_only_own_task_and_can_manage_it(self):
        self.login('user_a')

        list_response = self.client.get('/todo/list')
        self.assertEqual(list_response.status_code, 200)
        self.assertIn(b'A private title', list_response.data)
        self.assertNotIn(b'B private title', list_response.data)

        read_response = self.client.get(f'/todo/update/{self.task_a_id}')
        self.assertEqual(read_response.status_code, 200)
        update_response = self.client.post(
            f'/todo/update/{self.task_a_id}',
            data={'title': 'A updated title', 'desc': 'Allowed', 'state': 'completed'},
        )
        self.assertEqual(update_response.status_code, 302)
        self.assertEqual(self.get_task(self.task_a_id).title, 'A updated title')

        delete_response = self.client.post(f'/todo/delete/{self.task_a_id}')
        self.assertEqual(delete_response.status_code, 302)
        self.assertIsNone(self.get_task(self.task_a_id))

    def test_admin_can_view_all_tasks_and_manage_another_users_task(self):
        self.login('admin')

        admin_response = self.client.get('/todo/admin/tasks')
        self.assertEqual(admin_response.status_code, 200)
        self.assertIn(b'A private title', admin_response.data)
        self.assertIn(b'B private title', admin_response.data)

        update_response = self.client.post(
            f'/todo/update/{self.task_b_id}',
            data={'title': 'Admin update', 'desc': 'Authorized', 'state': 'completed'},
        )
        self.assertEqual(update_response.status_code, 302)
        self.assertEqual(self.get_task(self.task_b_id).title, 'Admin update')

    def test_standard_user_is_denied_admin_route_and_anonymous_user_is_redirected(self):
        self.login('user_a')
        self.assertEqual(self.client.get('/todo/admin/tasks').status_code, 403)

        self.client.get('/auth/logout')
        response = self.client.get('/todo/list')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login', response.location)

    def test_unknown_role_is_denied_by_default(self):
        with self.app.app_context():
            user = db.session.get(User, self.user_a_id)
            user.role = 'unrecognized'
            db.session.commit()

        self.login('user_a')
        self.assertEqual(self.client.get('/todo/list').status_code, 403)
        self.assertEqual(self.client.get('/todo/admin/tasks').status_code, 403)

    def test_registration_cannot_assign_admin_role(self):
        response = self.client.post(
            '/auth/register',
            data={
                'username': 'new_user',
                'password': 'password',
                'email': 'new-user@example.test',
                'role': 'admin',
            },
        )
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            user = User.query.filter_by(username='new_user').one()
            self.assertEqual(user.role, 'user')


if __name__ == '__main__':
    unittest.main()
