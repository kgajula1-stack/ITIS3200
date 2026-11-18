import logging

from flask import Blueprint, current_app, render_template, request, redirect, url_for, g, flash
from todor.auth import login_required
from todor.authz import authorize_todo, permission_required
from .models import Todo
from todor import db

bp = Blueprint('todo', __name__, url_prefix='/todo')
logger = logging.getLogger(__name__)


@bp.route('/list')
@login_required
@permission_required('todo:list')
def index():
    """Show the current user's tasks, grouped by state in the template."""
    if current_app.config['AUTHZ_MODE'] == 'baseline' or g.user.role == 'admin':
        todos = Todo.query.order_by(Todo.id).all()
    else:
        todos = Todo.query.filter_by(created_by=g.user.id).order_by(Todo.id).all()
    return render_template('todo/index.html', todos=todos)


@bp.route('/create', methods=('POST',))
@login_required
@permission_required('todo:create')
def create():
    """Create a new task owned by the current user."""
    try:
        title = request.form['title']
        desc = request.form['desc']

        todo = Todo(g.user.id, title, desc)

        db.session.add(todo)
        db.session.commit()

        return redirect(url_for('todo.index'))
    except Exception:
        logger.exception("Failed to create todo")
        flash("Internal error, try again")
        return redirect(url_for('todo.index'))


def get_todo(id, action):
    """Fetch a task by ID and apply the requested server-side permission."""
    todo = Todo.query.get_or_404(id)
    authorize_todo(todo, action)
    return todo


@bp.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    """Update a task's title, description and/or state."""
    action = 'read' if request.method == 'GET' else 'update'
    todo = get_todo(id, action)
    if request.method == 'GET':
        return render_template('todo/update.html', todo=todo)
    try:
        todo.title = request.form['title']
        todo.desc = request.form['desc']

        state_value = request.form.get('state')
        if state_value in Todo.STATES:
            todo.state = state_value

        db.session.commit()
        return redirect(url_for('todo.index'))
    except Exception:
        logger.exception("Failed to update todo %s", id)
        flash("Internal error, try again")
        return redirect(url_for('todo.index'))


@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    """Delete a task owned by the current user."""
    todo = get_todo(id, 'delete')
    try:
        db.session.delete(todo)
        db.session.commit()

        return redirect(url_for('todo.index'))
    except Exception:
        logger.exception("Failed to delete todo %s", id)
        flash("Internal error, try again")
        return redirect(url_for('todo.index'))


@bp.route('/admin/tasks')
@login_required
@permission_required('admin:tasks')
def admin_tasks():
    todos = Todo.query.order_by(Todo.id).all()
    return render_template('admin/tasks.html', todos=todos)
