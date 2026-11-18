from functools import wraps

from flask import abort, current_app, g, redirect, url_for


ROLE_PERMISSIONS = {
    'user': frozenset({
        'todo:create',
        'todo:list:own',
        'todo:read:own',
        'todo:update:own',
        'todo:delete:own',
    }),
    'admin': frozenset({
        'todo:create',
        'todo:list:any',
        'todo:read:any',
        'todo:update:any',
        'todo:delete:any',
        'admin:tasks',
    }),
}


def has_permission(user, permission):
    return permission in ROLE_PERMISSIONS.get(user.role, frozenset())


def permission_required(permission):
    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            if g.user is None:
                return redirect(url_for('auth.login'))
            if current_app.config['AUTHZ_MODE'] == 'baseline':
                return view(*args, **kwargs)

            required = permission
            if permission == 'todo:list':
                scope = 'any' if g.user.role == 'admin' else 'own'
                required = f'todo:list:{scope}'
            if not has_permission(g.user, required):
                abort(403)
            return view(*args, **kwargs)
        return wrapped_view
    return decorator


def authorize_todo(todo, action):
    if current_app.config['AUTHZ_MODE'] == 'baseline':
        return

    scope = 'any' if g.user.role == 'admin' else 'own'
    if not has_permission(g.user, f'todo:{action}:{scope}'):
        abort(403)
    if scope == 'own' and todo.created_by != g.user.id:
        abort(403)
