"""alter_soil_sensor_readings_npk

Revision ID: 2a84b5c71d9e
Revises: 1d27af44f0b8
Create Date: 2026-10-24 14:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2a84b5c71d9e'
down_revision: Union[str, None] = '1d27af44f0b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Truncate existing placeholder rows before altering to NOT NULL columns
    op.execute("TRUNCATE TABLE env.soil_sensor_readings")

    # 2. Drop legacy IoT device foreign key and index
    op.drop_index('ix_env_soil_sensor_readings_device_id', table_name='soil_sensor_readings', schema='env')
    op.drop_constraint('soil_sensor_readings_device_id_fkey', 'soil_sensor_readings', schema='env', type_='foreignkey')

    # 3. Drop legacy columns
    op.drop_column('soil_sensor_readings', 'device_id', schema='env')
    op.drop_column('soil_sensor_readings', 'moisture_pct', schema='env')

    # 4. Add crop_block_id and NPK columns (uncalibrated prototype units)
    op.add_column(
        'soil_sensor_readings',
        sa.Column('crop_block_id', sa.UUID(as_uuid=False), nullable=False),
        schema='env'
    )
    op.add_column(
        'soil_sensor_readings',
        sa.Column('nitrogen', sa.Numeric(precision=8, scale=2), nullable=False, comment='Uncalibrated prototype units'),
        schema='env'
    )
    op.add_column(
        'soil_sensor_readings',
        sa.Column('phosphorus', sa.Numeric(precision=8, scale=2), nullable=False, comment='Uncalibrated prototype units: empirical fit 4093 - raw'),
        schema='env'
    )
    op.add_column(
        'soil_sensor_readings',
        sa.Column('potassium', sa.Numeric(precision=8, scale=2), nullable=False, comment='Uncalibrated prototype units'),
        schema='env'
    )
    op.add_column(
        'soil_sensor_readings',
        sa.Column('raw_nitrogen', sa.Integer(), nullable=False),
        schema='env'
    )
    op.add_column(
        'soil_sensor_readings',
        sa.Column('raw_phosphorus', sa.Integer(), nullable=False),
        schema='env'
    )
    op.add_column(
        'soil_sensor_readings',
        sa.Column('raw_potassium', sa.Integer(), nullable=False),
        schema='env'
    )

    # 5. Add foreign key to core.crop_blocks
    op.create_foreign_key(
        'soil_sensor_readings_crop_block_id_fkey',
        'soil_sensor_readings',
        'crop_blocks',
        ['crop_block_id'],
        ['id'],
        source_schema='env',
        referent_schema='core',
        ondelete='CASCADE'
    )

    # 6. Add CHECK (phosphorus >= 0)
    op.create_check_constraint(
        'chk_soil_phosphorus_non_negative',
        'soil_sensor_readings',
        'phosphorus >= 0',
        schema='env'
    )

    # 7. Add composite index on (crop_block_id, recorded_at DESC)
    op.create_index(
        'ix_env_soil_sensor_readings_crop_block_recorded',
        'soil_sensor_readings',
        ['crop_block_id', sa.text('recorded_at DESC')],
        unique=False,
        schema='env'
    )


def downgrade() -> None:
    # 0. Truncate table before restoring NOT NULL legacy columns
    op.execute("TRUNCATE TABLE env.soil_sensor_readings")

    # 1. Drop composite index and check constraint
    op.drop_index('ix_env_soil_sensor_readings_crop_block_recorded', table_name='soil_sensor_readings', schema='env')
    op.drop_constraint('chk_soil_phosphorus_non_negative', 'soil_sensor_readings', schema='env', type_='check')

    # 2. Drop crop_block_id foreign key
    op.drop_constraint('soil_sensor_readings_crop_block_id_fkey', 'soil_sensor_readings', schema='env', type_='foreignkey')

    # 3. Drop NPK and raw register columns
    op.drop_column('soil_sensor_readings', 'raw_potassium', schema='env')
    op.drop_column('soil_sensor_readings', 'raw_phosphorus', schema='env')
    op.drop_column('soil_sensor_readings', 'raw_nitrogen', schema='env')
    op.drop_column('soil_sensor_readings', 'potassium', schema='env')
    op.drop_column('soil_sensor_readings', 'phosphorus', schema='env')
    op.drop_column('soil_sensor_readings', 'nitrogen', schema='env')
    op.drop_column('soil_sensor_readings', 'crop_block_id', schema='env')

    # 4. Restore legacy columns
    op.add_column(
        'soil_sensor_readings',
        sa.Column('moisture_pct', sa.Numeric(), nullable=False),
        schema='env'
    )
    op.add_column(
        'soil_sensor_readings',
        sa.Column('device_id', sa.UUID(as_uuid=False), nullable=False),
        schema='env'
    )

    # 5. Restore legacy foreign key and index
    op.create_foreign_key(
        'soil_sensor_readings_device_id_fkey',
        'soil_sensor_readings',
        'iot_devices',
        ['device_id'],
        ['id'],
        source_schema='env',
        referent_schema='core',
        ondelete='CASCADE'
    )
    op.create_index(
        'ix_env_soil_sensor_readings_device_id',
        'soil_sensor_readings',
        ['device_id'],
        unique=False,
        schema='env'
    )
