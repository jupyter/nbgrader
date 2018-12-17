"""added task cells

Revision ID: 167914646830
Revises: 724cde206c17
Create Date: 2018-06-23 07:46:30.221922

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '167914646830'
down_revision = '724cde206c17'
branch_labels = None
depends_on = None


def upgrade():
    """
    To upgrade we need to split the grade_cell and solution_cell database
    entries into a part in base_cell and a part in either grade_cell or
    solution_cell. Because the names are the same for the new and old
    grade_cell and solution_cell tables we create temporary tables
    'grade_cells' and 'solution_cells' and once the transfer has occured
    we drop the old tables and rename the temporary tables to the
    original names.
    """

    new_grade_table = sa.sql.table(
        'grade_cells',
        sa.Column('id', sa.VARCHAR(32), nullable=False),
        sa.Column('max_score', sa.Float(), nullable=False),
        sa.Column('cell_type', sa.VARCHAR(8), nullable=False),
    )

    new_solution_table = sa.sql.table(
        'solutions_cells',
        sa.Column('id', sa.VARCHAR(32), nullable=False),
    )

    old_grade_table = sa.Table(
        'grade_cell',
        sa.MetaData(),
        sa.Column('id', sa.VARCHAR(32), nullable=False),
        sa.Column('name', sa.VARCHAR(128), nullable=False),
        sa.Column('max_score', sa.Float(), nullable=False),
        sa.Column('cell_type', sa.VARCHAR(8), nullable=False),
        sa.Column('notebook_id', sa.VARCHAR(32)),
    )

    old_solution_table = sa.Table(
        'solution_cell',
        sa.MetaData(),
        sa.Column('id', sa.VARCHAR(32), nullable=False),
        sa.Column('name', sa.VARCHAR(128), nullable=False),
        sa.Column('max_score', sa.Float(), nullable=False),
        sa.Column('cell_type', sa.VARCHAR(8), nullable=False),
        sa.Column('notebook_id', sa.VARCHAR(32)),
    )

    base_cell_table = sa.sql.table(
        'base_cell',
        sa.Column('id', sa.VARCHAR(32), nullable=False),
        sa.Column('name', sa.VARCHAR(128), nullable=False),
        sa.Column('notebook_id', sa.VARCHAR(32)),
        sa.Column('type', sa.VARCHAR(50))
    )

    connection = op.get_bind()
    results = connection.execute(sa.select([
            old_grade_table.c.name,
            old_grade_table.c.id,
            old_grade_table.c.cell_type,
            old_grade_table.c.notebook_id,
            old_grade_table.c.max_score
            ])).fetchall()

    # copy info to the base_cell table
    cells = [
        {
            'name': name,
            'id': cellid,
            'type': 'GradeCell',
            'notebook_id': notebook_id,
        } for name, cellid, _, notebook_id, _ in results
            ]

    op.bulk_insert(base_cell_table, cells)

    # copy the grade_cell specific info to the grade_cells temporary database
    cells = [
        {
         'id': cellid,
         'type': celltype,
         'max_score': max_score,
        } for _, cellid, celltype, _, max_score in results]

    op.bulk_insert(new_grade_table, cells)

    # now transfer the solution cells...
    results = connection.execute(sa.select([
            old_solution_table.c.name,
            old_solution_table.c.id,
            old_solution_table.c.notebook_id,
            ])).fetchall()

    # copy info to the base_cell table
    cells = [
        {
            'name': name,
            'id': cellid,
            'type': 'SolutionCell',
            'notebook_id': notebook_id,
        } for name, cellid, notebook_id in results]

    op.bulk_insert(base_cell_table, cells)

    # copy the solution_cell specific info to the grade_cells
    # temporary database
    cells = [
        {
         'id': cellid,
        } for _, cellid, _ in results]

    op.bulk_insert(new_solution_table, cells)

    op.drop_table(u'grade_cell')
    op.drop_table(u'solution_cell')
    op.rename_table('solution_cells', 'solution_cell')
    op.rename_table('grade_cells', 'grade_cell')


def downgrade():
    pass
