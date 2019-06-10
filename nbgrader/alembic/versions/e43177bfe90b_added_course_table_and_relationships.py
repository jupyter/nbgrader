"""Added course table and relationships

Revision ID: e43177bfe90b
Revises: 282d30a0218e
Create Date: 2019-05-30 09:39:31.881296

"""
from alembic import op
import sqlalchemy as sa
from nbgrader.api import Course

# revision identifiers, used by Alembic.
revision = 'e43177bfe90b'
down_revision = '282d30a0218e'
branch_labels = None
depends_on = None


def _get_or_create_table(*args):
    try:
        table = op.create_table(*args)
    except sa.exc.OperationalError:
        table = sa.sql.table(*args)
    return table


def upgrade():
    """
    This migrations adds a course column to the assignment table
    and a matching foreign key into the course table
    """

    new_course_table = _get_or_create_table(
        'course',
        sa.Column("id", sa.String(128), unique=True,
                  primary_key=True, nullable=False),
    )

    # If the course table is empty, create a default course
    connection = op.get_bind()
    res = connection.execute("select id from course")
    results = res.fetchall()
    default_course = "default_course"

    if len(results) == 0:
        connection.execute(
            "INSERT INTO course (id) VALUES ('{}')".format(default_course))

    with op.batch_alter_table("assignment") as batch_op:

        batch_op.add_column(sa.Column(
            'course_id', sa.VARCHAR(128), nullable=False, default=default_course))
        batch_op.create_foreign_key(
            'fk_course_assignment', 'course', ['course_id'], ['id'])


def downgrade():
    with op.batch_alter_table("assignment") as batch_op:

        batch_op.drop_constraint('fk_course_assignment', type_='foreignkey')
        batch_op.drop_column('assignment', 'course_id')

    op.drop_table('course')
