from app import app, db
import sqlalchemy as sa
import sqlalchemy.orm as so
from app.models import Role

@app.shell_context_processor
def make_shell_context():
    return {'sa':sa, 'so':so, 'db':db}


@app.cli.command('seed_roles')
def seed_roles():
    roles = ['Admin', 'Editor', 'Author', 'Viewer']
    for role_name in roles:
        role = Role.query.filter_by(name=role_name).first()
        if role is None:
            role = Role(name=role_name, description=f'{role_name} role')
            db.session.add(role)
    db.session.commit()
    print('Roles added successfully.')