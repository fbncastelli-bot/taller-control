CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    usuario VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nombre_taller VARCHAR(100) NOT NULL,
    telefono_taller VARCHAR(30),
    rol VARCHAR(20) DEFAULT 'admin'
);

CREATE TABLE IF NOT EXISTS ordenes (
    id SERIAL PRIMARY KEY,
    usuario_id INT NOT NULL,
    cliente VARCHAR(100) NOT NULL,
    telefono VARCHAR(30),
    equipo VARCHAR(100) NOT NULL,
    falla TEXT,
    solucion TEXT,
    presupuesto NUMERIC(10, 2) DEFAULT 0,
    estado VARCHAR(30) DEFAULT 'Ingresado',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS repuestos (
    id SERIAL PRIMARY KEY,
    usuario_id INT NOT NULL,
    categoria VARCHAR(50),
    nombre VARCHAR(100) NOT NULL,
    ubicacion VARCHAR(50),
    cantidad INT DEFAULT 0,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ventas (
    id SERIAL PRIMARY KEY,
    usuario_id INT NOT NULL,
    producto VARCHAR(100) NOT NULL,
    precio NUMERIC(10, 2) DEFAULT 0,
    estado VARCHAR(30) DEFAULT 'En Venta',
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS caja (
    id SERIAL PRIMARY KEY,
    usuario_id INT NOT NULL,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tipo VARCHAR(20) NOT NULL,
    concepto VARCHAR(150) NOT NULL,
    monto NUMERIC(10, 2) DEFAULT 0,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS firmwares (
    id SERIAL PRIMARY KEY,
    chasis VARCHAR(100) NOT NULL,
    modelo VARCHAR(100),
    memoria VARCHAR(50),
    url_nube TEXT NOT NULL
);
