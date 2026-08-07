"""remove_unique_codigo_producto

Revision ID: 37ef7b9aecb3
Revises: b0147e10ad04
Create Date: 2026-08-03 13:59:29.602391

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '37ef7b9aecb3'
down_revision = 'b0147e10ad04'
branch_labels = None
depends_on = None


def upgrade():
    # En SQLite, recreamos la tabla sin la restricción UNIQUE en codigo_producto
    op.execute('''
        CREATE TABLE _alembic_tmp_productos (
            id INTEGER NOT NULL PRIMARY KEY,
            codigo_producto VARCHAR(50) NOT NULL,
            nombre VARCHAR(150) NOT NULL,
            marca VARCHAR(100) NOT NULL,
            estado VARCHAR(20) NOT NULL,
            categoria_id INTEGER NOT NULL,
            proveedor_id INTEGER NOT NULL,
            precio_compra FLOAT NOT NULL,
            precio_venta FLOAT NOT NULL,
            stock INTEGER NOT NULL,
            cantidad_comprada INTEGER NOT NULL,
            fecha_compra DATE NOT NULL,
            created_at DATETIME,
            updated_at DATETIME,
            FOREIGN KEY(categoria_id) REFERENCES categorias (id),
            FOREIGN KEY(proveedor_id) REFERENCES proveedores (id)
        );
    ''')
    op.execute('INSERT INTO _alembic_tmp_productos SELECT * FROM productos;')
    op.execute('DROP TABLE productos;')
    op.execute('ALTER TABLE _alembic_tmp_productos RENAME TO productos;')


def downgrade():
    pass
